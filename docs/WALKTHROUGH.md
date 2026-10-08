# Recorded Walkthrough

Start with the [02:05 policy-5 overview](walkthrough-short.mp4). The [08:16 desktop](walkthrough-desktop.mp4) and [04:33 mobile](walkthrough-mobile.mp4) recordings remain policy 4. All open with J1's HIGH result.

The overview is a new uninterrupted capture on frozen policy 5 after W1-W8. Its inference fingerprints match the fresh assessment. It is not an edited policy-4 clip or fresh unseen evidence. W2/W3 screening misses remain published in [the fresh report](../reports/UNSEEN_HOPELESSNESS_8.md); there was no further inference tuning.

All videos run at normal speed with permanently embedded captions below the untouched viewport. Journals are held for 14 seconds, supported answers/expanded quotes for 12 seconds, source pages for 8 seconds, and final abstention for at least 16 seconds. The overview's final caption discloses W2/W3.

The overview shows J1, J2, a fresh HTTP 201 READY upload, annual leave with page-2 evidence and uncited stock-option abstention. It adds two seen journal requests, both valid, not two independent evaluation cases. [Current raw overview](../reports/walkthrough-policy5-overview.json).

Full desktop/mobile recordings contain 18 valid journal requests across 13 distinct inputs, including J17 and a complete 512-word journal. Five repeated mobile inputs returned 5/5 identical six-field responses; this is observed repeatability, not a general determinism guarantee. Inputs are AI-assisted predicted-expectation fixtures and development data, not clinical ground truth.

## Result Timestamps

| Completed Result | Desktop (Policy 4) | Mobile (Policy 4) | Overview (Policy 5) |
| --- | --- | --- | --- |
| J1: Prolonged distress | 00:16 | 00:15 | 00:15 |
| J2: Positive achievement | 00:39 | 00:37 | 00:36 |
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
| Fresh PDF READY | 05:50 | 02:08 | 00:55 |
| Annual leave, page-2 quote | 06:14 | 02:31 | 01:18 |
| Original page 2 | 06:27 | 02:44 | 01:31 |
| Probation notice, page-3 quote | 06:44 | 03:00 | - |
| Original page 3 | 06:57 | 03:13 | - |
| Sick leave plus absent stock options: PARTIAL | 07:14 | 03:31 | - |
| Absent paternity leave: abstention | 07:40 | 03:57 | - |
| Stock-option vesting: abstention | 07:59 | 04:16 | 01:44 |

Times are approximate, derived from actual capture checkpoints.

## Evidence and Limits

All recordings use the supplied three-page handbook. Desktop and the new overview each require a fresh HTTP 201 READY upload; mobile reuses the old index. The [source PDF](walkthrough-source.pdf) preserves the page content; fresh uploads have refreshed creation metadata.

The overview shows 24 annual-leave days and the 5-day carry-over/31 March condition with page-2 citations. Full recordings additionally show 15-day probation notice, PARTIAL sick leave with absent stock options named, and paternity abstention.

The [compiled recording results](VIDEO_TEST_RESULTS.md) separate full policy-5 overview responses from unchanged policy-4 outputs. The [evidence ledger](EVIDENCE.md) separates historical, seen and fresh assessment stages. Confidence is uncalibrated; policy 5's 0.99 ceiling is presentation only and does not validate screening risk.

The [original policy-4 overview](https://github.com/tusharg007/mymanah-journal-intelligence/blob/ac6633611d6ad98570a90ad667ad748231b6d222/docs/walkthrough-short.mp4) and [original cut metadata](https://github.com/tusharg007/mymanah-journal-intelligence/blob/ac6633611d6ad98570a90ad667ad748231b6d222/reports/walkthrough-short.json) remain accessible at an immutable commit.

The [full policy-4 capture](../reports/walkthrough-recording.json), [policy-3 capture](../reports/walkthrough-policy3-recording.json) and [policy-2 capture](../reports/walkthrough-policy2-recording.json) are preserved historical evidence. Actual result/final MP4 frames were decoded for visual checks; source pages are nonblank and results remain readable.

## Reproduce the Overview

With the actual API and pinned models ready, Playwright available to Node and FFmpeg/libass/FFprobe installed:

```powershell
node web/record-walkthrough.cjs --overview
.venv\Scripts\python.exe scripts\render_walkthrough.py --overview
.venv\Scripts\python.exe scripts\export_video_results.py
.venv\Scripts\python.exe scripts\export_walkthrough_guide.py
```

This uses an isolated headless Edge context and does not rewrite the full desktop/mobile recordings. Decoded checkpoints are in artifacts/walkthrough-policy5-overview/. Avoid concurrent inference jobs during measurement.
