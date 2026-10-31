---
id: EXP-000
status: blocked
framework: recbole
issue:
---
# EXP-000 — can the research pipeline run and preserve its evidence?

**Question:** Can a tiny CPU BPR run finish with finite metrics and replayable artifacts?

**Plan:** Deterministic synthetic interactions; seed 42; two epochs; full ranking;
random user-grouped 80/10/10 split. This tests plumbing only, not scientific quality.
Config: [smoke](../configs/recbole-smoke.yaml). Budget: one CPU run, ten minutes.

**Evidence:** Not run. Dependencies and uv.lock still need network-enabled setup.

**Result:** Pending. No research claims.

**Review:** Plan/data pending; smoke pending; final evidence pending.

**Decision:** Complete setup, then have Reviewer inspect the plan before execution.
