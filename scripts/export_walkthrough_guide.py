"""Write walkthrough timestamps from the completed capture rather than hand-copying them."""
from __future__ import annotations

import json

from mymanah.config import ROOT


def stamp(seconds):
    return f"{int(seconds // 60):02}:{int(seconds % 60):02}"


def main():
    recordings = json.loads((ROOT / "reports/walkthrough-recording.json").read_text(encoding="utf8"))
    short = json.loads((ROOT / "reports/walkthrough-short.json").read_text(encoding="utf8"))
    desktop, mobile = recordings

    def time(run, title):
        return next((item["visibleFrom"] for item in run["evidence"] if item["title"] == title), None)

    def short_time(source):
        offset = 0
        for segment in short["source_segments"]:
            if segment["start"] <= source < segment["end"]:
                return offset + source - segment["start"]
            offset += segment["end"] - segment["start"]
        return None

    durations = [stamp(round(short["duration_seconds"])), stamp(round(desktop["videoDurationSeconds"])), stamp(round(mobile["videoDurationSeconds"]))]
    equal = sum(row["actual"] == next(item["actual"] for item in desktop["journals"] if item["id"] == row["id"])
                for row in mobile["journals"])
    lines = ["# Recorded Walkthrough", "",
             f"Start with the [{durations[0]} short walkthrough](walkthrough-short.mp4), or watch the [{durations[1]} desktop](walkthrough-desktop.mp4) and [{durations[2]} mobile](walkthrough-mobile.mp4) recordings. All open with J1's HIGH result.", "",
             "The videos show real local inference at normal speed, with permanently embedded captions below the untouched app viewport. Journal results are held for 14 seconds, supported answers and expanded quotes for 12 seconds, source pages for 8 seconds, and the final unsupported result for 16 seconds. Mobile scrolls each complete result into view.", "",
             "Desktop covers eleven diverse pack scenarios, a one-fact instruction-attack entry (J17), and a complete 512-word development journal. The long entry is pasted visibly rather than typed character by character. Inputs are an AI-assisted self-test pack with predicted expectations plus development data; predictions are not ground truth.",
             f"All 18 recorded journal requests returned HTTP 200. Of five repeated mobile inputs, {equal}/5 returned identical six-field outputs to desktop; this is observed repeatability rather than a general determinism guarantee.", "",
             "The short cut retains complete scenes for J1, J2, fresh PDF upload, annual-leave answer with page-2 evidence, and the final unsupported question. Input entry, processing waits and result-reading time remain at normal speed. Other scenes are in the full videos. Exact segments are in the [short-cut report](../reports/walkthrough-short.json).", "",
             "## Result Timestamps", "",
             "| Completed result | Desktop | Mobile | Short |", "| --- | --- | --- | --- |"]
    titles = [(row["id"] + " - completed analysis", row["id"] + ": " + row["title"]) for row in desktop["journals"]]
    titles += [("PDF ready", "Fresh PDF READY"), ("Completed answer - page 2", "Annual leave, page-2 quote"),
               ("Original PDF - page 2", "Original page 2"), ("Completed answer - page 3", "Probation notice, page-3 quote"),
               ("Original PDF - page 3", "Original page 3"), ("Completed partial answer - page 2", "Sick leave plus absent stock options: PARTIAL"),
               ("Completed paternity-leave abstention", "Absent paternity leave: abstention"),
               ("Completed unsupported-question result", "Stock-option vesting: abstention")]
    for title, label in titles:
        at = time(desktop, title)
        values = [at, time(mobile, title), short_time(at)]
        lines.append(f"| {label} | " + " | ".join(stamp(value) if value is not None else "-" for value in values) + " |")
    lines += ["", "Times are approximate and are derived from the actual capture report.", "",
              "## Evidence and Limits", "",
              "Both viewports use the supplied three-page handbook. Desktop requires a fresh HTTP 201 READY upload; mobile reuses that index. The [source PDF](walkthrough-source.pdf) preserves supplied page content with refreshed creation metadata. Answers show annual leave (24 days, page 2), probation notice (15 days, page 3), a verified partial sick-leave answer with the missing stock-option topic named, and uncited paternity/vesting abstentions.", "",
              "Current summaries come from the real Qwen3 4B generator with evidence verification; a verified extractive fallback is available after two failures. One-fact entries receive non-repeating scope text. Confidence uses the selected emotion decision score or winning sentiment confidence for a consistency override. It does not establish risk correctness.", "",
              "The [compiled video results](VIDEO_TEST_RESULTS.md) contain every input and response. Separate [current development results](../reports/JOURNAL_POLICY4_REGRESSION.md) include generator metadata and independent long-entry timings. The [ten unseen results](../reports/UNSEEN_REVIEW_10.md) were run once without tuning: U6/U10 retained screening misses. Those cases are reported separately and are not re-recorded as development successes.", "",
              "The [raw recording report](../reports/walkthrough-recording.json) preserves requests, responses, viewport sizes and checkpoints. MP4 result/final frames were decoded for visual checks, including nonblank source-page canvases. Prior [policy-3](../reports/walkthrough-policy3-recording.json) and [policy-2](../reports/walkthrough-policy2-recording.json) raw recordings remain historical evidence.", "",
              "## Reproduce", "", "Start the actual API and local models, make Playwright available to Node, then run:", "",
              "```powershell", "node web/record-walkthrough.cjs", ".venv\\Scripts\\python.exe scripts/render_walkthrough.py",
              ".venv\\Scripts\\python.exe scripts/render_short_walkthrough.py", ".venv\\Scripts\\python.exe scripts/export_video_results.py",
              ".venv\\Scripts\\python.exe scripts/export_walkthrough_guide.py", "```", "",
              "The recorder uses an isolated headless Edge session and retains its synthetic upload for mobile reuse. The renderer requires FFmpeg/libass and FFprobe; decoded checkpoints are in `artifacts/walkthrough-v5/`. Avoid concurrent inference jobs during measurement.", ""]
    (ROOT / "docs/WALKTHROUGH.md").write_text("\n".join(lines), encoding="utf8")


if __name__ == "__main__":
    main()
