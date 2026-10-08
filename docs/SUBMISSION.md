# Submission Notes

Repository: https://github.com/tusharg007/mymanah-journal-intelligence

Actual recordings: [2:04 overview](walkthrough-short.mp4), [8:16 desktop walkthrough](walkthrough-desktop.mp4) and [4:33 mobile walkthrough](walkthrough-mobile.mp4), opening with J1's HIGH result. Diverse inputs come from an AI-assisted self-test pack with predicted expectations supplied by the candidate, plus a natural 512-word development entry. Results remain visible for reading with permanently embedded captions. [Compiled inputs and actual results](VIDEO_TEST_RESULTS.md), timestamps and source PDF accompany the recordings.

## Approach

I separated model adapters, text policy, journal processing, document ingestion/recovery, retrieval, persistence, admission control and HTTP contracts. FastAPI serves a React/TypeScript interface. Every journal starts real local Qwen3 4B generation concurrently with CPU classification. RoBERTa supplies English sentiment; NLI supplies the seven-label emotion taxonomy, contextual distress signals and claim-support verification. Standard fine-tuned emotion label sets do not directly cover anxiety and stress. The selected generator is a revision/hash-pinned Hugging Face GGUF served by local Ollama, without hosted LLM APIs.

The LLM produces third-person summary sentences and selects exact source quotes through a constrained JSON schema. Source, number and NLI checks verify them before return; one repair is allowed. After two generation/verification failures, bounded extracts may be returned only after the same evidence checks, within the deadline. Deadline errors remain errors. One-fact entries receive truthful scope text instead of repeated sentences. Reports retain generator token counts and summary-path metadata.

Confidence reports the normalized selected emotion score, or winning sentiment confidence when positive/neutral consistency supplies happy. J2/J12 report 0.9773/0.9736. This is an uncalibrated decision score and does not validate independently selected screening risk, summaries or all response fields jointly.

Uploaded PDFs are bounded and parsed in an isolated subprocess, chunked by page/token budget, embedded with E5 and indexed in a generation-specific Chroma collection. SQLite owns document state, quotas and canonical citation text. Dense retrieval and BM25+ are fused. A pre-generation topic guard abstains on absent modifiers such as paternity leave. Mixed questions generate their supported part, verify its claims and return PARTIAL with the uncovered question named. Claims require exact quotes, supported numbers and original-context NLI checks. READY is published only after indexing/probing, enabling immediate questions.

Loopback review is credential-free by default. API keys are opt-in, remote binding requires keys, and document/source access is principal-scoped. Upload cancellation, interrupted-ingestion recovery, deletion, finite deadlines, bounded concurrency and quiesced backup/restore are tested. Runtime uses local artifacts with offline Hugging Face settings and disabled Ollama cloud features. Dependency/model/frontend locks, reproducible bootstrap scripts and measured reports are included.

## Evidence

- Windows deterministic suite: 109 passing tests. Linux deterministic/build checks run on each push. The prior Linux CPU Docker real-model suite passed two tests; it predates policy version 3.
- All 76 AI-assisted self-test cases were exercised before policy version 3. Original errors and measurements remain in the [self-test report](../reports/REVIEWER_TEST_PACK.md). The [current journal regression](../reports/JOURNAL_POLICY4_REGRESSION.md) contains 20 pack inputs, four J1 regressions and the 512-word entry, including every response, generator token counts, confidence sources and separate full-precision timings. Predictions are not independent ground truth; mood guesses are separate from label comparisons.
- Current pack regression: 20/20 valid responses and 19/20 predicted-label agreements, with J14's emotion disagreement retained. All 25 development summaries used generation. Short pack-entry p50/p95 was 2.467/2.706 seconds (19 samples); J20 took 23.807809 seconds and the 512-word entry 20.539648 seconds. Earlier equal 13.406-second values remain historical rounded observations, not current measurements.
- The ten new user-supplied inputs were run once, unchanged, with no subsequent tuning: 10/10 valid responses and 8/10 matching all specified labels. U6 returned anger/MEDIUM instead of sad/HIGH; U10 returned MEDIUM instead of HIGH while excluding its injected instruction. U7/U8/U9 returned LOW/LOW/MEDIUM. The [unseen report](../reports/UNSEEN_REVIEW_10.md) includes all inputs, summaries and confidence interpretations. Warm sequential p50/p95 was 1.829/2.241 seconds across these ten short entries; this small sample is not a production guarantee.
- The [current targeted PDF regression](../reports/POLICY4_CONDITION_REGRESSION.md) rechecks R12/R14 and previously omitted cap/expiry/approval conditions. This is a separate follow-up, not a new 76-case pass count.
- All seven targeted PDF checks matched predicted status/fact/page checks, following fresh HTTP 201 READY in 1.329 seconds. R14 abstained in 0.062 seconds without citations; R12 retained the sick-leave certificate condition and named the uncovered stock-option question.
- Generator comparison, before policy version 3: 4B validated 49/50 development journals and returned 30/30 document-question responses; 1.5B validated 41/50 journals and returned 21/30 question responses. Failures are retained.
- Frozen 100-case English evaluation, measured before policy version 3: 96 validated responses; label agreement including service errors was 95/100 sentiment, 93/100 emotion and 81/100 screening priority. Successful-request p50/p95 was 11.71/18.39 seconds on the tested laptop. These numbers do not measure the current corrections.
- Fine-tuned sentiment baseline: RoBERTa 99/100 matching annotations, versus NLI sentiment 97/100. Counts, macro metrics, confusion matrices and uncertainty are published.
- New ten-page PDF: synchronous READY in 0.865 seconds. Expected-page retrieval hit 27/27 answerable/partial cases. Automated end-to-end matches were 27/30; one is a matcher false negative and two are conservative full abstentions instead of partial answers.
- Desktop/mobile real workflows, nonblank PDF canvas, source-page navigation, four-width responsive checks, offline API-process smoke and restored-index/keyed-isolation rehearsal passed.
- Linux image build, non-root fail-closed startup and [full real-model CPU Docker integration](https://github.com/tusharg007/mymanah-journal-intelligence/actions/runs/37673144901) passed. The fresh CPU runner observed a 19.69-second journal and a 0.898-second two-page READY upload; these are smoke observations, not latency percentiles. Linux GPU execution is not yet verified.

## Assumptions and Limitations

English journals and text-based English PDFs are the supported release. Hindi/Hinglish is an unimplemented optional extension; ambiguous Latin-script language detection is imperfect. Scanned/encrypted/corrupt or unusable PDFs fail explicitly; there is no OCR or reliable table-layout interpretation. Questions are standalone and use one authorized document, without external facts or chat memory.

Screening labels are an assignment policy, not clinical risk prediction. MEDIUM recall is weak (13/28 in the held-out fixtures); two correctly classified HIGH examples do not establish safety. Emotion can be wrong even at high classification scores. Confidence and mood are uncalibrated heuristics, not validated probabilities or clinical scales. Some valid summaries are conservatively rejected, and NLI verification is fallible.

The original prolonged-distress miss, positive/neutral inconsistency and three
journal service errors were corrected on development inputs. The unseen U6/U10
screening misses show limited generalization. Figurative J14 still returns sad
rather than the predicted neutral/anger, and its generated summary overinterprets
'Never again' as an intent to avoid similar meetings despite passing NLI. Generated
summaries can overinterpret, omit details or repeat ideas. J17 now gives a generated
risk sentence followed by 'No further details are given.' Long-entry emotion is
derived from verified summary excerpts and can miss feelings elsewhere in the entry.
Qualifying conditions and residual document-answer disagreements are reported
separately in the targeted policy-condition regression.

R2/R8/R18 preserve cap/expiry/approval conditions with exact citations. R12 returns
verified sick leave as PARTIAL; R14 returns uncited INSUFFICIENT_EVIDENCE before
generation. The lexical topic guard can miss synonyms; absence from retrieved
chunks does not prove absence from the whole document. Conditions outside the
chosen quote can still be omitted. Historical failures remain available.

Evaluation cases have provisional engineering annotations and simple synthetic language, not independent clinician/human validation. No zero-bug, zero-hallucination, clinical-readiness or horizontal-scalability guarantee is made. The implementation uses one application process with embedded storage and bounded local inference, not a distributed service.

The security report retains scoped Chroma server advisories and the audit's CPU-Torch coverage gap. The embedded profile avoids the affected HTTP/configuration surfaces; this is not a claim of zero vulnerabilities. Public hosting would additionally require TLS, reviewed proxy controls, secret management and operational hardening.
