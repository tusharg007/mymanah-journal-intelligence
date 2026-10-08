# Evaluation Evidence

`reviewer-test-pack.json` preserves all 76 AI-assisted predicted expectations before
execution; `fixtures/reviewer/` contains the four supplied synthetic PDFs. These
are self-test development cases, not new training data or a replacement held-out
benchmark. [Observed results](../reports/REVIEWER_TEST_PACK.md) include failures.
With the real local API ready, `python -m scripts.reviewer_journals` runs the 20
journals. `python -m scripts.reviewer_protocol` runs the other 56 on Windows and
temporarily restarts the workspace API for cold-start, keyed isolation and
persistence checks, restoring credential-free loopback service afterward. Do not
run the two scripts concurrently. Run these operational checks only against a
dedicated local review instance, not a shared production service.

`development.json` contains the original 50 English journals plus four policy-version-3 regression cases (dev51-dev54). `long-journal-development.txt` adds a natural long-entry latency check. These additions are not included in the original 50-case generator comparison. `heldout.json` contains 100 separately authored English journals, written before observing model outputs; its published measurements predate policy version 3. `rag_cases.json` contains a readable ten-page synthetic policy and 30 questions, including exceptions, partial evidence, missing facts, and injected instructions. They are artificial, non-identifying fixtures with provisional engineering annotations, not clinician-reviewed data. Candidate review of label ambiguities is required before final performance claims.

Current corrections are checked with `python -m scripts.journal_regression --output reports/journal-policy4-regression.json` and
`python -m scripts.policy_condition_regression --output reports/policy4-condition-regression.json`. These write separate post-change
reports and do not replace the original 76-case or frozen held-out observations.

`unseen-review-10.json` preserves the user's ten unchanged entries and specified
expectations. `python -m scripts.unseen_review` runs them once without HTTP retries
and refuses to overwrite an existing report. Input and implementation hashes,
every response, confidence source and generator metadata are retained in
`reports/unseen-review-10.json`. No model, hypothesis, threshold or prompt changes
are made after observing this run. The cases remain an assessment set rather than
development tuning data. Ten predicted cases do not establish broad generalization.

The held-out set is deliberately balanced by dominant emotion except for two extra explicit-danger cases. Its sentiment distribution is not balanced; publish class counts and macro metrics, not only overall accuracy. Its simple writing and explicit emotion words can inflate apparent quality. It does not establish real-world, clinical, multilingual or nuanced-journal accuracy. Expanded negation/contrast cases belong in development and critical regression suites.

Do not tune prompts or hypotheses on held-out outputs and then call the same report unbiased held-out performance. Record post-correction reruns as regression results. A fluent reviewer is required before any Hindi/Hinglish smoke annotations can support even limited claims. No metrics have been prefilled in this directory.

`python -m evals.reliability reports/heldout-qwen4b.json reports/heldout-score-reliability.json` summarizes the returned confidence heuristic by score bin without fitting calibration. It compares joint sentiment/emotion agreement, not correctness of every response field. Empty bins remain unobserved and rejected responses remain visible in coverage. Full probability vectors were not retained, so task-wise Brier scores cannot be computed from this report.
