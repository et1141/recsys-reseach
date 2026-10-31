"""Fetch complete upstream skill folders and pin commits; package local imports."""
import hashlib
import json
import shutil
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def command(*args: str) -> str:
    return subprocess.check_output(args, text=True).strip()


def main() -> None:
    spec = json.loads((ROOT / "setup/sources.json").read_text())
    lockfile = ROOT / "setup/sources.lock.json"
    locks = json.loads(lockfile.read_text()) if lockfile.exists() else {}
    vendor = ROOT / "vendor"
    vendor.mkdir(exist_ok=True)
    for name, url in spec["repositories"].items():
        dest = vendor / name
        if not dest.exists():
            command("git", "clone", "--depth", "1", url, str(dest))
        if name in locks:
            revision = locks[name]["commit"]
            command("git", "-C", str(dest), "fetch", "--depth", "1", "origin", revision)
            command("git", "-C", str(dest), "checkout", "--detach", revision)
        revision = command("git", "-C", str(dest), "rev-parse", "HEAD")
        if command("git", "-C", str(dest), "status", "--porcelain"):
            raise RuntimeError(f"Modified upstream checkout: {dest}")
        locks[name] = {"url": url, "commit": revision}
        lockfile.write_text(json.dumps(locks, indent=2) + "\n", encoding="utf-8")
    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    hashes = {}
    for name, (repo, rel) in spec["skills"].items():
        folder = vendor / repo / rel
        if not (folder / "SKILL.md").is_file():
            raise FileNotFoundError(folder / "SKILL.md")
        with zipfile.ZipFile(dist / f"{name}.zip", "w", zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(folder.rglob("*")):
                if path.is_file():
                    arcname = f"{name}/{path.relative_to(folder).as_posix()}"
                    archive.write(path, arcname)
                    hashes[arcname] = hashlib.sha256(path.read_bytes()).hexdigest()
            for license_file in (vendor / repo).glob("LICENSE*"):
                if license_file.is_file():
                    archive.write(license_file, f"{name}/UPSTREAM-{license_file.name}")
    for name, (repo, rel) in spec["identities"].items():
        original = vendor / repo / rel
        hashes[f"identity/{name}"] = hashlib.sha256(original.read_bytes()).hexdigest()
        # Preserve the source identity and explicitly layer the user's project contract.
        combined = original.read_text(encoding="utf-8")
        combined += "\n\n# Project-specific instructions (take precedence)\n"
        combined += (ROOT / "agents" / f"{name}.md").read_text(encoding="utf-8")
        combined += "\n" + (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        (dist / f"{name}.md").write_text(combined, encoding="utf-8")
    for folder in (ROOT / "skills").iterdir():
        if folder.is_dir():
            shutil.make_archive(str(dist / folder.name), "zip", folder.parent, folder.name)
    (ROOT / "setup/source-files.sha256.json").write_text(
        json.dumps(hashes, indent=2) + "\n", encoding="utf-8"
    )
    print("Prepared pinned imports. Commit setup/sources.lock.json and source-files.sha256.json.")


if __name__ == "__main__":
    main()
