# Submission Notes

Repository: https://github.com/tusharg007/mymanah-journal-intelligence

Actual application recordings: [2:02 overview](walkthrough-short.mp4), [6:08 desktop walkthrough](walkthrough-desktop.mp4) and [3:42 mobile walkthrough](walkthrough-mobile.mp4), opening with corrected J1 (HIGH). The recordings use diverse inputs from an AI-assisted self-test pack with predicted expectations, supplied by the candidate. Results are held visibly for reading with permanently embedded captions. [Compiled inputs and actual results](VIDEO_TEST_RESULTS.md), timestamps and source PDF accompany the recordings.

## Approach

I separated model adapters, text policy, journal processing, document ingestion/recovery, retrieval, persistence, admission control and HTTP contracts. FastAPI serves a React/TypeScript interface. Journal classification runs on CPU concurrently with local quantized generation. RoBERTa supplies English sentiment; an NLI adapter supplies the seven-label emotion taxonomy, contextual distress signals and claim-support verification. Standard fine-tuned emotion label sets do not directly cover anxiety and stress. The selected 4B generator is a revision/hash-pinned Hugging Face GGUF served by local Ollama, not a hosted LLM API.

Uploaded PDFs are bounded and parsed in an isolated subprocess, chunked by page/token budget, embedded with E5 and indexed in a generation-specific Chroma collection. SQLite owns document state, quotas and canonical citation text. Dense retrieval and BM25+ are fused, then structured claims must pass exact-quote, number and original-context support checks. A document becomes READY only after indexing/probing, so reviewers can ask immediately. Failures do not produce fabricated summaries or misleading abstention responses.

Loopback review is credential-free by default. API keys are opt-in, remote binding requires keys, and document/source access is principal-scoped. Upload cancellation, interrupted-ingestion recovery, deletion, finite deadlines, bounded concurrency and quiesced backup/restore are tested. Runtime uses local artifacts with offline Hugging Face settings and disabled Ollama cloud features. Dependency/model/frontend locks, reproducible bootstrap scripts and measured reports are included.

## Evidence

- Windows deterministic suite: 96 passing tests, with Linux checks run on each push. Both current native real-model contract/fresh-PDF tests pass. The prior Linux CPU Docker real-model suite also passed two tests; that Docker run predates policy version 3.
- AI-assisted self-test pack with predicted expectations: all 76 cases were exercised before policy version 3. The original 20 journals produced 17 responses and three service errors. After correction, all 20 produced valid responses: 19 agreed with predicted sentiment/emotion/risk; J14 retained an emotion disagreement. J1 and its three development paraphrases returned HIGH; J5/J6/J7/J14 did not. J2/J12 returned happy and J15/J16 succeeded. J20 and a natural 512-word journal each returned in 13.406 seconds in the final regression. Mood guesses are separate from label comparisons. These are development observations, not independent ground truth. [Complete results](../reports/REVIEWER_TEST_PACK.md) preserve original and post-change evidence.
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
journal service errors were corrected on the development self-test inputs. This
does not establish generalization: figurative J14 still returns sad rather than
the predicted neutral/anger, and the one-fact injection case J17 repeats its literal
risk statement to meet the two-sentence contract. Long-entry emotion is derived
from verified summary excerpts and can miss feelings elsewhere in the entry.
Qualifying conditions and residual document-answer disagreements are reported
separately in the targeted policy-condition regression.

R2/R8/R18 now include cap/expiry/approval conditions in the answer text with exact
citations. R19 and R17 also pass the targeted checks. R12's mixed sick-leave/stock-option
question and R14's unsupported paternity question still return `ANSWER_UNSUPPORTED`,
not the expected partial answer or abstention. These controlled errors are unresolved.

Evaluation cases have provisional engineering annotations and simple synthetic language, not independent clinician/human validation. No zero-bug, zero-hallucination, clinical-readiness or horizontal-scalability guarantee is made. The implementation uses one application process with embedded storage and bounded local inference, not a distributed service.

The security report retains scoped Chroma server advisories and the audit's CPU-Torch coverage gap. The embedded profile avoids the affected HTTP/configuration surfaces; this is not a claim of zero vulnerabilities. Public hosting would additionally require TLS, reviewed proxy controls, secret management and operational hardening.
