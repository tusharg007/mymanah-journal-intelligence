# Recorded Walkthrough

Watch the [desktop video](walkthrough-desktop.mp4) or [mobile video](walkthrough-mobile.mp4). The expanded recordings use diverse inputs from the supplied reviewer test pack, not just one journal.

The recordings show actual local inference at normal speed, including processing waits. Captions are embedded permanently in a band below the app; no separate subtitle file is required. Completed journals remain visible for 14 seconds, the final unsupported result for 16 seconds, and each supported answer with its expanded quote for 12 seconds. Mobile scrolls the complete result into view.

Desktop shows 11 scenarios: achievement (J2), an ordinary day (J3), anger (J4), interview anxiety (J5), workload stress (J6), grief (J7), fear after a threat (J8), negation (J12), mixed feelings (J13), prolonged distress (J1), and explicit risk language (J9). Mobile shows J2, J5, J7, J1 and J9.

## Result Timestamps

| Completed result | Desktop | Mobile |
| --- | --- | --- |
| J2: achievement | 00:22 | 00:20 |
| J3: ordinary day | 01:01 | - |
| J4: anger | 01:43 | - |
| J5: anxiety | 02:21 | 00:56 |
| J6: stress | 02:58 | - |
| J7: grief | 03:35 | 01:30 |
| J8: fear | 04:15 | - |
| J12: negation | 04:50 | - |
| J13: mixed feelings | 05:26 | - |
| J1: prolonged distress; risk disagreement | 06:05 | 02:06 |
| J9: explicit risk language | 06:44 | 02:48 |
| PDF READY | 07:03 | 03:05 |
| Annual leave, expanded page-2 quote | 07:27 | 03:31 |
| Original page 2 | 07:40 | 03:44 |
| Probation notice, expanded page-3 quote | 07:59 | 04:04 |
| Original page 3 | 08:12 | 04:16 |
| Completed unsupported response | 08:26 | 04:31 |

Times are approximate; desktop runs about 8:43 and mobile about 4:48.

Captions label observed test-pack disagreements, including neutral emotion for achievement and MEDIUM rather than expected HIGH for prolonged distress. These are unresolved model/policy limitations, not successful expected predictions. The [76-case report](../reports/REVIEWER_TEST_PACK.md) includes errors and cases outside this illustrative selection.

The document portion uploads the supplied three-page handbook, waits for READY, asks about 24 days of annual leave (page 2) and 15 days' notice during probation (page 3), opens each source page, and asks an unsupported stock-option question. Mobile reuses the saved index. The [source PDF](walkthrough-source.pdf) preserves the supplied page content; only creation metadata is refreshed to require a new 201/READY upload.

The [compiled video test results](VIDEO_TEST_RESULTS.md) list every journal input and result from both recordings and all document questions, answers and citations. The [recording report](../reports/walkthrough-recording.json) retains raw responses, request times, viewport sizes, chapter times and visible-result checkpoints. Both recordings were checked by decoding frames from the final MP4s, including the last frame.

## Reproduce

Start the actual API and local models, make Playwright available to Node, and run:

```powershell
node web/record-walkthrough.cjs
.venv\Scripts\python.exe scripts/render_walkthrough.py
```

The browser uses an isolated headless Edge session. The recorder copies the supplied synthetic handbook with fresh creation metadata, requires a new upload to return 201/READY, waits for actual model responses, checks citations, and verifies each result fits in the recorded viewport. It retains the uploaded fixture so mobile can reuse the saved index. This adds a synthetic document to the local library.

The renderer requires FFmpeg with libass and FFprobe. It preserves playback speed and app pixels, adds the caption band, and writes decoded frame checkpoints under `artifacts/walkthrough-v3/`. `web/live-qa.cjs` remains the faster browser smoke check.
