# Recorded Walkthrough

Start with the [02:05 overview](walkthrough-short.mp4), or watch the full [08:09 desktop walkthrough](walkthrough-desktop.mp4). **Both recordings use frozen policy 5.** Mobile is not part of this submission walkthrough.

The desktop is newly recorded, not an edited policy-4 clip. Both recordings' source fingerprints match the once-only W1-W8 assessment; no inference code changed afterward. These already-seen inputs are not fresh generalization evidence.

The replaced desktop showed confidence above the final 0.99 ceiling in J3/J4/J5/J6/J7/J9 and J12's older abstract summary. The new capture shows the actual current responses, including the concrete J12 summary.

All requests run at normal speed with permanently embedded captions below the untouched viewport. Journals remain visible for 14 seconds, supported answers/expanded quotes for 12 seconds, source pages for 8 seconds and final abstention for at least 16 seconds.

Desktop includes 13 distinct journals (13 valid responses), including J17 and the complete 512-word entry, plus five PDF questions. Overview repeats J1/J2 and shows annual leave and stock-option abstention. Each recording uploads a fresh handbook and receives HTTP 201 READY.

**Known screening misses remain:** W2 returned MEDIUM and W3 LOW instead of predicted HIGH. The [fresh assessment](../reports/UNSEEN_HOPELESSNESS_8.md) is unchanged. Final captions disclose W2/W3; rerecording is not model correction.

## Result Timestamps

| Completed Result | Desktop (Policy 5) | Overview (Policy 5) |
| --- | --- | --- |
| J1: Prolonged distress | 00:22 | 00:15 |
| J2: Positive achievement | 00:44 | 00:36 |
| J3: An ordinary day | 01:09 | - |
| J4: Anger after criticism | 01:33 | - |
| J5: Interview anxiety | 01:58 | - |
| J6: Workload stress | 02:22 | - |
| J7: Grief | 02:45 | - |
| J8: Fear after a threat | 03:09 | - |
| J12: Negation: not sad | 03:33 | - |
| J13: Mixed excitement and worry | 03:56 | - |
| J9: Explicit risk language | 04:20 | - |
| J17: One-fact entry with an instruction attack | 04:43 | - |
| long01: A full 512-word journal | 05:19 | - |
| Fresh PDF READY | 05:38 | 00:55 |
| Annual leave, page-2 quote | 06:09 | 01:18 |
| Original page 2 | 06:22 | 01:31 |
| Probation notice, page-3 quote | 06:38 | - |
| Original page 3 | 06:51 | - |
| Sick leave plus absent stock options: PARTIAL | 07:09 | - |
| Absent paternity leave: abstention | 07:34 | - |
| Stock-option vesting: abstention | 07:53 | 01:44 |

Approximate timestamps come from actual completed-result checkpoints.

## Inputs and Evidence

The [compiled recording results](VIDEO_TEST_RESULTS.md) contain every input and full journal/PDF response. Inputs are AI-assisted predicted-expectation development fixtures, not clinical ground truth. Mood guesses are not counted as label failures.

The [source PDF](walkthrough-source.pdf) preserves supplied handbook page content; fresh uploads refresh only creation metadata. Annual leave includes the 24-day allowance and 5-day carry-over/31 March condition with page-2 citations. Desktop additionally shows 15-day probation notice, PARTIAL sick leave with absent stock options named, and paternity abstention.

Source pages and complete results were decoded from the actual MP4 for visual checks. Confidence is uncalibrated; the 0.99 ceiling is presentation only and does not establish correct screening. Generation/verification can use a verified extractive fallback.

Raw current captures: [desktop](../reports/walkthrough-policy5-desktop.json) and [overview](../reports/walkthrough-policy5-overview.json). The [evidence ledger](EVIDENCE.md) separates seen, fresh and historical stages.

The [policy-4 desktop video](https://github.com/tusharg007/mymanah-journal-intelligence/blob/submission-v1/docs/walkthrough-desktop.mp4) and [original raw capture](../reports/walkthrough-recording.json) remain historical evidence; the previous submission-v1 tag is unchanged. The old mobile file is left untouched, not re-recorded or promoted here.

## Reproduce Desktop

With the real API/models ready, Playwright available to Node and FFmpeg/libass/FFprobe installed:

```powershell
node web/record-walkthrough.cjs --desktop-only
.venv\Scripts\python.exe scripts\render_walkthrough.py --desktop-only
.venv\Scripts\python.exe scripts\export_video_results.py
.venv\Scripts\python.exe scripts\export_walkthrough_guide.py
```

This uses an isolated headless Edge context and does not run mobile. Decoded checkpoints are in `artifacts/walkthrough-policy5-desktop/`. Avoid concurrent inference jobs. Use `--overview` instead of `--desktop-only` only to reproduce the short recording.
