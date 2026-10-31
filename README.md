# Recommendation research workspace

## Run Multica

Double-click **Start-Multica.cmd**, or run it from any terminal:

```powershell
C:\Users\adria\Files\recsys-research\Start-Multica.cmd
```

Prerequisites: Docker Desktop with Linux containers and Node.js (already available here).
The launcher starts Docker Desktop if needed, builds the existing Multica source using
Docker, starts PostgreSQL/API/web, waits for database migrations and web readiness, and
opens the app. Subsequent launches reuse configuration, Docker build caches and database
volumes. No host Go installation is needed to start the Multica service.

Use `Start-Multica.cmd --stop` to stop without deleting data, `--logs` to inspect logs,
or `--no-open` to skip opening the browser. First use still requires account/workspace
creation and the agent-runtime setup below; the launcher does not supply coding credentials.
The command file uses Node.js directly, so it does not execute a PowerShell script file.

**Prepared, but not running yet.** The existing Multica checkout is clean at
`e8ae72c9dfc1b4474b61a9087f51b33cbee6a048`. This session could not reach package
servers, find Docker/Go/uv, or access WSL. No Multica services or agents have been
created on a running server, no upstream skills downloaded, and no training run performed.
`uv.lock` must still be generated and validated; dependency compatibility is unverified.
The current PowerShell execution policy blocks the optional `.ps1` research/backup
utilities. The Multica startup command no longer depends on those utilities.

Open **notes/** as an Obsidian vault and start at [Home](notes/Home.md).
One experiment note holds the question, evidence links, review and decision.
The detailed evidence lives in artifacts and W&B. You control scope and final acceptance.

## What is prepared

- Coordinator, Researcher, Implementer, and independent Reviewer/Architect instructions.
- Squad routing: plan/data review -> smoke review -> results review -> your acceptance.
- Minimal experiment-note and research-verification skills.
- Import automation for the exact upstream identities and skills you selected, including
  supporting files and licenses. The first successful fetch records commit pins and hashes;
  later fetches reuse those pins. Local project instructions take precedence.
- Framework-neutral provenance helpers and optional RecBole, PyTorch, Lightning environments.
- A tiny synthetic RecBole/BPR smoke runner. It is not a paper reproduction or a benchmark.
- Local server build, research initialization and backup scripts.

The Designer is omitted until an interface task needs it. W&B replaces the proposed MLflow
setup. No Slack messages or scheduled jobs are enabled by this package.

## Complete host setup

These one-time research-agent steps need an ordinary terminal with network access.
In addition to the Docker startup prerequisites above, install Git, uv, and Go matching
the inspected Multica checkout's `server/go.mod` to build the host CLI. Authenticate your
chosen coding CLI. These are agent-runtime requirements, not everyday server startup steps.

On Windows, from this directory:

```powershell
# Builds the existing source; generates secrets only when .env is absent.
./Start-Multica.cmd

# Build the CLI from the same checkout as the server; avoids release/main mismatch.
New-Item -ItemType Directory -Force .local | Out-Null
Push-Location ../multica/server
go build -o ../../recsys-research/.local/multica.exe ./cmd/multica
Pop-Location
```

Open http://localhost:3000, request a login code and create a workspace. With no SMTP
configured, retrieve that code locally from `docker compose -f docker-compose.selfhost.yml
logs backend` in the Multica checkout. Do not paste credentials into research notes.

```powershell
./.local/multica.exe setup self-host
./.local/multica.exe daemon status
./.local/multica.exe daemon autostart enable
```

Autostart is login-based. A successful command does not prove unattended reboot recovery:
test reboot, service health, daemon online status and an agent run on the intended host.
Docker must also start. On a Linux server, use `make selfhost-build` in the pinned checkout
and build `./cmd/multica` with Go; the Python preparation/provisioning scripts are portable.

Then prepare the research environment (choose the framework needed now):

```powershell
./setup/Initialize-Research.ps1 -Framework recbole
# Alternatives: -Framework torch, or -Framework lightning
uv run --frozen python setup/prepare_sources.py
```

Review and commit `uv.lock`, `setup/sources.lock.json`, and `setup/source-files.sha256.json`.
They are deliberately not fabricated when fetching is blocked. The current version ranges
are a starting specification; only a successful resolver, imports and smoke run establish
compatibility. GPU/CUDA environments need their own recorded and tested dependency choice.

Get the workspace, runtime and daemon IDs from Multica. Provision once:

```powershell
uv run --frozen python setup/provision.py --cli .local/multica.exe --workspace-id YOUR_WORKSPACE --runtime-id YOUR_RUNTIME --daemon-id YOUR_DAEMON
```

The script creates the four agents, imports and attaches their skills, creates a squad,
and attaches this directory to the project. It saves returned IDs under `.local/` so it can
resume a partial setup. Existing conflicting skill names fail rather than being overwritten.
Review the created objects in the UI. Keep this provisioning state private and backed up.
The local directory uses `in_place` execution to serialize edits on a single checkout.
If moving to a remote host, copy the repository there and provision from its real path.

## W&B and the first run

Default tracking is offline. For online tracking in the launching environment:

```powershell
uv run --frozen wandb login
$env:WANDB_ENTITY = 'your-entity'
$env:WANDB_PROJECT = 'recsys-research'
$env:WANDB_MODE = 'online'
```

Configure the same environment for the daemon's training runtime; a new terminal's variables
do not automatically reach an already-running daemon. Never store the API key in Git or
agent instructions. Offline runs can later be synced with `wandb sync PATH_TO_OFFLINE_RUN`.

Create the first issue in the project and assign the squad. Ask Reviewer to review
[EXP-000](notes/EXP-000-environment-smoke.md) and its config. After the plan passes and
code/lock/config are committed, the implementer runs:

```powershell
uv run --frozen --extra recbole python scripts/smoke_recbole.py
```

The runner refuses a missing/untracked lock or dirty checkout. It records dependency versions,
config, commit, data hash, exact split membership, token mapping, logs, checkpoint, metrics
and W&B reference. Basic split and metric checks are automated. A completed run stays
**unreviewed**: independent review must still inspect training, replay and interpretation.
Gate instructions guide agents; they are not hard access controls in Multica.

For real experiments, use framework-specific entry points with the same evidence contract
in AGENTS.md. Do not extend the synthetic runner into an implicit universal training API.
PyTorch/Lightning can use the shared provenance helpers and W&B directly; no training adapter
for an unspecified architecture has been invented. Document benchmark-specific leakage
rules and metric definitions in the experiment plan.

## Continuity and optional Slack

Commit atomic changes; keep one next action in Home. Before upgrades run
`./setup/Backup-Multica.ps1`. It saves a checked Postgres dump, uploads and `.env` privately;
a restore rehearsal remains required. Preserve local experiment artifacts and synced W&B
artifacts, not only summary metrics. Archive image digests for deployments you need to restore.

For Slack, use the [official manifest](https://multica.ai/docs/slack-bot-integration).
Start with only Coordinator: provide its `xoxb-` and `xapp-` tokens in Multica's integration
settings. The fresh server setup generates `MULTICA_SLACK_SECRET_KEY`; an existing `.env`
is preserved and needs that key configured separately. Socket Mode needs no public webhook.
Do not add automatic summaries until the channel and desired schedule are selected.

## Validation performed here

Five unit checks passed: cross-split leakage, duplicate interactions, valid splits,
invalid ranking metrics and changed-data hashes. Both custom skills passed the skill
validator. Python files compiled and PowerShell scripts parsed. These checks used the
available bundled Python 3.12, not the pending Python 3.11 research environment.

Not verified: dependency resolution, Ruff/pytest under uv, container build/readiness,
CLI provisioning against a live server, training, W&B sync, Slack, reboot or restore.

Docker launcher: `node --test setup/start-multica.test.mjs` checks fresh secrets,
database credential consistency, incompatible templates and actual localhost port parsing.
Full startup remains blocked until Docker Desktop is installed and accessible.

Sources: [self hosting](https://multica.ai/docs/self-host-quickstart),
[Squads](https://multica.ai/docs/squads), [skills](https://multica.ai/docs/skills),
[upstream selection](setup/sources.json). CLI flags were checked against the local pinned source.
