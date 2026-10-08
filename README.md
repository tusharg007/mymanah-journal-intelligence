# MyManah Journal Intelligence

Local Hugging Face inference for journal analysis and evidence-grounded PDF questions. Python/FastAPI, React/TypeScript, SQLite, Chroma, hybrid dense/BM25 retrieval and local Ollama. No hosted LLM API clients, web retrieval, canned inference responses or runtime model downloads.

## Implementation Status

Both workflows use actual downloaded models, and the 4B generator is selected from two measured candidates. Development evaluation includes 50 journals and 30 questions against a newly uploaded ten-page PDF, followed by 100 frozen held-out journals. Native inference, full Linux CPU Docker inference, offline operation, browser workflows, authentication and persisted-index restoration have been executed. Raw results and failures are retained in `reports/`; an unexecuted profile is not advertised as tested. The approved `IMPLEMENTATION_PLAN.md` is unchanged and excluded from public source control along with the supplied assessment PDF. Submission notes and actual walkthrough recordings are in `docs/`.

## Windows Setup

Python 3.11, Node 22.13+, about 12-15 GB free project disk plus adequate system-drive/pagefile headroom, and Ollama 0.40.0. This machine uses CPU classification/embeddings and NVIDIA GPU offload for generation. Use a project-local environment; do not install into an unrelated project's environment.

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

To obtain the portable runtime explicitly:

```powershell
.venv\Scripts\python.exe scripts\download_runtime.py
Expand-Archive -LiteralPath artifacts\ollama-windows-amd64.zip -DestinationPath artifacts\ollama
```

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
- RAG: scoped dense and BM25+ retrieval -> reciprocal rank fusion -> evidence budget -> topic-absence guard -> supported question parts -> structured claims -> quote/numeric/NLI checks -> server-resolved citations. Missing topics abstain before generation; supported parts return PARTIAL when another part is uncovered.
- After claim verification, a cited policy sentence containing approval/carry-over/other explicit qualifying language is preserved in the answer rather than shortened. This retains conditions present in that quote, not conditions elsewhere in the document.
- One API worker, one active interactive request, two waiting requests and one ingestion lane. Each principal has 10 interactive requests and 2 uploads per minute. Model adapters share a bounded CPU lock; timed-out model work retains admission until it actually completes.
- Upload timeout/cancellation invalidates its publication token. A duplicate waiter's timeout does not cancel the owner. Restart cleans unpublished indexes and interrupted uploads. Deletion makes a document unavailable before cleanup.
- Journal contents are transient. PDFs persist until deletion. No raw journal, question, PDF text, prompts, generated answers or keys in application logs. Data/model directories and secrets are excluded from Git.

`confidence` reports the normalized score of the selected emotion. When winning positive sentiment resolves a neutral-emotion prediction to happy, it reports that sentiment score instead of the discarded happy NLI score. Policy 5 caps either score at 0.99 for presentation; this is not calibration. It does not score sentiment, summary and risk jointly. Supported hopelessness (NLI at least 0.65) plus overwhelm (at least 0.50), persistence or impairment (either at least 0.65) gives HIGH, alongside the existing lexical giving-up plus supported-distress and explicit-danger rules. Mood reserves 1-2 for HIGH entries and uses a gentler mapping for ordinary negative or mixed feelings. LOW/MEDIUM/HIGH are assignment screening priorities, not clinical risk prediction.

Starting hard deadlines: short journal 30 seconds, larger journal 60, question 45, synchronous upload 60. Queue time counts toward the deadline; expired waiters do not start inference. Classifier deadlines are checked between length-bounded batches, not by interrupting an active Torch forward pass. The warm short-entry **target** is 10-15 seconds, including verification. Long journals use seven risk/distress pairs per 160-token window; emotion is scored from the exact excerpts supporting the verified summary, while sentiment and risk cover the full entry. CPU NLI explicitly uses float32: retaining the checkpoint's float16 dtype was slow on the tested CPU. A dynamic-int8 experiment was rejected after real support checks failed. Downloaded weights and pins are unchanged.

Every journal starts a real Ollama/Qwen3 4B generation call concurrently with CPU classification. The LLM produces third-person summary sentences and selects exact source quotes through a constrained JSON schema. Source, number, instruction, causal and NLI checks run before return; one repair is allowed. After two generation/verification failures, bounded verbatim extracts may be used only if they also pass evidence checks and the deadline has not expired. HIGH-risk summaries are no longer forcibly replaced with source quotes. A one-fact summary appends `No further details are given.` rather than repeating the fact. Logs retain generation token counts, elapsed model time, summary path and confidence source without prompts or personal text.

## Verification and Evaluation

The [76-case report](reports/REVIEWER_TEST_PACK.md) covers an AI-assisted self-test
pack with predicted expectations supplied by the candidate. Its predictions are
development aids, not ground truth. The original video inputs exposed J1's risk
miss and neutral emotion for J2/J12; provisional mood ranges are a separate
calibration concern. Original responses and service errors remain available.

Historical policy version 3's separate [journal regression](reports/JOURNAL_POLICY3_REGRESSION.md)
returned valid responses for all 20 pack inputs, with 19 agreeing with predicted
sentiment/emotion/risk and one emotion disagreement (figurative J14: sad).
J1 and its three development paraphrases returned HIGH; J5/J6/J7/J14 did not.
J2/J12 returned happy, J15/J16 succeeded, and J20 returned in 13.406 seconds.
A separate natural 512-word journal also returned in 13.406 seconds. Short pack
entries in that run took 1.703-3.828 seconds. These are small warm local observations,
not production latency percentiles. The unchanged held-out measurements below
precede this revision. Long-entry emotion can omit feelings outside the selected
summary excerpts; confidence and mood remain uncalibrated.

Historical policy-4 [development results](reports/JOURNAL_POLICY4_REGRESSION.md)
returned 20/20 valid pack responses, with 19 agreeing on predicted labels (J14
remains the emotion disagreement). J2/J12 confidence is 0.9773/0.9736. All 25
development summaries followed the generated path, with output-token counts
retained. Short pack entries took 2.033-2.706 seconds, with measured p50/p95 of
2.467/2.706 seconds (19 samples). Independent long-entry measurements were J20
23.807809 seconds and the 512-word entry 20.539648 seconds. The full long-entry
input and generated summary are published in that report.

The ten AI-assisted [original unseen entries](reports/UNSEEN_REVIEW_10.md) were run once
without retries or tuning at that stage, before the requested policy-5 follow-up: 10 valid responses, eight matching every
specified label. U6 returned anger/MEDIUM instead of sad/HIGH; U10 returned MEDIUM
instead of HIGH while excluding its injected instruction. U7/U8/U9 returned
LOW/LOW/MEDIUM. Warm short-entry p50/p95 was 1.829/2.241 seconds (10 samples).
These are small local observations, not production latency guarantees or
independent clinical validation. High emotion scores can accompany incorrect
labels and do not validate the risk policy.

The [policy-5 seen regression](reports/JOURNAL_POLICY5_REGRESSION.md) separately
rechecks U6/U10 and the U7-U9 controls after diagnosing all seven safety scores.
They are now seen development inputs, not fresh generalization evidence.
The original unseen and frozen held-out reports remain unchanged. All timing
observations above are from the tested GPU laptop; CPU-only performance can be
slower, and long journals can exhaust the 60-second deadline. Full desktop/mobile
videos preserve policy 4; the re-recorded overview measures frozen policy 5.

The fresh [W1-W8 assessment](reports/UNSEEN_HOPELESSNESS_8.md) was run once with
no tuning afterward: eight valid responses, six matching supplied expectations.
W2 returned MEDIUM and W3 LOW instead of HIGH; W4/W5/W7 produced no false HIGH.
Inference code is frozen, and these screening misses remain disclosed. The
[evidence ledger](docs/EVIDENCE.md) separates historical, seen and fresh results.

All seven [current targeted document checks](reports/POLICY4_CONDITION_REGRESSION.md)
matched their predicted status/fact/page checks after a fresh 201 READY upload in
1.329 seconds. R12 returns PARTIAL with verified sick leave and its certificate
condition; R14 abstains without citations in 0.062 seconds before generation.
The lexical guard checks retrieved evidence; synonyms and retrieval omissions
remain limitations.

```powershell
.venv\Scripts\python.exe -m ruff check mymanah scripts tests evals
.venv\Scripts\python.exe -m pytest -m 'not live' -q
.venv\Scripts\python.exe -m pytest -m live -q
.venv\Scripts\python.exe -m scripts.journal_regression --seen-cases U6 U7 U8 U9 U10 --output reports/local-journal-recheck.json
.venv\Scripts\python.exe -m scripts.policy_condition_regression --output reports/local-document-recheck.json
.venv\Scripts\python.exe -m scripts.export_policy5_results
.venv\Scripts\python.exe -m scripts.offline_check
```

Unit/API/failure tests may use explicitly test-only injected adapters; production has no fake inference mode. PDF transaction tests use real pypdf/SQLite/Chroma. Live tests use actual downloaded classifiers/embeddings/generation and upload a new PDF immediately before asking questions. Benchmark reports include case counts, failures, confusion matrices and rough p50/p95. Development results are not held-out performance claims. Small curated evaluations do not establish clinical or deployment validity.

The original held-out report is retained, not overwritten by these commands.
Any later run against `evals/heldout.json` must use a separate regression filename
and must not be described as an untouched held-out evaluation of the tuned revision.

Stop the API before running model benchmarks or the offline check on a memory-constrained laptop; otherwise two classifier registries consume RAM and distort timings. Leave local Ollama running. To repeat browser verification, install Playwright in the tooling environment, then run `node web/live-qa.cjs` against the running API. For the complete captioned presentation with visible-result reading time, use `node web/record-walkthrough.cjs` followed by `python scripts/render_walkthrough.py`; see [the walkthrough and timestamps](docs/WALKTHROUGH.md).

### Measured Development Results (Before Policy Version 3)

| Measure | Qwen 4B (selected) | Qwen 1.5B |
| --- | --- | --- |
| Validated journal responses | 49 / 50 | 41 / 50 |
| Warm successful journal p50 / p95 | 11.23 / 15.56 s | 2.25 / 2.54 s |
| Document-question responses | 30 / 30 | 21 / 30 |
| Automated question status/text matches | 27 / 30 | 19 / 30 |

These runs were not a controlled speed comparison: dependency versions and available RAM differed. Both used the same synthetic cases and frozen corrected prompts. Rejected outputs are errors, not fabricated successful summaries. The 4B ten-page upload took 0.865 seconds and returned READY before the immediate question. Retrieval included the expected page on all 27 answerable/partial cases. One of the three automated 4B mismatches is a singular/plural matcher false negative ("line manager" versus "Line managers"); two are conservative full abstentions where partial answers were expected. Raw cases are not relabeled to improve scores.

Those pre-policy-3 development runs included a positive completion entry classified as neutral emotion, and six of twelve expected MEDIUM cases classified LOW. The three development HIGH examples were correctly classified, which is far too little evidence for clinical reliability. Subsequent corrections use four additional development regressions and the AI-assisted self-test inputs; they do not rewrite these historical counts. Exact class counts, service errors, confusion matrices and Wilson intervals are in the reports. Summary/claim NLI validation can both reject valid paraphrases and accept mistakes; it is not a proof of factual correctness. See `reports/CORRECTIONS.md`, `reports/SECURITY.md`, and `evals/README.md`.

### Frozen Held-Out Results (Before Policy Version 3)

These measurements precede the giving-up rule, emotion consistency, mood, summary and CPU precision changes in policy version 3. The frozen set and its original results are preserved; the numbers below do not measure the current revision. The 100 separately authored, provisional English cases produced 96 validated responses and four `SUMMARY_UNSUPPORTED` errors. Successful-request p50/p95 was 11.71/18.39 seconds.

| Output | Matching labels / all cases | Wilson 95% interval | Macro-F1 |
| --- | --- | --- | --- |
| Sentiment | 95 / 100 | 88.8%-97.8% | 0.956 |
| Dominant emotion | 93 / 100 | 86.3%-96.6% | 0.949 |
| Screening priority | 81 / 100 | 72.2%-87.5% | 0.836 |

The fine-tuned RoBERTa baseline matched 99/100 sentiment annotations (macro-F1 0.976), versus NLI sentiment's 97/100 (macro-F1 0.951). Sentiment counts: 72 negative, 14 neutral, 14 positive. Emotions: 14 each except 16 sad. Screening: 70 LOW, 28 MEDIUM, 2 HIGH. Only 13/28 MEDIUM examples matched; both HIGH examples matched. Labels are provisional engineering annotations, not independently validated. Subsequent corrections use development cases and the AI-assisted self-test pack with predicted expectations, rather than the frozen inputs.

`reports/heldout-score-reliability.json` reports selected-score bins, joint sentiment/emotion agreement and Wilson intervals without fitting calibration. The 0.90-0.95 bin contains 23/25 jointly matching labels, so high scores can still be wrong. Four service errors are excluded from the bins but explicitly retained in coverage counts. Per-class probability vectors were not retained; task-wise Brier scores are not invented from this minimum-score heuristic.

## Backup and Restore

Stop the API before either command. Keep archives outside `data/`, and restore only to an empty destination:

```powershell
.venv\Scripts\python.exe -m scripts.backup backup backups\journal-intelligence.zip
.venv\Scripts\python.exe -m scripts.backup restore backups\journal-intelligence.zip --destination restored-data
$env:DATA_DIR = "$PWD\restored-data"
.venv\Scripts\python.exe scripts\start.py
```

After readiness, ask a real question against a restored document to verify its persisted index, not only the SQLite integrity check. Backup archives contain uploaded PDF text and must be treated as private. Journals are not persisted. Unsetting `DATA_DIR` restores the normal data location on the next restart.

With the API stopped, `python -m scripts.rehearse_backup` repeats the real synthetic-Delta restore and keyed owner-isolation check. It requires the document created by the browser verification, preserves its generation/vector count and source hash, then performs a real question without reingestion. Ephemeral keys and private archives are excluded from the public reports.

## Docker and GPU Evaluation

Docker uses a CPU-classifier image and a local Ollama container sharing a network namespace. Models/data persist on mounted local volumes; API keys are mandatory for the Docker-published binding. Bootstrap the selected artifacts explicitly, then start/import Ollama before starting the API:

```bash
uv venv .venv --python 3.11
uv pip install --python .venv/bin/python --require-hashes -r requirements.linux.lock
uv pip install --python .venv/bin/python --no-deps -e .
.venv/bin/python scripts/bootstrap.py --skip-import --generator qwen4b
mkdir -p data
sudo chown 10001:10001 data
export API_KEYS="reviewer:$(.venv/bin/python -c 'import secrets; print(secrets.token_urlsafe(32))')"
docker compose build api
docker compose up -d ollama
docker compose exec ollama ollama create mymanah-qwen4b -f /models/qwen4b/Modelfile.container
docker compose up -d api
```

Do not reuse a Windows absolute Modelfile path inside Linux. `Modelfile.container` refers to `/models/qwen4b/Qwen3-4B-Instruct-2507-Q4_K_M.gguf`. For existing open-mode documents, a key named `local` keeps that owner's namespace; a new principal intentionally gets a separate library.

First bootstrap the selected models with `python scripts/bootstrap.py --skip-import --generator qwen4b`. Stop the native API before using the same data directory through Docker. On a fresh Linux checkout, create `data/`, grant UID 10001 ownership (`sudo chown 10001:10001 data`), and ensure mounted public model artifacts are readable by that UID. Do not recursively change ownership of unrelated or existing private directories. Start/import Ollama before starting the API; if the API has already failed startup because the alias was absent, restart `api` after import. Readiness does not automatically recover a failed initial load.

The [real-model Linux CPU integration](https://github.com/tusharg007/mymanah-journal-intelligence/actions/runs/37673144901) passed on a fresh four-vCPU / 15 GiB runner after downloading/hash-verifying the selected artifacts. Both live tests passed: journal contract and newly uploaded PDF with immediate supported question, citations and abstention. Observed server timings were 19.69 seconds for the journal, 0.898 seconds for the two-page READY upload, and 26.24 seconds for the supported question. These are individual observations, not latency percentiles. The stack was stopped after the bounded job. Exact evidence and the initial mount-permission failure are retained in `reports/docker-integration.json` and `reports/docker-integration.junit.xml`.

For NVIDIA Linux, use `docker compose -f compose.yaml -f compose.gpu.yaml up --build` only with a verified NVIDIA container runtime. GPU nodes/notebooks run the same package and evaluation commands, not a separate notebook implementation or hosted inference provider. The Linux GPU profile still requires execution verification before being marked tested.

## Verification Status

- 129 deterministic tests pass on Windows after policy 5 and the summary quality check. Two additional actual-model live tests are measured separately. The previous Linux CPU Docker real-model run predates policy version 3; Linux deterministic checks run on each push via `.github/workflows/checks.yml`. Ruff and frontend production build are checked separately.
- Desktop/mobile workflows passed with real journal analysis, PDF READY upload, immediate answer, inspected citations, nonblank PDF.js canvas, page navigation and unsupported-question abstention. Layout checks at widths 320, 390, 1440 and 1920 pixels report no page/source overflow or JavaScript errors (`reports/responsive-layout.json`). Actual recordings preserve inference waiting time.
- Offline smoke passed with non-loopback Python sockets blocked. This is an API-process guard, not an OS firewall or instrumentation of Ollama/PDF subprocesses.
- Quiesced backup/restore passed with preserved PDF bytes, generation and vectors, a real restored-index question, 401 for unauthenticated keyed access and 404 for another principal's document/source access.
- Linux CI built the image and verified actual non-root API startup/static/model-manifest paths plus fail-closed missing-model readiness without network access. The separate full real-model CPU Docker integration passed. The Linux GPU profile is not execution-verified.
- No public deployment, paid GPU job, or hiring-team email was started. Dependency audit gaps and residual Chroma advisories are documented, not presented as a zero-vulnerability result.

## Attribution

CardiffNLP's English sentiment model is based on the Twitter/XLM-T research lineage; retain its [model card and attribution](https://huggingface.co/cardiffnlp/twitter-roberta-base-sentiment-latest). Additional upstream cards: [DeBERTa NLI](https://huggingface.co/MoritzLaurer/deberta-v3-base-zeroshot-v2.0-c), [E5](https://huggingface.co/intfloat/multilingual-e5-small), [Qwen 4B GGUF](https://huggingface.co/unsloth/Qwen3-4B-Instruct-2507-GGUF), [Qwen 1.5B GGUF](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF). Upstream model licenses are separate from application code.

Source rendering uses Mozilla [PDF.js](https://github.com/mozilla/pdf.js) (Apache 2.0), pinned through the frontend lock. Worker, fonts, CMaps and image decoders are bundled locally; uploaded PDF scripts/forms/annotations are not executed by the canvas preview. No PDF assets are fetched from a CDN.
