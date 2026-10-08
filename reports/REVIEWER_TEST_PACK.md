# External Reviewer Test Pack

These are real local-model observations against the supplied 76-case pack, not
mocked responses or a claim of production/clinical readiness. Expected labels are
preserved in `evals/reviewer-test-pack.json`; the four non-identifying PDF fixtures
are in `evals/fixtures/reviewer/`. Original attachment hashes are retained. The
original DOCX and ZIP are excluded from publication.

## Journals

All 20 inputs were exercised. The completed run returned 17 valid six-field
responses: 7 matched every automated check and 10 disagreed with at least one
expected label or mood range. Three cases produced service errors. These are
counts on this small authored set, not statistical release gates.

- J1 returned MEDIUM rather than the pack's required HIGH for prolonged distress.
  This is a substantive screening-policy miss and is visible in the recording.
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

## HTTP, Documents and Grounding

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

## Recovery Correction

The long journal initially kept the CPU busy after its response timed out and
expired queued requests could start more work. A narrow deadline/batching fix was
made without changing model weights, policy thresholds, prompts or architecture.
Five regression tests bring the deterministic Windows suite to 70 passing tests.

The post-fix real check still returns 504 for J20 at 60.016 seconds. The next
unsupported-language request returns 422 in 0.015 seconds and the following short
journal succeeds in 18.422 seconds. See `reviewer-timeout-recovery.json` and
`CORRECTIONS.md`. Initial queue failures remain in a separate report.

The full journal run preceded that correction; the protocol rerun and expanded
walkthrough follow it. The frozen earlier evaluation was not relabeled or replaced.
The walkthrough is illustrative evidence, not a substitute for these retained
failures or a claim that all 76 cases pass.
