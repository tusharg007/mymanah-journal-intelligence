# MyManah Journal Intelligence

Local Hugging Face inference for journal analysis and evidence-grounded PDF questions. Python/FastAPI, React/TypeScript, SQLite, Chroma, hybrid dense/BM25 retrieval and local Ollama. No hosted LLM API clients, web retrieval, canned inference responses or runtime model downloads.

## Implementation Status

Both workflows use actual downloaded models, and the 4B generator is selected from two measured candidates. Development evaluation includes 50 journals and 30 questions against a newly uploaded ten-page PDF. Raw results and failures are retained in `reports/`. Verification status is tracked below; an unexecuted profile is not advertised as tested. The approved `IMPLEMENTATION_PLAN.md` is unchanged and excluded from public source control along with the supplied assessment PDF.

## Windows Setup

Python 3.11, Node 22+, about 12-15 GB free disk, and Ollama 0.40.0. This machine uses CPU classification/embeddings and NVIDIA GPU offload for generation. Use a project-local environment; do not install into an unrelated project's environment.

```powershell
uv venv .venv --python 3.11
uv pip install --python .venv\Scripts\python.exe --require-hashes -r requirements.windows.lock
uv pip install --python .venv\Scripts\python.exe --no-deps -e .
Set-Location web
npm.cmd ci --ignore-scripts
npm.cmd run build
Set-Location ..
```

The official portable Windows runtime can reside at `artifacts/ollama/ollama.exe`. Put that directory on the current session's PATH, or use an official installed Ollama executable. Runtime release: [Ollama 0.40.0](https://github.com/ollama/ollama/releases/tag/v0.40.0). Windows AMD64 ZIP SHA-256: `3623e256762ca89bd6fa99b0cc4106401919ce9df926411673e632e3ea287bb5`.

```powershell
$env:PATH = "$PWD\artifacts\ollama;$env:PATH"
$env:OLLAMA_MODELS = "$PWD\models\ollama"
$env:OLLAMA_HOST = '127.0.0.1:11434'
$env:OLLAMA_NUM_PARALLEL = '1'
$env:OLLAMA_MAX_LOADED_MODELS = '1'
$env:OLLAMA_NO_CLOUD = '1'
$env:LLAMA_ARG_FIT_TARGET = '256'
ollama serve
```

In a second terminal, from this project, run bootstrap once. Downloads require internet; application inference does not.

```powershell
$env:PATH = "$PWD\artifacts\ollama;$env:PATH"
$env:OLLAMA_MODELS = "$PWD\models\ollama"
.venv\Scripts\python.exe scripts\bootstrap.py --all-generators
.venv\Scripts\python.exe scripts\doctor.py
.venv\Scripts\python.exe scripts\start.py
```

Alternatively `scripts/start.ps1` starts the local runtime if necessary. Open [the local application](http://127.0.0.1:8000) and [API documentation](http://127.0.0.1:8000/docs). Readiness remains 503 until checksum verification, CPU warmup, GGUF identity validation and generator loading succeed. Health never pulls models.

## Exact Journal Contract

Default `API_KEYS` is **unset**, allowing loopback requests without credentials:

```bash
curl http://127.0.0.1:8000/analyze-journal \
  -H 'Content-Type: application/json' \
  -d '{"text":"I finished my project today and feel pleased with my progress."}'
```

PowerShell:

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8000/analyze-journal -Method Post -ContentType application/json -Body '{"text":"I finished my project today and feel pleased with my progress."}'
```

The successful response has exactly `sentiment`, `emotion`, `moodScore`, `summary`, `crisisRisk`, `confidence`. Sentiment/emotion are lowercase, crisis priority uppercase, mood an integer 1-10, summary two or three sentences. Extra request fields are rejected. Bounds: 32 KiB body, 8,000 characters, 2,000 generator tokens and at most 24 classifier windows, without truncation.

### Optional Authentication

Generate a URL-safe key from 32 random bytes and set the variable before starting the API:

```powershell
$key = & .venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(32))"
$env:API_KEYS = "reviewer:$key"
```

Restart the API. Clients include `Authorization: Bearer <key>`. Multiple principals: `API_KEYS=alice:<key1>,bob:<key2>`. An empty/malformed variable fails startup instead of silently opening access. Remove the variable and restart to restore loopback open mode. Never expose open mode through a proxy/tunnel. Non-loopback HOST requires keys; public access additionally requires TLS and reviewed proxy controls. Keys are held in UI memory only; refresh/logout clears them.

## PDF Upload and Questions

Text-based English PDFs: maximum 10 MiB, 100 pages, 500,000 extracted characters and 5,000 chunks. Scanned-only, encrypted, corrupt and unusable-text PDFs fail explicitly. No OCR or layout-aware table interpretation is claimed.

```bash
curl -F 'file=@policy.pdf' http://127.0.0.1:8000/documents
```

A new upload returns **201**, `status: READY` and `document.id` after extraction, embedding, index verification and atomic publication. Identical READY uploads return 200. Ask immediately; no job polling is necessary:

```bash
curl http://127.0.0.1:8000/documents/DOCUMENT_ID/questions \
  -H 'Content-Type: application/json' -d '{"question":"What is the annual leave allowance?"}'
```

Question response: `status` (`ANSWERED`, `PARTIAL`, `INSUFFICIENT_EVIDENCE`), `answer`, and citations containing authorized document ID, filename, page, chunk ID and an exact quote. Unavailable generation returns an error, not an evidence-abstention response. Questions are standalone; there is no conversation memory. List: `GET /documents`; metadata: `GET /documents/{id}`; authenticated source preview: `GET /documents/{id}/file`; delete: `DELETE /documents/{id}`.

## Models and Decisions

Exact repositories, revisions, weight hashes, tokenizer revisions and licenses are in `model_manifest.json`. Bootstrap verifies upstream Git/LFS identities, then writes a local artifact checksum lock. Startup checks local bytes and never trusts a mutable repository head.

| Task | Model | License |
| --- | --- | --- |
| English sentiment | CardiffNLP Twitter RoBERTa sentiment latest, pinned commit | CC BY 4.0 |
| Seven emotions, crisis evidence, support verification | MoritzLaurer DeBERTa-v3-base zeroshot v2.0-c | MIT |
| Embeddings | intfloat multilingual-e5-small, query/passage prefixes | MIT |
| Generator candidate A | Unsloth Qwen3-4B-Instruct-2507 Q4_K_M GGUF | Apache 2.0 |
| Generator candidate B | Official Qwen2.5-1.5B-Instruct Q4_K_M GGUF | Apache 2.0 |

NLI is used for seven emotions because standard fine-tuned emotion taxonomies omit anxiety/stress or otherwise mismatch the requested labels. Fear is not arbitrarily relabeled anxiety. The real fine-tuned English benchmark compares RoBERTa sentiment against NLI on identical three-label cases; it does not pretend incompatible emotion label sets constitute a seven-class comparison.

The selected default is `GENERATOR=qwen4b` for both tasks. `qwen1b` remains available as the measured, rejected smaller candidate, not an automatic fallback. Pre-quantized weights are downloaded and verified, not self-converted. Hindi/Hinglish remains an unimplemented optional extension: this release supports English only. Unsupported non-Latin input receives a controlled 422; Latin-script detection cannot reliably distinguish all Hinglish.

On this 16 GB RAM / RTX 3050 Laptop 4 GB machine, reducing Ollama's fitting reserve to 256 MiB enabled full 37-layer GPU offload. This is a measured laptop setting, not a recommendation to override GPU memory limits on every host. Initial allocation failure and subsequent measurements remain in `reports/generator-comparison.json`. Windows may expand its pagefile under memory pressure; leave adequate system-drive headroom.

## Architecture and Safety

- Journal: validate -> CPU RoBERTa/NLI classification in parallel with Ollama summary -> source/numeric/NLI support checks -> versioned crisis/mood rules -> exact response.
- PDF: bounded subprocess extraction -> per-page tokenizer chunks -> canonical SQLite chunks -> explicit E5 vectors in a document-generation-specific Chroma collection -> retrieval probe -> READY publication.
- RAG: scoped dense and BM25+ retrieval -> reciprocal rank fusion -> evidence budget -> structured claims -> quote/numeric/NLI checks -> server-resolved citations. No outside facts or unverified streaming.
- One API worker, one active interactive request, two waiting requests and one ingestion lane. Model adapters share a bounded CPU lock; timed-out model work retains admission until it actually completes.
- Upload timeout/cancellation invalidates its publication token. A duplicate waiter's timeout does not cancel the owner. Restart cleans unpublished indexes and interrupted uploads. Deletion makes a document unavailable before cleanup.
- Journal contents are transient. PDFs persist until deletion. No raw journal, question, PDF text, prompts, generated answers or keys in application logs. Data/model directories and secrets are excluded from Git.

`confidence=min(selected sentiment score, selected emotion score)` is an uncalibrated classification heuristic, **not** a probability all response fields are correct. Mood uses the versioned formula in `mymanah/policy.py`, with approximate distress adjustment, not a clinical scale. LOW/MEDIUM/HIGH are assignment screening priorities, not clinical risk prediction. The broad sample-compatible HIGH policy includes prolonged distress, impairment and giving-up language. No automatic clinical escalation or notification occurs.

Starting hard deadlines: short journal 30 seconds, larger journal 60, question 45, synchronous upload 60. The warm short-entry **target** is 10-15 seconds, including verification; actual measurements are required. Each ordinary window initially costs 14 NLI pairs, plus summary verification, not a single classification operation.

## Verification and Evaluation

```powershell
.venv\Scripts\python.exe -m ruff check mymanah scripts tests evals
.venv\Scripts\python.exe -m pytest -m 'not live' -q
.venv\Scripts\python.exe -m pytest -m live -q
.venv\Scripts\python.exe -m evals.benchmark --generator qwen4b --output reports\development-qwen4b.json --rag-output reports\rag-qwen4b.json
.venv\Scripts\python.exe -m evals.benchmark --generator qwen1b --output reports\development-qwen1b.json --rag-output reports\rag-qwen1b.json
.venv\Scripts\python.exe -m evals.benchmark --generator qwen4b --cases evals\heldout.json --output reports\heldout-qwen4b.json
.venv\Scripts\python.exe -m scripts.offline_check
```

Unit/API/failure tests may use explicitly test-only injected adapters; production has no fake inference mode. PDF transaction tests use real pypdf/SQLite/Chroma. Live tests use actual downloaded classifiers/embeddings/generation and upload a new PDF immediately before asking questions. Benchmark reports include case counts, failures, confusion matrices and rough p50/p95. Development results are not held-out performance claims. Small curated evaluations do not establish clinical or deployment validity.

Stop the API before running model benchmarks or the offline check on a memory-constrained laptop; otherwise two classifier registries consume RAM and distort timings. Leave local Ollama running. To repeat browser verification, install Playwright in the tooling environment, then run `node web/live-qa.cjs` against the running API; set `RECORD_VIDEO=1` to record the actual workflows.

### Measured Development Results

| Measure | Qwen 4B (selected) | Qwen 1.5B |
| --- | --- | --- |
| Validated journal responses | 49 / 50 | 41 / 50 |
| Warm successful journal p50 / p95 | 11.23 / 15.56 s | 2.25 / 2.54 s |
| Document-question responses | 30 / 30 | 21 / 30 |
| Automated question status/text matches | 27 / 30 | 19 / 30 |

These runs were not a controlled speed comparison: dependency versions and available RAM differed. Both used the same synthetic cases and frozen corrected prompts. Rejected outputs are errors, not fabricated successful summaries. The 4B ten-page upload took 0.865 seconds and returned READY before the immediate question. Retrieval included the expected page on all 27 answerable/partial cases. One of the three automated 4B mismatches is a singular/plural matcher false negative ("line manager" versus "Line managers"); two are conservative full abstentions where partial answers were expected. Raw cases are not relabeled to improve scores.

Known journal errors include a positive completion entry classified as neutral emotion, and six of twelve expected MEDIUM cases classified LOW on development data. The three development HIGH examples were correctly classified, which is far too little evidence for clinical reliability. Exact class counts, service errors, confusion matrices and Wilson intervals are in the reports. Summary/claim NLI validation can both reject valid paraphrases and accept mistakes; it is not a proof of factual correctness. See `reports/CORRECTIONS.md`, `reports/SECURITY.md`, and `evals/README.md`.

## Backup and Restore

Stop the API before either command. Keep archives outside `data/`, and restore only to an empty destination:

```powershell
.venv\Scripts\python.exe -m scripts.backup backup backups\journal-intelligence.zip
.venv\Scripts\python.exe -m scripts.backup restore backups\journal-intelligence.zip --destination restored-data
$env:DATA_DIR = "$PWD\restored-data"
.venv\Scripts\python.exe scripts\start.py
```

After readiness, ask a real question against a restored document to verify its persisted index, not only the SQLite integrity check. Backup archives contain uploaded PDF text and must be treated as private. Journals are not persisted. Unsetting `DATA_DIR` restores the normal data location on the next restart.

## Docker and GPU Evaluation

Docker uses a CPU-classifier image and a local Ollama container sharing a network namespace. Models/data persist on mounted local volumes; API keys are mandatory for the Docker-published binding. Set `API_KEYS`, then `docker compose up --build`. Import the verified mounted GGUF explicitly using a container-local Modelfile (`FROM /models/qwen4b/Qwen3-4B-Instruct-2507-Q4_K_M.gguf`) and `docker compose exec ollama ollama create mymanah-qwen4b -f /models/qwen4b/Modelfile.container`. Do not reuse a Windows absolute Modelfile path inside Linux.

For NVIDIA Linux, use `docker compose -f compose.yaml -f compose.gpu.yaml up --build` only with a verified NVIDIA container runtime. GPU nodes/notebooks run the same package and evaluation commands, not a separate notebook implementation or hosted inference provider. Docker/GPU profiles require execution verification before being marked tested.

## Verification Status

Native models, candidate comparisons, synchronous ingestion and deterministic tests have been executed. Held-out evaluation, fresh live/browser verification, offline rehearsal, persisted-index restore and walkthrough recording are being completed. Docker execution is currently blocked by insufficient C: drive space; the CPU and Linux GPU profiles are present but not yet execution-verified. No hiring-team email has been sent. Dependency audit limitations are explicitly retained rather than claiming a zero-vulnerability result.

## Attribution

CardiffNLP's English sentiment model is based on the Twitter/XLM-T research lineage; retain its [model card and attribution](https://huggingface.co/cardiffnlp/twitter-roberta-base-sentiment-latest). Additional upstream cards: [DeBERTa NLI](https://huggingface.co/MoritzLaurer/deberta-v3-base-zeroshot-v2.0-c), [E5](https://huggingface.co/intfloat/multilingual-e5-small), [Qwen 4B GGUF](https://huggingface.co/unsloth/Qwen3-4B-Instruct-2507-GGUF), [Qwen 1.5B GGUF](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF). Upstream model licenses are separate from application code.
