"""Tiny synthetic CPU plumbing test; never scientific reproduction evidence."""
import datetime
import logging
import os
import random
import sys
from pathlib import Path

from provenance import (
    environment, require_reproducible_checkout, sha256, validate_ranking_metrics,
    validate_splits, write_json,
)

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    os.chdir(ROOT)
    commit = require_reproducible_checkout(ROOT)
    import wandb
    from recbole.config import Config
    from recbole.data import create_dataset, data_preparation
    from recbole.utils import get_model, get_trainer, init_seed

    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output = ROOT / "artifacts" / f"EXP-000-{stamp}"
    output.mkdir(parents=True, exist_ok=False)
    dataset_file = ROOT / "data/toy/toy.inter"
    dataset_file.parent.mkdir(parents=True, exist_ok=True)
    rng = random.Random(42)
    rows = ["user_id:token\titem_id:token\ttimestamp:float"]
    for user in range(24):
        for index, item in enumerate(rng.sample(range(60), 20)):
            rows.append(f"u{user}\ti{item}\t{1000000 + user * 100 + index}")
    expected = "\n".join(rows) + "\n"
    if dataset_file.exists() and dataset_file.read_text(encoding="utf-8") != expected:
        raise RuntimeError("Existing toy dataset differs; refusing to overwrite")
    dataset_file.write_text(expected, encoding="utf-8")
    config = Config(config_file_list=[str(ROOT / "configs/recbole-smoke.yaml")],
                    config_dict={"checkpoint_dir": str(output), "log_wandb": False})
    init_seed(config["seed"], config["reproducibility"])
    logging.basicConfig(level=logging.INFO, handlers=[
        logging.FileHandler(output / "training.log", encoding="utf-8"),
        logging.StreamHandler(),
    ])
    write_json(output / "resolved-config.json", config.final_config_dict)
    manifest = {
        "experiment": "EXP-000", "purpose": "synthetic plumbing only", "commit": commit,
        "lock_sha256": sha256(ROOT / "uv.lock"), "command": [sys.executable, *sys.argv],
        "environment": environment(), "device": "CPU", "seed": config["seed"],
        "dataset": {"source": "scripts/smoke_recbole.py deterministic generator",
                    "sha256": sha256(dataset_file), "rows": len(rows) - 1},
        "review": "pending", "status": "started",
    }
    write_json(output / "manifest.json", manifest)
    run = wandb.init(project=os.environ.get("WANDB_PROJECT", "recsys-research"),
                     entity=os.environ.get("WANDB_ENTITY"), group="EXP-000",
                     name=output.name, mode=os.environ.get("WANDB_MODE", "offline"),
                     dir=str(output), config={"seed": 42, "model": "BPR", "commit": commit},
                     tags=["synthetic", "smoke", "review-pending"])
    try:
        dataset = create_dataset(config)
        train, valid, test = data_preparation(config, dataset)
        splits = {}
        for name, loader in (("train", train), ("valid", valid), ("test", test)):
            interactions = loader.dataset.inter_feat
            pairs = list(zip(interactions[config["USER_ID_FIELD"]].tolist(),
                             interactions[config["ITEM_ID_FIELD"]].tolist()))
            splits[name] = pairs
            write_json(output / f"split-{name}.json", pairs)
        validate_splits(splits)
        write_json(output / "token-map.json",
                   {field: values.tolist() for field, values in dataset.field2id_token.items()})
        model = get_model(config["model"])(config, train.dataset).to(config["device"])
        trainer = get_trainer(config["MODEL_TYPE"], config["model"])(config, model)
        _, validation = trainer.fit(train, valid, saved=True, show_progress=False)
        metrics = trainer.evaluate(test, load_best_model=True, show_progress=False)
        validate_ranking_metrics(validation)
        validate_ranking_metrics(metrics)
        results = {"validation": dict(validation), "test": dict(metrics)}
        write_json(output / "metrics.json", results)
        run.log({f"test/{key}": value for key, value in metrics.items()})
        run.log({f"validation/{key}": value for key, value in validation.items()})
        manifest.update(status="completed-unreviewed", wandb_id=run.id,
                        wandb_url=run.url, checks=["split-disjointness", "finite-bounded-metrics"])
        manifest["files"] = {p.name: sha256(p) for p in output.iterdir()
                             if p.is_file() and p.name != "manifest.json"}
        write_json(output / "manifest.json", manifest)
        artifact = wandb.Artifact(output.name, type="experiment-evidence")
        # Upload only generated evidence, never arbitrary raw data or environment secrets.
        for name in ["manifest.json", "metrics.json", "resolved-config.json", "training.log"]:
            artifact.add_file(str(output / name))
        run.log_artifact(artifact)
    except BaseException as error:
        manifest.update(status="failed", error=str(error))
        write_json(output / "manifest.json", manifest)
        run.finish(exit_code=1)
        raise
    else:
        run.finish()
    print(f"Evidence: {output}. Independent review remains pending.")


if __name__ == "__main__":
    main()
