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

The original contract smoke checked the required emotion vocabulary rather than making one
proud/neutral disagreement a model-quality release gate. That disagreement remains visible
in the original development reports; policy version 3's later correction is measured separately.

The 4B candidate subsequently loaded all 37 layers on the GPU with a 256 MiB fitting
reserve. Both candidates retain their measured failures; the original allocation failure
is not removed from the comparison history. Security-updated classifier packages changed
CPU timing, so the candidate timing runs are not a controlled isolated speed comparison.

## Reviewer Pack: Deadline Recovery

The AI-assisted 76-case self-test pack with predicted expectations exposed a long journal continuing CPU work after
its HTTP timeout, with expired queued requests then starting unnecessary inference.
Admission now expires waiting requests at their original deadline. Journal language
and token preflight occurs before admission; classifier work checks the deadline
between batches and caps each NLI batch at 1024 padded tokens (maximum eight rows).
An active Torch forward pass is not forcibly interrupted. Model weights, prompts,
screening thresholds, mood formula and approved architecture were not changed.

At that stage, five focused regression tests brought the Windows deterministic suite to 70 passing
tests. The real long entry still timed out at 60 seconds; the following unsupported
language request returns 422 immediately and a short journal succeeds in 18.422
seconds. This corrects recovery, not long-entry latency. Initial failed runs remain
in the historical reports. The self-test pack also revealed semantic disagreements and
controlled model errors; see `REVIEWER_TEST_PACK.md`, not an all-pass claim.

## Policy Version 3: Development Corrections

J1's assignment example and three paraphrases were added as dev51-dev54, not to the
frozen held-out set. Current personal giving-up/hopelessness language together
with one supported distress signal gives HIGH. Context controls cover figurative
speech, negation, recovery, other people and giving up an activity. J5/J6/J7/J14
are explicitly rechecked through the real API.

Strong positive sentiment resolves a neutral-emotion prediction to happy without
inflating confidence; the returned confidence still includes the weak happy NLI
score. Mood reserves 1-2 for HIGH, floors ordinary negative entries at 3, and caps
positive entries with a negative dominant emotion at 7. None of these scores is a
validated clinical scale or probability.

The checkpoint declares float16. Explicit float32 CPU loading removed a major
latency cost on this Windows CPU. Dynamic int8 was tested and rejected: all six
real probe summaries failed support checks. It is not exposed as a release option.
No model pins or downloaded weight bytes changed. Full-entry NLI safety uses seven
hypotheses per 160-token window; long-entry emotion uses exact excerpts supporting
the verified summary. This trades full-entry emotion coverage for bounded latency,
not full-entry risk coverage.

The generator's native JSON schema restricts summary quotes to actual source spans.
Exact quote, number and original-context NLI checks remain active. Crisis statements
preserve the selected source quote literally, preventing additions such as "actively".
A non-risk summary that copies the entire entry gets one bounded style rewrite;
there is still no fabricated fallback summary. RAG instructions now explicitly
retain relevant caps, expiry dates and approval conditions.

Recognized model-control directives are omitted from summary evidence, but not
from full-entry classification. Summary validation rejects model-control metadata
and unsupported explicit causal qualifiers. These narrow guards do not prove
general prompt-injection immunity or hallucination prevention.

Prompt changes alone did not reliably preserve policy qualifiers. After successful
claim/citation verification, answer assembly retains the complete cited policy
sentence for explicit approval/carry-over/qualifying language. It does not repair
failed claims or add uncited facts. Conditions outside the selected quote can still
be missed. The targeted report records both complete results and residual failures.

At that stage the deterministic suite contained 96 passing Windows tests. Separate real-model
regressions are published in `JOURNAL_POLICY3_REGRESSION.md` and
`POLICY_CONDITION_REGRESSION.md`. Original development, held-out and 76-case raw
observations are not overwritten; they precede these corrections. Small regression
sets demonstrate observed behavior, not zero-error guarantees or clinical safety.

## Policy Version 4: Decision Scores and Generated Summaries

The positive/neutral emotion consistency decision now reports winning sentiment
confidence, rather than a discarded tiny happy NLI score. Other responses report
the normalized selected emotion score. Positive sentiment consistently resolves
neutral emotion to happy without the previous 0.80 cutoff. Confidence remains
uncalibrated and is not a joint probability of every output field being correct.

Every journal begins an actual Qwen3 4B generation call alongside classification.
Third-person generated sentences retain constrained source quotes and factual
verification. HIGH-risk results no longer force all sentences to literal quotes.
A single factual sentence receives deterministic scope text instead of duplication.
After two failed generation/verification attempts, bounded verbatim extracts must
still pass the evidence checks; deadline errors remain errors. Inference metadata
records output token counts, summary path and confidence source without user text.

RAG checks content-topic absence in retrieved evidence before generation. It
abstains on absent topics such as paternity leave and generates only supported
parts of mixed questions, marking verified answers PARTIAL and naming uncovered
parts. Qualifier preservation now includes explicit 'required' language, retaining
the sick-leave medical-certificate condition. The lexical guard is conservative
and imperfect; absence from retrieved chunks is not proof of whole-document absence.

The ten user-supplied unseen inputs were run once, unchanged, with implementation
hashes retained and no subsequent tuning. Eight matched every specified label;
U6/U10 remained screening misses and U6 also disagreed on emotion. Confidence
checks are decision-score consistency checks, not correctness guarantees. The
earlier frozen held-out percentiles remain explicitly pre-change measurements.
Separate current development timings retain input hashes and full clock precision.

The final deterministic suite contains 109 passing tests. The current reports are
`JOURNAL_POLICY4_REGRESSION.md`, `UNSEEN_REVIEW_10.md` and
`POLICY4_CONDITION_REGRESSION.md`; all prior raw measurements are preserved.

After the unseen run, a separate development boundary check found that an
unpunctuated extract plus scope text could count as only one sentence. Presentation
now appends terminal punctuation before joining sentences. This is a formatting
correction, not a model/prompt/policy or confidence adjustment. No unseen inputs
were rerun. Their original implementation hashes and results are retained; the
release differs only in this presentation helper, which leaves the already
punctuated assessment summaries unchanged.
