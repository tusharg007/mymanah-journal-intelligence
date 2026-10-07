# Evaluation Evidence

`development.json` contains 50 English journals, including the original 20-case feasibility set. `heldout.json` contains 100 separately authored English journals, written before observing model outputs. `rag_cases.json` contains a readable ten-page synthetic policy and 30 questions, including exceptions, partial evidence, missing facts, and injected instructions. They are artificial, non-identifying fixtures with provisional engineering annotations, not clinician-reviewed data. Candidate review of label ambiguities is required before final performance claims.

The held-out set is deliberately balanced by dominant emotion except for two extra explicit-danger cases. Its sentiment distribution is not balanced; publish class counts and macro metrics, not only overall accuracy. Its simple writing and explicit emotion words can inflate apparent quality. It does not establish real-world, clinical, multilingual or nuanced-journal accuracy. Expanded negation/contrast cases belong in development and critical regression suites.

Do not tune prompts or hypotheses on held-out outputs and then call the same report unbiased held-out performance. Record post-correction reruns as regression results. A fluent reviewer is required before any Hindi/Hinglish smoke annotations can support even limited claims. No metrics have been prefilled in this directory.
