"""Framework-neutral evidence helpers. No ML dependencies required."""
import hashlib
import importlib.metadata
import json
import math
import platform
import subprocess
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, content: Any) -> None:
    path.write_text(json.dumps(content, indent=2, default=str, allow_nan=False) + "\n",
                    encoding="utf-8")


def require_reproducible_checkout(root: Path) -> str:
    def git(*args: str) -> str:
        return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()
    if not (root / "uv.lock").is_file():
        raise RuntimeError("Missing uv.lock: resolve dependencies, validate, and commit the lock first")
    git("ls-files", "--error-unmatch", "uv.lock")
    if git("status", "--porcelain"):
        raise RuntimeError("Commit experiment code/config before running; checkout is dirty")
    return git("rev-parse", "HEAD")


def environment() -> dict:
    return {
        "python": platform.python_version(), "platform": platform.platform(),
        "processor": platform.processor(),
        "packages": {d.metadata["Name"]: d.version for d in importlib.metadata.distributions()},
    }


def validate_ranking_metrics(metrics: dict) -> None:
    if not metrics:
        raise ValueError("No evaluation metrics")
    for name, value in metrics.items():
        if not math.isfinite(float(value)) or not 0 <= float(value) <= 1:
            raise ValueError(f"Invalid bounded ranking metric {name}: {value}")


def validate_splits(splits: dict[str, list[tuple[int, int]]]) -> None:
    seen: set[tuple[int, int]] = set()
    for name, pairs in splits.items():
        current = set(pairs)
        if not current or len(current) != len(pairs):
            raise ValueError(f"Empty or duplicate interactions in {name}")
        if seen & current:
            raise ValueError(f"User-item leakage in {name}")
        seen.update(current)
