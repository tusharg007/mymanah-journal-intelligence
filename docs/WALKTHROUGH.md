# Recorded Walkthrough

Start with the [02:04 short walkthrough](walkthrough-short.mp4), or watch the [08:16 desktop](walkthrough-desktop.mp4) and [04:33 mobile](walkthrough-mobile.mp4) recordings. All open with J1's HIGH result.

The videos show real local inference at normal speed, with permanently embedded captions below the untouched app viewport. Journal results are held for 14 seconds, supported answers and expanded quotes for 12 seconds, source pages for 8 seconds, and the final unsupported result for 16 seconds. Mobile scrolls each complete result into view.

Desktop covers eleven diverse pack scenarios, a one-fact instruction-attack entry (J17), and a complete 512-word development journal. The long entry is pasted visibly rather than typed character by character. Inputs are an AI-assisted self-test pack with predicted expectations plus development data; predictions are not ground truth.
All 18 recorded journal requests returned HTTP 200. Of five repeated mobile inputs, 5/5 returned identical six-field outputs to desktop; this is observed repeatability rather than a general determinism guarantee.

The short cut retains complete scenes for J1, J2, fresh PDF upload, annual-leave answer with page-2 evidence, and the final unsupported question. Input entry, processing waits and result-reading time remain at normal speed. Other scenes are in the full videos. Exact segments are in the [short-cut report](../reports/walkthrough-short.json).

## Result Timestamps

| Completed result | Desktop | Mobile | Short |
| --- | --- | --- | --- |
| J1: Prolonged distress | 00:16 | 00:15 | 00:16 |
| J2: Positive achievement | 00:39 | 00:37 | 00:39 |
| J3: An ordinary day | 01:03 | - | - |
| J4: Anger after criticism | 01:29 | - | - |
| J5: Interview anxiety | 01:55 | 01:02 | - |
| J6: Workload stress | 02:19 | - | - |
| J7: Grief | 02:44 | 01:26 | - |
| J8: Fear after a threat | 03:10 | - | - |
| J12: Negation: not sad | 03:33 | - | - |
| J13: Mixed excitement and worry | 03:57 | - | - |
| J9: Explicit risk language | 04:22 | 01:50 | - |
| J17: One-fact entry with an instruction attack | 04:46 | - | - |
| long01: A full 512-word journal | 05:31 | - | - |
| Fresh PDF READY | 05:50 | 02:08 | 00:58 |
| Annual leave, page-2 quote | 06:14 | 02:31 | 01:22 |
| Original page 2 | 06:27 | 02:44 | 01:35 |
| Probation notice, page-3 quote | 06:44 | 03:00 | - |
| Original page 3 | 06:57 | 03:13 | - |
| Sick leave plus absent stock options: PARTIAL | 07:14 | 03:31 | - |
| Absent paternity leave: abstention | 07:40 | 03:57 | - |
| Stock-option vesting: abstention | 07:59 | 04:16 | 01:48 |

Times are approximate and are derived from the actual capture report.

## Evidence and Limits

Both viewports use the supplied three-page handbook. Desktop requires a fresh HTTP 201 READY upload; mobile reuses that index. The [source PDF](walkthrough-source.pdf) preserves supplied page content with refreshed creation metadata. Answers show annual leave (24 days, page 2), probation notice (15 days, page 3), a verified partial sick-leave answer with the missing stock-option topic named, and uncited paternity/vesting abstentions.

Current summaries come from the real Qwen3 4B generator with evidence verification; a verified extractive fallback is available after two failures. One-fact entries receive non-repeating scope text. Confidence uses the selected emotion decision score or winning sentiment confidence for a consistency override. It does not establish risk correctness.

The [compiled video results](VIDEO_TEST_RESULTS.md) contain every input and response. Separate [current development results](../reports/JOURNAL_POLICY4_REGRESSION.md) include generator metadata and independent long-entry timings. The [ten unseen results](../reports/UNSEEN_REVIEW_10.md) were run once without tuning: U6/U10 retained screening misses. Those cases are reported separately and are not re-recorded as development successes.

The [raw recording report](../reports/walkthrough-recording.json) preserves requests, responses, viewport sizes and checkpoints. MP4 result/final frames were decoded for visual checks, including nonblank source-page canvases. Prior [policy-3](../reports/walkthrough-policy3-recording.json) and [policy-2](../reports/walkthrough-policy2-recording.json) raw recordings remain historical evidence.

## Reproduce

Start the actual API and local models, make Playwright available to Node, then run:

```powershell
node web/record-walkthrough.cjs
.venv\Scripts\python.exe scripts/render_walkthrough.py
.venv\Scripts\python.exe scripts/render_short_walkthrough.py
.venv\Scripts\python.exe scripts/export_video_results.py
.venv\Scripts\python.exe scripts/export_walkthrough_guide.py
```

The recorder uses an isolated headless Edge session and retains its synthetic upload for mobile reuse. The renderer requires FFmpeg/libass and FFprobe; decoded checkpoints are in `artifacts/walkthrough-v5/`. Avoid concurrent inference jobs during measurement.
