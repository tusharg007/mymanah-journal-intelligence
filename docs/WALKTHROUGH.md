# Recorded Walkthrough

Start with the [2:02 short walkthrough](walkthrough-short.mp4), or watch the [6:08 desktop video](walkthrough-desktop.mp4) and [3:42 mobile video](walkthrough-mobile.mp4). All open with J1's corrected HIGH result. The recordings use diverse inputs from an AI-assisted self-test pack with predicted expectations, supplied by the candidate. Predictions are a development aid rather than ground truth.

The recordings show actual local inference at normal speed, including processing waits. Captions are embedded permanently in a band below the app; no separate subtitle file is required. Completed journals remain visible for 14 seconds, the final unsupported result for 16 seconds, and each supported answer with its expanded quote for 12 seconds. Mobile scrolls the complete result into view.

Desktop shows 11 scenarios: prolonged distress (J1), achievement (J2), an ordinary day (J3), anger (J4), interview anxiety (J5), workload stress (J6), grief (J7), fear after a threat (J8), negation (J12), mixed feelings (J13), and explicit risk language (J9). Mobile shows J1, J2, J5, J7 and J9. All 16 recorded journal requests returned HTTP 200; the five repeated inputs returned identical six-field responses across viewports. This is observed repeatability, not a general determinism guarantee.

The short cut selects complete scenes from desktop: J1, J2, a fresh PDF upload,
annual-leave answer/source page, and the unsupported question. It retains typing,
processing waits and result-reading time without speeding up inference. The omitted
probation scene remains in both full videos. The [short-cut report](../reports/walkthrough-short.json)
records its exact source segments.

## Result Timestamps

| Completed result | Desktop | Mobile | Short |
| --- | --- | --- | --- |
| J1: prolonged distress, HIGH | 00:15 | 00:15 | 00:15 |
| J2: achievement, happy | 00:36 | 00:36 | 00:36 |
| J3: ordinary day | 01:01 | - | - |
| J4: anger | 01:26 | - | - |
| J5: anxiety | 01:50 | 01:01 | - |
| J6: stress | 02:14 | - | - |
| J7: grief | 02:39 | 01:26 | - |
| J8: fear | 03:03 | - | - |
| J12: negation, happy | 03:25 | - | - |
| J13: mixed feelings | 03:48 | - | - |
| J9: explicit risk language | 04:12 | 01:50 | - |
| PDF READY | 04:31 | 02:07 | 00:55 |
| Annual leave, expanded page-2 quote | 04:54 | 02:29 | 01:18 |
| Original page 2 | 05:07 | 02:42 | 01:31 |
| Probation notice, expanded page-3 quote | 05:23 | 02:58 | - |
| Original page 3 | 05:36 | 03:11 | - |
| Completed unsupported response | 05:51 | 03:25 | 01:45 |

Times are approximate. Captions are permanently embedded below the app viewport in all three videos.

The [76-case self-test report](../reports/REVIEWER_TEST_PACK.md) preserves the original errors and cases outside the video selection. Mood ranges are provisional calibration guesses and are not counted as label failures.

The document portion uploads the supplied three-page handbook, waits for READY, asks about 24 days of annual leave (page 2) and 15 days' notice during probation (page 3), opens each source page, and asks an unsupported stock-option question. Mobile reuses the saved index. The [source PDF](walkthrough-source.pdf) preserves the supplied page content; only creation metadata is refreshed to require a new 201/READY upload.

The [compiled video test results](VIDEO_TEST_RESULTS.md) list every journal input and result from both recordings and all document questions, answers and citations. The [recording report](../reports/walkthrough-recording.json) retains raw responses, request times, viewport sizes, chapter times and visible-result checkpoints. All three videos were checked by decoding opening/result/final frames from the MP4s. The [old policy-2 recording report](../reports/walkthrough-policy2-recording.json) preserves the pre-correction observations; it is not current performance.

## Reproduce

Start the actual API and local models, make Playwright available to Node, and run:

```powershell
node web/record-walkthrough.cjs
.venv\Scripts\python.exe scripts/render_walkthrough.py
.venv\Scripts\python.exe scripts/render_short_walkthrough.py
.venv\Scripts\python.exe scripts/export_video_results.py
```

The browser uses an isolated headless Edge session. The recorder copies the supplied synthetic handbook with fresh creation metadata, requires a new upload to return 201/READY, waits for actual model responses, checks citations, and verifies each result fits in the recorded viewport. It retains the uploaded fixture so mobile can reuse the saved index. This adds a synthetic document to the local library.

The renderer requires FFmpeg with libass and FFprobe. It preserves playback speed and app pixels, adds the caption band, and writes decoded frame checkpoints under `artifacts/walkthrough-v4/`. `web/live-qa.cjs` remains the faster browser smoke check.
