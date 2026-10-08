"""Generate a version-aware walkthrough guide from actual recording checkpoints."""
from __future__ import annotations

import json

from mymanah.config import ROOT


def stamp(seconds):
    return f"{int(seconds // 60):02}:{int(seconds % 60):02}"


def time(run, title):
    return next((item["visibleFrom"] for item in run["evidence"] if item["title"] == title), None)


def main():
    desktop, mobile = json.loads((ROOT / "reports/walkthrough-recording.json").read_text(encoding="utf8"))
    overview = json.loads((ROOT / "reports/walkthrough-policy5-overview.json").read_text(encoding="utf8"))[0]
    assessment = json.loads((ROOT / "reports/unseen-hopelessness-8.json").read_text(encoding="utf8"))
    assert overview["policy_version"] == "journal-policy-5"
    assert overview["implementation_sha256"] == assessment["implementation_sha256"]
    durations = [stamp(round(run["videoDurationSeconds"])) for run in (overview, desktop, mobile)]
    equal = sum(row["actual"] == next(item["actual"] for item in desktop["journals"] if item["id"] == row["id"])
                for row in mobile["journals"])
    lines = [
        "# Recorded Walkthrough", "",
        f"Start with the [{durations[0]} policy-5 overview](walkthrough-short.mp4). The [{durations[1]} desktop](walkthrough-desktop.mp4) and [{durations[2]} mobile](walkthrough-mobile.mp4) recordings remain policy 4. All open with J1's HIGH result.", "",
        "The overview is a new uninterrupted capture on frozen policy 5 after W1-W8. Its inference fingerprints match the fresh assessment. It is not an edited policy-4 clip or fresh unseen evidence. W2/W3 screening misses remain published in [the fresh report](../reports/UNSEEN_HOPELESSNESS_8.md); there was no further inference tuning.", "",
        "All videos run at normal speed with permanently embedded captions below the untouched viewport. Journals are held for 14 seconds, supported answers/expanded quotes for 12 seconds, source pages for 8 seconds, and final abstention for at least 16 seconds. The overview's final caption discloses W2/W3.", "",
        "The overview shows J1, J2, a fresh HTTP 201 READY upload, annual leave with page-2 evidence and uncited stock-option abstention. It adds two seen journal requests, both valid, not two independent evaluation cases. [Current raw overview](../reports/walkthrough-policy5-overview.json).", "",
        f"Full desktop/mobile recordings contain 18 valid journal requests across 13 distinct inputs, including J17 and a complete 512-word journal. Five repeated mobile inputs returned {equal}/5 identical six-field responses; this is observed repeatability, not a general determinism guarantee. Inputs are AI-assisted predicted-expectation fixtures and development data, not clinical ground truth.", "",
        "## Result Timestamps", "",
        "| Completed Result | Desktop (Policy 4) | Mobile (Policy 4) | Overview (Policy 5) |",
        "| --- | --- | --- | --- |",
    ]
    titles = [(row["id"] + " - completed analysis", row["id"] + ": " + row["title"]) for row in desktop["journals"]]
    titles += [("PDF ready", "Fresh PDF READY"), ("Completed answer - page 2", "Annual leave, page-2 quote"),
               ("Original PDF - page 2", "Original page 2"), ("Completed answer - page 3", "Probation notice, page-3 quote"),
               ("Original PDF - page 3", "Original page 3"), ("Completed partial answer - page 2", "Sick leave plus absent stock options: PARTIAL"),
               ("Completed paternity-leave abstention", "Absent paternity leave: abstention"),
               ("Completed unsupported-question result", "Stock-option vesting: abstention")]
    for title, label in titles:
        values = [time(run, title) for run in (desktop, mobile, overview)]
        lines.append(f"| {label} | " + " | ".join(stamp(value) if value is not None else "-" for value in values) + " |")
    lines += ["", "Times are approximate, derived from actual capture checkpoints.", "",
              "## Evidence and Limits", "",
              "All recordings use the supplied three-page handbook. Desktop and the new overview each require a fresh HTTP 201 READY upload; mobile reuses the old index. The [source PDF](walkthrough-source.pdf) preserves the page content; fresh uploads have refreshed creation metadata.", "",
              "The overview shows 24 annual-leave days and the 5-day carry-over/31 March condition with page-2 citations. Full recordings additionally show 15-day probation notice, PARTIAL sick leave with absent stock options named, and paternity abstention.", "",
              "The [compiled recording results](VIDEO_TEST_RESULTS.md) separate full policy-5 overview responses from unchanged policy-4 outputs. The [evidence ledger](EVIDENCE.md) separates historical, seen and fresh assessment stages. Confidence is uncalibrated; policy 5's 0.99 ceiling is presentation only and does not validate screening risk.", "",
              "The [original policy-4 overview](https://github.com/tusharg007/mymanah-journal-intelligence/blob/ac6633611d6ad98570a90ad667ad748231b6d222/docs/walkthrough-short.mp4) and [original cut metadata](https://github.com/tusharg007/mymanah-journal-intelligence/blob/ac6633611d6ad98570a90ad667ad748231b6d222/reports/walkthrough-short.json) remain accessible at an immutable commit.", "",
              "The [full policy-4 capture](../reports/walkthrough-recording.json), [policy-3 capture](../reports/walkthrough-policy3-recording.json) and [policy-2 capture](../reports/walkthrough-policy2-recording.json) are preserved historical evidence. Actual result/final MP4 frames were decoded for visual checks; source pages are nonblank and results remain readable.", "",
              "## Reproduce the Overview", "",
              "With the actual API and pinned models ready, Playwright available to Node and FFmpeg/libass/FFprobe installed:", ""]
    fence = chr(96) * 3
    lines += [fence + "powershell", "node web/record-walkthrough.cjs --overview",
              r".venv\Scripts\python.exe scripts\render_walkthrough.py --overview",
              r".venv\Scripts\python.exe scripts\export_video_results.py",
              r".venv\Scripts\python.exe scripts\export_walkthrough_guide.py",
              fence, "",
              "This uses an isolated headless Edge context and does not rewrite the full desktop/mobile recordings. Decoded checkpoints are in artifacts/walkthrough-policy5-overview/. Avoid concurrent inference jobs during measurement.", ""]
    (ROOT / "docs/WALKTHROUGH.md").write_text("\n".join(lines), encoding="utf8")


if __name__ == "__main__":
    main()
