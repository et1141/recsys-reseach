"""Provision an authenticated Multica workspace. Stops on conflicts; saves partial progress."""
import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def object_id(result: dict) -> str:
    for candidate in (result, result.get("skill", {})):
        if candidate.get("id"):
            return candidate["id"]
    raise ValueError(f"No created object ID in response: {result}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace-id", required=True)
    parser.add_argument("--runtime-id", required=True)
    parser.add_argument("--daemon-id", required=True)
    parser.add_argument("--cli", default="multica")
    args = parser.parse_args()
    statepath = ROOT / ".local" / f"multica-{args.workspace_id}.json"
    statepath.parent.mkdir(exist_ok=True)
    state = json.loads(statepath.read_text()) if statepath.exists() else {}
    spec = json.loads((ROOT / "setup/sources.json").read_text())
    if not (ROOT / "setup/sources.lock.json").exists():
        raise RuntimeError("Run setup/prepare_sources.py first")

    def cli(*words: str) -> dict:
        return json.loads(subprocess.check_output(
            [args.cli, "--workspace-id", args.workspace_id, *words, "--output", "json"],
            text=True, encoding="utf-8",
        ))

    def save() -> None:
        statepath.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")

    def create(key: str, *words: str) -> str:
        if key not in state:
            state[key] = object_id(cli(*words))
            save()
        return state[key]

    skills = {}
    for name in sorted({s for names in spec["attachments"].values() for s in names}):
        skills[name] = create(
            f"skill:{name}", "skill", "import", "--file", str(ROOT / "dist" / f"{name}.zip")
        )
    agents = {}
    for role, names in spec["attachments"].items():
        instructions = (ROOT / "dist" / f"{role}.md").read_text(encoding="utf-8")
        agents[role] = create(
            f"agent:{role}", "agent", "create", "--name", f"RecSys {role.title()}",
            "--instructions", instructions, "--runtime-id", args.runtime_id,
        )
        cli("agent", "skills", "set", agents[role], "--skill-ids",
            ",".join(skills[name] for name in names))
    squad = create("squad", "squad", "create", "--name", "RecSys Research",
                   "--leader", agents["coordinator"])
    cli("squad", "update", squad, "--instructions",
        (ROOT / "agents/squad.md").read_text(encoding="utf-8"))
    for role in ("researcher", "implementer", "reviewer"):
        key = f"member:{role}"
        if key not in state:
            cli("squad", "member", "add", squad, "--member-id", agents[role], "--type", "agent")
            state[key] = True
            save()
    project = create("project", "project", "create", "--title", "Recommendation Research",
                     "--description", (ROOT / "agents/project.md").read_text(encoding="utf-8"))
    if "resource" not in state:
        state["resource"] = cli(
            "project", "resource", "add", project, "--type", "local_directory",
            "--local-path", str(ROOT), "--daemon-id", args.daemon_id,
            "--execution-mode", "in_place",
        )
        save()
    print("Created project, squad, agents and attached skills. Verify them in Multica before assigning work.")


if __name__ == "__main__":
    main()
