# Submission Notes

Repository: https://github.com/tusharg007/mymanah-journal-intelligence

Actual application recordings: [Desktop walkthrough](walkthrough-desktop.mp4) and [Mobile walkthrough](walkthrough-mobile.mp4). These show real local model requests, journal analysis, synchronous PDF readiness, immediate grounded questions, source citations/rendering and an unsupported question. They are screen recordings, not canned-output previews; inference waiting time is retained. No public deployment is claimed.

## Approach

I separated model adapters, text policy, journal processing, document ingestion/recovery, retrieval, persistence, admission control and HTTP contracts. FastAPI serves a React/TypeScript interface. Journal classification runs on CPU concurrently with local quantized generation. RoBERTa supplies English sentiment; an NLI adapter supplies the seven-label emotion taxonomy, contextual distress signals and claim-support verification. Standard fine-tuned emotion label sets do not directly cover anxiety and stress. The selected 4B generator is a revision/hash-pinned Hugging Face GGUF served by local Ollama, not a hosted LLM API.

Uploaded PDFs are bounded and parsed in an isolated subprocess, chunked by page/token budget, embedded with E5 and indexed in a generation-specific Chroma collection. SQLite owns document state, quotas and canonical citation text. Dense retrieval and BM25+ are fused, then structured claims must pass exact-quote, number and original-context support checks. A document becomes READY only after indexing/probing, so reviewers can ask immediately. Failures do not produce fabricated summaries or misleading abstention responses.

Loopback review is credential-free by default. API keys are opt-in, remote binding requires keys, and document/source access is principal-scoped. Upload cancellation, interrupted-ingestion recovery, deletion, finite deadlines, bounded concurrency and quiesced backup/restore are tested. Runtime uses local artifacts with offline Hugging Face settings and disabled Ollama cloud features. Dependency/model/frontend locks, reproducible bootstrap scripts and measured reports are included.

## Evidence

- Windows deterministic suite: 65 passing tests; the prior 63-test suite also passed on Linux, with final Linux checks run on each push. Native and Linux CPU Docker real-model contract/PDF suites: two passing tests each.
- Generator comparison: 4B validated 49/50 development journals and returned 30/30 document-question responses; 1.5B validated 41/50 journals and returned 21/30 question responses. Failures are retained.
- Frozen 100-case English evaluation: 96 validated responses; label agreement including service errors is 95/100 sentiment, 93/100 emotion and 81/100 screening priority. Successful-request p50/p95 is 11.71/18.39 seconds on the tested laptop.
- Fine-tuned sentiment baseline: RoBERTa 99/100 matching annotations, versus NLI sentiment 97/100. Counts, macro metrics, confusion matrices and uncertainty are published.
- New ten-page PDF: synchronous READY in 0.865 seconds. Expected-page retrieval hit 27/27 answerable/partial cases. Automated end-to-end matches were 27/30; one is a matcher false negative and two are conservative full abstentions instead of partial answers.
- Desktop/mobile real workflows, nonblank PDF canvas, source-page navigation, four-width responsive checks, offline API-process smoke and restored-index/keyed-isolation rehearsal passed.
- Linux image build, non-root fail-closed startup and [full real-model CPU Docker integration](https://github.com/tusharg007/mymanah-journal-intelligence/actions/runs/37673144901) passed. The fresh CPU runner observed a 19.69-second journal and a 0.898-second two-page READY upload; these are smoke observations, not latency percentiles. Linux GPU execution is not yet verified.

## Assumptions and Limitations

English journals and text-based English PDFs are the supported release. Hindi/Hinglish is an unimplemented optional extension; ambiguous Latin-script language detection is imperfect. Scanned/encrypted/corrupt or unusable PDFs fail explicitly; there is no OCR or reliable table-layout interpretation. Questions are standalone and use one authorized document, without external facts or chat memory.

Screening labels are an assignment policy, not clinical risk prediction. MEDIUM recall is weak (13/28 in the held-out fixtures); two correctly classified HIGH examples do not establish safety. Emotion can be wrong even at high classification scores. Confidence and mood are uncalibrated heuristics, not validated probabilities or clinical scales. Some valid summaries are conservatively rejected, and NLI verification is fallible.

Evaluation cases have provisional engineering annotations and simple synthetic language, not independent clinician/human validation. No zero-bug, zero-hallucination, clinical-readiness or horizontal-scalability guarantee is made. The implementation uses one application process with embedded storage and bounded local inference, not a distributed service.

The security report retains scoped Chroma server advisories and the audit's CPU-Torch coverage gap. The embedded profile avoids the affected HTTP/configuration surfaces; this is not a claim of zero vulnerabilities. Public hosting would additionally require TLS, reviewed proxy controls, secret management and operational hardening.
