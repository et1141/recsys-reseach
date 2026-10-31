---
name: research-verification
description: Independently review recommendation experiment plans, data, training health and result claims across frameworks.
---

Read AGENTS.md and the exact experiment note. Review the actual artifacts, not the
implementer's summary alone. Do not approve work you authored. If independence is
unavailable, leave the gate pending and ask the coordinator to route another reviewer.

Plan/data: identify the falsifiable claim; verify paper source, baseline comparability,
split membership and disjointness, temporal policy, duplicate interactions, preprocessing
fit boundaries, cold-start handling, negative sampling, candidate set and test isolation.
Check seed list, tuning budget, stopping rule and metric definition before compute.

Smoke: inspect losses, finite metrics, checkpoint load/evaluate, deterministic replay
within declared tolerances, tiny overfit behavior and simple baseline sanity. A running
program alone is insufficient. Distinguish a toy pipeline test from benchmark evidence.

Results: inspect exact revision/lock/data/splits/config, logs, W&B and checkpoint hashes;
recompute a metric on a small fixture and rerun a representative evaluation. Examine
variance across seeds, matched baseline tuning, ablations, leakage and alternative
explanations. Decide whether the result supports the hypothesis, is inconclusive, or
contradicts it. Failed results are valid evidence; do not tune on the test set.

Write a concise pass / changes-required / blocked verdict with reviewer identity,
stage, inspected evidence and one next action. Record outstanding checks explicitly.
The coordinator advances only after pass; human acceptance is a separate final step.
