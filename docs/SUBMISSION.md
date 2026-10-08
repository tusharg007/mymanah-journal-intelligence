# Submission

| Status | Final Release |
| --- | --- |
| Policy | **journal-policy-5**, inference code frozen after W1-W8 |
| Checks | **129 deterministic tests + 2 actual-model smoke tests**; pinned Ubuntu 24.04/Node-24 [CI passed](https://github.com/tusharg007/mymanah-journal-intelligence/actions/runs/37857697838) |
| Fresh assessment | W1-W8 run once, no tuning: **8 valid / 6 matching supplied expectations** |
| Evidence scope | 30 seen development responses; original 100-case held-out results predate policy 3 and do not measure this release |
| Known misses | **W2: MEDIUM, W3: LOW instead of HIGH**; U6/J14 emotion errors; imperfect summaries and uncalibrated scores |

[Repository](https://github.com/tusharg007/mymanah-journal-intelligence) |
[Policy-5 overview](walkthrough-short.mp4) |
[Full recordings and timestamps](WALKTHROUGH.md)

## Approach

I built a FastAPI/React application with separate model adapters, journal policy,
document ingestion, retrieval, persistence and HTTP boundaries. Only pinned local
Hugging Face models run: RoBERTa for English sentiment, DeBERTa NLI for the seven
emotion labels and support checks, E5 for retrieval, and Qwen3 4B GGUF through
Ollama. Standard emotion taxonomies do not directly cover anxiety and stress.
There are no hosted LLM APIs.

Journal classification runs on CPU concurrently with real local summary generation.
The LLM produces third-person sentences with exact source quotes; source, number
and NLI checks verify them. One repair is allowed, then only a verified extractive
fallback within the deadline. Confidence is the selected emotion score, or the
winning sentiment score for a positive/neutral consistency override, capped at
0.99 for presentation only. It does not validate crisis priority or summary facts.

PDF upload is synchronous and returns READY after bounded extraction, page-aware
chunking, indexing and a retrieval probe. Dense/BM25 retrieval feeds verified
claims with verbatim, page-level citations. Absent topics abstain before generation;
mixed supported/unsupported questions return PARTIAL with the missing topic named.
SQLite/Chroma storage, isolated PDF parsing, principal-scoped access, bounded
concurrency, finite deadlines, recovery and deletion support the implementation.

## Review and Run

Use the [README's platform setup](../README.md). After Windows dependencies are
installed and Ollama is running:

```powershell
.venv\Scripts\python.exe scripts\bootstrap.py --generator qwen4b
.venv\Scripts\python.exe scripts\doctor.py
.venv\Scripts\python.exe scripts\start.py
```

Open http://127.0.0.1:8000. Bootstrap downloads pinned artifacts; inference then
runs locally. Loopback review needs no API key by default; remote binding requires
keys. Short-entry observations are from the tested GPU laptop, not CPU-only
performance guarantees. CPU-only long journals can exhaust the 60-second deadline.

## Evidence and Limits

The [evidence ledger](EVIDENCE.md) separates historical, seen and fresh results.
The [fresh W1-W8 report](../reports/UNSEEN_HOPELESSNESS_8.md) includes every input
and full response. W4/W5/W7 produced no false HIGH, but W2/W3 missed the predicted
HIGH. Those misses remain unchanged, not patched away. W6/W7 used verified
extractive summaries; W5 inferred unsupported gender. U6 still selects anger for
a hopeless entry. High emotion confidence can accompany an incorrect risk label.

English journals and text-based English PDFs are supported. Hindi/Hinglish and OCR
are not implemented; scanned/encrypted/corrupt PDFs fail explicitly. Language
detection, NLI verification, summaries, retrieval and qualifying conditions remain
fallible. Screening is an assignment policy, **not reliable clinical crisis detection**.
Confidence and mood are uncalibrated heuristics. AI-assisted predicted expectations
are not independent clinical ground truth. There is no zero-bug, zero-hallucination
or clinical-readiness claim.
