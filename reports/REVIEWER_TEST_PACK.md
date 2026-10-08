# AI-Assisted Self-Test Pack

These are real local-model observations against an **AI-assisted self-test pack
with predicted expectations** supplied by the candidate. It is a development aid,
not an external reviewer evaluation or independently validated ground truth.
The observations are not mocked responses or a claim of clinical readiness. Predicted labels are
preserved in `evals/reviewer-test-pack.json`; the four non-identifying PDF fixtures
are in `evals/fixtures/reviewer/`. Original attachment hashes are retained. The
original DOCX and ZIP are excluded from publication.

## Historical Journals (Before Policy 3)

All 20 inputs were exercised before policy version 3. The run returned 17 valid
six-field responses and three service errors. Of those 17 responses, 13 agreed
with predicted sentiment, emotion and risk; four disagreed. The original automated
checker also counted provisional mood ranges, yielding 7 all-field matches and
10 disagreements. That is not a fair count of substantive label failures: mood
ranges were guesses and are a separate calibration concern, not ground truth.

- J1 returned MEDIUM rather than the assignment example's HIGH. This is a
  substantive screening-policy miss in the original observations.
- J2 and J12 returned neutral emotion where happy was expected. J4-J6, J13-J14,
  J18-J19 disagreed with expected mood ranges (J14 also with emotion).
- J15 and J16 each returned SUMMARY_UNSUPPORTED twice, including the one identical
  retry allowed by the pack. J20 exceeded its 60-second deadline.
- J9 and J17 returned HIGH for explicit risk language; this tiny sample does not
  establish clinical safety or prompt-injection immunity.
- Summary checks cover sentence count, numbers and selected assertions, not full
  semantic fidelity. Manual inspection of J10 found that "ongoing conflict"
  overinterprets "tired of fighting". C1/A3's short summary repeats its sentence.

`reviewer-journals.json` retains complete responses and attempts. The initial
Ollama loading failures are retained separately rather than silently discarded.

## Historical HTTP, Documents and Grounding

The 56 non-journal cases include real restarts, fresh uploads, separate principals,
deletion and concurrent HTTP requests. `reviewer-protocol.json` retains expectations,
response bodies, timings and each check. An HTTP 200 alone is not a semantic pass.
The observed totals are 45 PASS, 9 MISMATCH and 2 EXPECTATION_CONFLICT. All eight
document-handling cases passed, as did cross-document abstention, principal
isolation, restart persistence and deletion. Of 22 RAG cases, 15 passed and seven
disagreed. The travel-policy positive-answer check I1 failed separately.

- R2 omits the five-day cap and 31 March expiry from its answer. R8 omits manager
  approval; R18 omits director approval. Their exact citations contain those
  conditions, but that does not repair the incomplete answer text.
- R12, R14 and R19 return ANSWER_UNSUPPORTED errors, not the requested partial,
  abstention or supported answer. I1 likewise rejects the travel-policy answer.
- R17 corrects the false 30-day premise to 24 days, but reports PARTIAL instead of
  ANSWERED. This is a status mismatch, not agreement with the false premise.
- C9's Latin-script Hinglish input times out. English-only support and imperfect
  language detection remain documented limitations.
- C10's supplied recipe correctly contains 8000 characters (C11 contains 8001).
  The 8000-character repeated input exceeds the separate documented 2000-token
  limit and returns 413. Its unconditional expected 200 conflicts with that limit.
- A6 distinguishes admission capacity from completion: one active plus two queued
  slots do not promise three successes within a deadline that includes queue time.
  Actual results were two 200s, two immediate QUEUE_FULL 429s and one 504 at 30.031
  seconds. The queue bound worked; the pack's three-success expectation was not met.

## Initial Recovery Correction

The long journal initially kept the CPU busy after its response timed out and
expired queued requests could start more work. A narrow deadline/batching fix was
made without changing model weights, policy thresholds, prompts or architecture.
At that stage, five regression tests brought the deterministic Windows suite to 70 passing tests.

That initial post-fix real check still returned 504 for J20 at 60.016 seconds. The next
unsupported-language request returns 422 in 0.015 seconds and the following short
journal succeeds in 18.422 seconds. See `reviewer-timeout-recovery.json` and
`CORRECTIONS.md`. Initial queue failures remain in a separate report.

The original full journal run preceded that correction; the original protocol rerun
and policy-2 walkthrough followed it. The frozen earlier evaluation was not relabeled or replaced.
The original walkthrough was illustrative evidence, not a substitute for these retained
failures or a claim that all 76 cases pass.

## Policy 3 Follow-Up

That correction used a narrow current-personal-giving-up/hopelessness plus
supported-distress HIGH rule, a strong-positive/neutral-emotion consistency rule,
gentler mood mapping, constrained exact-source summary quotes and explicit float32
CPU NLI. Long entries retain full-entry sentiment and safety scoring, with emotion
scored from verified summary excerpts. This can miss emotions absent from those
excerpts and is explicitly not full-entry emotion coverage.

Separate [journal regression results](JOURNAL_POLICY3_REGRESSION.md) include every
original journal, J1 and three development paraphrases, plus a natural long entry.
[Policy-condition results](POLICY_CONDITION_REGRESSION.md) check the omitted
cap/expiry/approval conditions and four other prior RAG disagreements. These are
post-change regression checks, not a replacement for the original 76-case run.
The frozen held-out set and old measurements remain unchanged and are labeled
as measured before policy version 3. Updated videos are indexed in
[`docs/WALKTHROUGH.md`](../docs/WALKTHROUGH.md).

The final journal regression returned 20/20 valid pack responses, 19 predicted-label
agreements and one emotion disagreement (J14: sad). J1/dev51-dev54 returned HIGH,
while J5/J6/J7/J14 did not. J2/J12 returned happy; J15/J16/J20 succeeded. J20 and
the separate natural 512-word journal each took 13.406 seconds. J17's literal risk
sentence is repeated; a two-sentence output does not guarantee a good summary.
Low happy confidence for J12 is retained rather than cosmetically increased.

The targeted document follow-up received fresh 201/READY in 0.906 seconds.
R2/R8/R18 include all predicted qualifying facts with exact quotes on the correct
pages; R19 and R17 pass. R12 and R14 still return `ANSWER_UNSUPPORTED` rather than
the predicted partial/abstention status. Those errors were unresolved at policy 3. This was
five matching targeted cases and two service errors, not a new 76-case pass count.

## Policy 4 Follow-Up

Current decision confidence uses the normalized selected emotion score, or the
winning sentiment score when positive/neutral consistency supplies happy. J2/J12
now return 0.9773/0.9736. Every journal starts actual local LLM generation; verified
third-person text is retained rather than forcibly replaced with risk quotes.
After two failures a bounded extractive candidate must still pass evidence checks.
One-fact entries receive non-repeating scope text. Generation token counts and
summary path metadata accompany the [current journal report](JOURNAL_POLICY4_REGRESSION.md).

The ten unchanged user-supplied unseen entries were run once without retries or
tuning. All ten returned valid responses; eight matched the specified labels.
U6 returned anger/MEDIUM instead of sad/HIGH; U10 returned MEDIUM rather than HIGH
while excluding its injected instruction. U7/U8/U9 returned LOW/LOW/MEDIUM.
The [complete unseen report](UNSEEN_REVIEW_10.md) includes inputs, six-field
responses, confidence interpretation, timings and generation evidence. High
emotion confidence does not validate the independent screening risk.

The [current document regression](POLICY4_CONDITION_REGRESSION.md) rechecks R12/R14
and prior qualifier cases. Original policy-3 failures above remain historical
observations. Current latency uses independent nanosecond clock intervals; the
old equal 13.406-second values retain their original rounded precision.
