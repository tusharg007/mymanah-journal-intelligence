# Submission Notes

Repository: https://github.com/tusharg007/mymanah-journal-intelligence

Actual recordings: [2:04 overview](walkthrough-short.mp4), [8:16 desktop walkthrough](walkthrough-desktop.mp4) and [4:33 mobile walkthrough](walkthrough-mobile.mp4), opening with J1's HIGH result. Diverse inputs come from an AI-assisted self-test pack with predicted expectations supplied by the candidate, plus a natural 512-word development entry. Results remain visible for reading with permanently embedded captions. [Compiled inputs and actual results](VIDEO_TEST_RESULTS.md), timestamps and source PDF accompany the recordings.

## Approach

I separated model adapters, text policy, journal processing, document ingestion/recovery, retrieval, persistence, admission control and HTTP contracts. FastAPI serves a React/TypeScript interface. Every journal starts real local Qwen3 4B generation concurrently with CPU classification. RoBERTa supplies English sentiment; NLI supplies the seven-label emotion taxonomy, contextual distress signals and claim-support verification. Standard fine-tuned emotion label sets do not directly cover anxiety and stress. The selected generator is a revision/hash-pinned Hugging Face GGUF served by local Ollama, without hosted LLM APIs.

The LLM produces third-person summary sentences and selects exact source quotes through a constrained JSON schema. Source, number and NLI checks verify them before return; one repair is allowed. After two generation/verification failures, bounded extracts may be returned only after the same evidence checks, within the deadline. Deadline errors remain errors. One-fact entries receive truthful scope text instead of repeated sentences. Reports retain generator token counts and summary-path metadata.

Confidence reports the normalized selected emotion score, or winning sentiment confidence when positive/neutral consistency supplies happy. Policy 5 caps either score at 0.99 to avoid displaying certainty; this presentation ceiling is not statistical calibration. The policy-4 recordings show J2/J12 at 0.9773/0.9736. The score does not validate independently selected screening risk, summaries or all response fields jointly.

Uploaded PDFs are bounded and parsed in an isolated subprocess, chunked by page/token budget, embedded with E5 and indexed in a generation-specific Chroma collection. SQLite owns document state, quotas and canonical citation text. Dense retrieval and BM25+ are fused. A pre-generation topic guard abstains on absent modifiers such as paternity leave. Mixed questions generate their supported part, verify its claims and return PARTIAL with the uncovered question named. Claims require exact quotes, supported numbers and original-context NLI checks. READY is published only after indexing/probing, enabling immediate questions.

Loopback review is credential-free by default. API keys are opt-in, remote binding requires keys, and document/source access is principal-scoped. Upload cancellation, interrupted-ingestion recovery, deletion, finite deadlines, bounded concurrency and quiesced backup/restore are tested. Runtime uses local artifacts with offline Hugging Face settings and disabled Ollama cloud features. Dependency/model/frontend locks, reproducible bootstrap scripts and measured reports are included.

## Evidence

- Windows deterministic suite: 129 passing tests after the policy-5 correction and J12 quality check. Linux deterministic/build checks run on push and pull request, as configured in [checks.yml](../.github/workflows/checks.yml); the [verified policy-4 push run](https://github.com/tusharg007/mymanah-journal-intelligence/actions/runs/37850522620) passed. This is distinct from the prior manually dispatched Linux CPU Docker real-model suite, which passed two tests before policy version 3.
- All 76 AI-assisted self-test cases were exercised before policy version 3. Original errors and measurements remain in the [self-test report](../reports/REVIEWER_TEST_PACK.md). The [policy-4 journal regression](../reports/JOURNAL_POLICY4_REGRESSION.md) contains 20 pack inputs, four J1 regressions and the 512-word entry, including every response, generator token counts, confidence sources and separate full-precision timings. Predictions are not independent ground truth; mood guesses are separate from label comparisons.
- Policy-4 pack regression: 20/20 valid responses and 19/20 predicted-label agreements, with J14's emotion disagreement retained. All 25 development summaries used generation. On the tested GPU laptop, short pack-entry p50/p95 was 2.467/2.706 seconds (19 samples); J20 took 23.807809 seconds and the 512-word entry 20.539648 seconds. The recorded short entries took approximately 2.5-4.6 seconds on that same GPU laptop. Earlier equal 13.406-second values remain historical rounded observations, not current measurements.
- Ten assessment inputs written with AI assistance were run once, unchanged, on policy 4 before any tuning on their results: 10/10 valid responses and 8/10 matching all specified labels. U6 returned anger/MEDIUM instead of sad/HIGH; U10 returned MEDIUM instead of HIGH while excluding its injected instruction. U7/U8/U9 returned LOW/LOW/MEDIUM. The [original unseen report](../reports/UNSEEN_REVIEW_10.md) is preserved. On the tested GPU laptop, warm sequential p50/p95 was 1.829/2.241 seconds across these ten short entries; this small sample is not a production guarantee. U6/U10 and the U7-U9 controls are now seen development inputs for the explicitly requested policy-5 follow-up, not a fresh unseen evaluation.
- The [pre-change signal diagnostic](../reports/policy4-hopelessness-diagnostic.json) confirms U6/U10 had hopelessness scores 0.842/0.995 and overwhelm scores 0.628/0.572. Policy 4's 0.65 distress cutoff blocked HIGH; it did not require persistence and impairment simultaneously. Policy 5 accepts supported hopelessness with overwhelm at least 0.50, or persistence/impairment at least 0.65, retaining the original lexical-plus-distress path. The [policy-5 seen regression](../reports/JOURNAL_POLICY5_REGRESSION.md) reports all inputs and actual outputs separately; no generalization claim is made.
- Policy-5 follow-up: 30/30 valid responses and 28/30 matching specified labels; J14 and U6 retain emotion disagreements. U6/U10 return HIGH, U7/U8/U9 remain LOW/LOW/MEDIUM, and J5/J6/J7/J14 do not escalate. On the tested GPU laptop, J1-J19 p50/p95 was 2.501/2.747 seconds (19 samples), J20 took 24.070286 seconds, and the 512-word journal took 20.934335 seconds. All 30 summaries used generation. All 25 original policy-4 development cases retain their risk labels. A separate seen J12 style follow-up returns "The writer reports no sadness today. The writer feels great and everything is going well." through the existing one-repair path in 3.686 seconds; the initial abstract response is preserved.
- The [current targeted PDF regression](../reports/POLICY4_CONDITION_REGRESSION.md) rechecks R12/R14 and previously omitted cap/expiry/approval conditions. This is a separate follow-up, not a new 76-case pass count.
- All seven targeted PDF checks matched predicted status/fact/page checks, following fresh HTTP 201 READY in 1.329 seconds. R14 abstained in 0.062 seconds without citations; R12 retained the sick-leave certificate condition and named the uncovered stock-option question.
- Generator comparison, before policy version 3: 4B validated 49/50 development journals and returned 30/30 document-question responses; 1.5B validated 41/50 journals and returned 21/30 question responses. Failures are retained.
- Frozen 100-case English evaluation, measured before policy version 3: 96 validated responses; label agreement including service errors was 95/100 sentiment, 93/100 emotion and 81/100 screening priority. Successful-request p50/p95 was 11.71/18.39 seconds on the tested laptop. These numbers do not measure the current corrections.
- Fine-tuned sentiment baseline: RoBERTa 99/100 matching annotations, versus NLI sentiment 97/100. Counts, macro metrics, confusion matrices and uncertainty are published.
- New ten-page PDF: synchronous READY in 0.865 seconds. Expected-page retrieval hit 27/27 answerable/partial cases. Automated end-to-end matches were 27/30; one is a matcher false negative and two are conservative full abstentions instead of partial answers.
- Desktop/mobile real workflows, nonblank PDF canvas, source-page navigation, four-width responsive checks, offline API-process smoke and restored-index/keyed-isolation rehearsal passed.
- Linux image build, non-root fail-closed startup and [full real-model CPU Docker integration](https://github.com/tusharg007/mymanah-journal-intelligence/actions/runs/37673144901) passed. The fresh CPU runner observed a 19.69-second journal and a 0.898-second two-page READY upload before policy 3; these are smoke observations, not current latency percentiles. CPU-only machines can be substantially slower than the tested GPU laptop, and long journals can exhaust the 60-second deadline. Linux GPU execution is not yet verified.

## Assumptions and Limitations

English journals and text-based English PDFs are the supported release. Hindi/Hinglish is an unimplemented optional extension; ambiguous Latin-script language detection is imperfect. Scanned/encrypted/corrupt or unusable PDFs fail explicitly; there is no OCR or reliable table-layout interpretation. Questions are standalone and use one authorized document, without external facts or chat memory.

Screening labels are an assignment policy, not clinical risk prediction. MEDIUM recall is weak (13/28 in the held-out fixtures); two correctly classified HIGH examples do not establish safety. Emotion can be wrong even at high classification scores. Confidence and mood are uncalibrated heuristics, not validated probabilities or clinical scales. Some valid summaries are conservatively rejected, and NLI verification is fallible.

The original prolonged-distress miss, positive/neutral inconsistency and three
journal service errors were corrected on development inputs. The original unseen U6/U10
screening misses remain published; their follow-up correction uses seen inputs and
does not establish generalization. U6's anger-versus-sad emotion error remains.
Other hopelessness phrasings can still be missed. Figurative J14 still returns sad
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
