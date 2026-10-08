# Recorded Walkthrough

Watch the [desktop video (2:38)](walkthrough-desktop.mp4) or [mobile video (2:18)](walkthrough-mobile.mp4). These replace the original short recordings, which advanced too quickly and closed before the final result had time to render visibly.

The recordings show actual local inference at normal speed, including processing waits. Captions sit in a separate band below the app. Completed journal and unsupported-question results remain visible for about 16 seconds; each supported answer and its expanded quote remain visible for about 12 seconds. Mobile deliberately scrolls the complete result into view.

| Completed result | Desktop | Mobile | Visible evidence |
| --- | --- | --- | --- |
| Journal analysis | 00:39 | 00:24 | All six outputs, summary and measured request time |
| PDF ready | 01:01 | 00:44 | READY status and two-page document; desktop uploads a new PDF, mobile reuses its saved index |
| Annual leave answer | 01:21 | 01:01 | 23 days, expanded exact quote and page-1 citation |
| Original page 1 | 01:33 | 01:14 | Source PDF text can be compared with the answer |
| Equipment answer | 01:55 | 01:34 | 420 pounds per year, expanded quote and page-2 citation |
| Original page 2 | 02:07 | 01:47 | Citation selects the correct rendered page |
| Unsupported question | 02:23 | 02:02 | Completed INSUFFICIENT EVIDENCE response with no citations; remains visible through the end |

Times are approximate. The [source PDF](walkthrough-source.pdf) contains the exact non-identifying policy used in the video. The journal input is: "Today I celebrated my friend's promotion with her. I felt joyful and grateful for our time together."

The [recording report](../reports/walkthrough-recording.json) retains actual responses, request times, viewport sizes, chapter times and visible-result checkpoints. Both recordings were checked by decoding frames from the final MP4s, including the last frame. These show the completed results and their captions.

## Reproduce

Start the actual API and local models, make Playwright available to Node, and run:

```powershell
node web/record-walkthrough.cjs
.venv\Scripts\python.exe scripts/render_walkthrough.py
```

The browser uses an isolated headless Edge session. The recorder creates a synthetic PDF with fresh creation metadata, requires a new upload to return 201/READY, waits for actual model responses, checks citations, and verifies each result fits in the recorded viewport. It retains the uploaded fixture so the mobile session can reuse the saved index. This adds a synthetic document to the local library.

The renderer requires FFmpeg with libass and FFprobe. It preserves playback speed and app pixels, adds the caption band, and writes frame checkpoints for inspection under `artifacts/walkthrough-v2/`. `web/live-qa.cjs` remains the faster browser smoke check; the presentation recording uses the dedicated script above.
