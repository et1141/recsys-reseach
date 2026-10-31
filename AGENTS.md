# Research contract

Use RecBole where suitable; use PyTorch, Lightning, or another justified tool when the
research question requires it. Never change the hypothesis merely to fit a framework.
Prefer simple baselines and small falsifiable experiments before architectural complexity.

Read notes/Home.md, the issue, and its experiment note before work. Use one experiment
ID across the issue, note, branch, run group, artifacts, and review. Keep one weekly
goal and one next action. The human controls scope and final acceptance.

Required handoffs: researcher plan -> independent reviewer plan/data approval ->
implementer smoke run -> independent reviewer smoke approval -> planned runs ->
independent reviewer evidence/interpretation review -> human acceptance. Failures
return to the implementer. The author cannot approve their own stage. These are
agent workflow rules, not a security boundary or a server-enforced state machine.

Every run needs a committed code revision, committed uv.lock, resolved configuration,
framework/dependency versions, command, hardware, seed, dataset source/version/license
and file hashes, preprocessing and split identities, sampling and evaluation protocol,
checkpoint selection rule, parameters, metrics, logs and artifacts. Save exact split
membership. Keep raw data and credentials out of Git and W&B uploads by default.
Never call a dependency specification a lock, or a smoke run a reproduced result.

Fit preprocessing on training data. Choose hyperparameters and checkpoints using
validation only; isolate the test set. Record repeated interactions, cold-start policy,
temporal leakage, candidate universe, masking and full versus sampled ranking.
Use comparable budgets and tuned baselines. Predeclare seeds and uncertainty analysis.
Report negative results and deviations. Verify finite losses, gradients where applicable,
metric ranges, a tiny overfit check and baseline sanity before scaling training.

Use uv, Ruff, type annotations and meaningful pytest tests for research code.
Run uv sync --frozen with the selected extra. No unattended expensive sweeps:
respect the plan's explicit GPU/time/run budget. Save progress before stopping.
Never silently substitute synthetic data for a benchmark.

Write one short atomic note per experiment using notes/templates/experiment.md.
Use [[wiki links]] for hypotheses, papers and related experiments; add those notes
only when useful. Preserve human text. Link evidence instead of copying logs.
Do not generate thesis prose or large reports unless requested.
