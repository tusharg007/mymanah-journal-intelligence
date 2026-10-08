# Bounded Development Corrections

The original measured CPU report is retained in `cpu-development.json` under journal-policy-1.
It includes 18/20 matching emotion labels and 16/20 matching screening labels, including
0/4 MEDIUM predictions. Labels are provisional synthetic engineering annotations, not clinical ground truth.

Before the held-out run, journal-policy-2 changes the happy hypothesis to explicitly include
pleased/proud/grateful wording and narrows neutral to routine activities with no emotional reaction.
MEDIUM now includes supported overwhelming distress, or supported
persistent distress together with impairment, as described in the approved plan. HIGH thresholds
and the original explicit-danger rules are unchanged. Threat-related MEDIUM cases may still be missed.

One bounded generator-prompt revision supplies the schema in the prompt, explicitly defines the
answerability/completeness flags, and requests only question-relevant claims. Native JSON-schema
constraints and original-context quote/number/NLI verification remain active. No answer is hard-coded.

Empty Ollama warmup did not initialize first decoding on this machine. Startup now performs
one real schema-constrained decoding token before declaring readiness; initialization uses its own
120-second bound rather than consuming the reviewer's first short-entry deadline.

The first live run returned a short-journal timeout and contradictory RAG flags. The next run
returned real successful inference but failed semantic assertions for happy/neutral and an extra
supported page-2 claim. Subsequent results are post-correction regression results, not untouched
measurements. Held-out labels will not be revised after observing predictions.

The contract smoke now checks the required emotion vocabulary rather than making one
proud/neutral disagreement a model-quality release gate. That disagreement remains visible
in the development reports and must not be described as corrected.

The 4B candidate subsequently loaded all 37 layers on the GPU with a 256 MiB fitting
reserve. Both candidates retain their measured failures; the original allocation failure
is not removed from the comparison history. Security-updated classifier packages changed
CPU timing, so the candidate timing runs are not a controlled isolated speed comparison.

## Reviewer Pack: Deadline Recovery

The external 76-case reviewer pack exposed a long journal continuing CPU work after
its HTTP timeout, with expired queued requests then starting unnecessary inference.
Admission now expires waiting requests at their original deadline. Journal language
and token preflight occurs before admission; classifier work checks the deadline
between batches and caps each NLI batch at 1024 padded tokens (maximum eight rows).
An active Torch forward pass is not forcibly interrupted. Model weights, prompts,
screening thresholds, mood formula and approved architecture were not changed.

Five focused regression tests bring the Windows deterministic suite to 70 passing
tests. The real long entry still times out at 60 seconds; the following unsupported
language request returns 422 immediately and a short journal succeeds in 18.422
seconds. This corrects recovery, not long-entry latency. Initial failed runs remain
in the reviewer reports. The external pack also reveals semantic disagreements and
controlled model errors; see `REVIEWER_TEST_PACK.md`, not an all-pass claim.
