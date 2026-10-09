"""Generate timestamps for the frozen-policy desktop and overview recordings."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def stamp(seconds):
    return f"{int(seconds // 60):02}:{int(seconds % 60):02}"


def time(run, title):
    return next((item["visibleFrom"] for item in run["evidence"] if item["title"] == title), None)


def main():
    desktop = json.loads((ROOT / "reports/walkthrough-policy5-desktop.json").read_text(encoding="utf8"))[0]
    overview = json.loads((ROOT / "reports/walkthrough-policy5-overview.json").read_text(encoding="utf8"))[0]
    assessment = json.loads((ROOT / "reports/unseen-hopelessness-8.json").read_text(encoding="utf8"))
    for run in (desktop, overview):
        assert run["policy_version"] == "journal-policy-5"
        assert run["implementation_sha256"] == assessment["implementation_sha256"]
    durations = [stamp(round(run["videoDurationSeconds"])) for run in (overview, desktop)]
    valid = sum(row["statusCode"] == 200 for row in desktop["journals"])
    lines = [
        "# Recorded Walkthrough", "",
        f"Start with the [{durations[0]} overview](walkthrough-short.mp4), or watch the full [{durations[1]} desktop walkthrough](walkthrough-desktop.mp4). **Both recordings use frozen policy 5.** Mobile is not part of this submission walkthrough.", "",
        "The desktop is newly recorded, not an edited policy-4 clip. Both recordings' source fingerprints match the once-only W1-W8 assessment; no inference code changed afterward. These already-seen inputs are not fresh generalization evidence.", "",
        "The replaced desktop showed confidence above the final 0.99 ceiling in J3/J4/J5/J6/J7/J9 and J12's older abstract summary. The new capture shows the actual current responses, including the concrete J12 summary.", "",
        "All requests run at normal speed with permanently embedded captions below the untouched viewport. Journals remain visible for 14 seconds, supported answers/expanded quotes for 12 seconds, source pages for 8 seconds and final abstention for at least 16 seconds.", "",
        f"Desktop includes {len(desktop['journals'])} distinct journals ({valid} valid responses), including J17 and the complete 512-word entry, plus five PDF questions. Overview repeats J1/J2 and shows annual leave and stock-option abstention. Each recording uploads a fresh handbook and receives HTTP 201 READY.", "",
        "**Known screening misses remain:** W2 returned MEDIUM and W3 LOW instead of predicted HIGH. The [fresh assessment](../reports/UNSEEN_HOPELESSNESS_8.md) is unchanged. Final captions disclose W2/W3; rerecording is not model correction.", "",
        "## Result Timestamps", "",
        "| Completed Result | Desktop (Policy 5) | Overview (Policy 5) |",
        "| --- | --- | --- |",
    ]
    titles = [(row["id"] + " - completed analysis", row["id"] + ": " + row["title"]) for row in desktop["journals"]]
    titles += [("PDF ready", "Fresh PDF READY"), ("Completed answer - page 2", "Annual leave, page-2 quote"),
               ("Original PDF - page 2", "Original page 2"), ("Completed answer - page 3", "Probation notice, page-3 quote"),
               ("Original PDF - page 3", "Original page 3"), ("Completed partial answer - page 2", "Sick leave plus absent stock options: PARTIAL"),
               ("Completed paternity-leave abstention", "Absent paternity leave: abstention"),
               ("Completed unsupported-question result", "Stock-option vesting: abstention")]
    for title, label in titles:
        values = [time(run, title) for run in (desktop, overview)]
        lines.append(f"| {label} | " + " | ".join(stamp(value) if value is not None else "-" for value in values) + " |")
    lines += ["", "Approximate timestamps come from actual completed-result checkpoints.", "",
              "## Inputs and Evidence", "",
              "The [compiled recording results](VIDEO_TEST_RESULTS.md) contain every input and full journal/PDF response. Inputs are AI-assisted predicted-expectation development fixtures, not clinical ground truth. Mood guesses are not counted as label failures.", "",
              "The [source PDF](walkthrough-source.pdf) preserves supplied handbook page content; fresh uploads refresh only creation metadata. Annual leave includes the 24-day allowance and 5-day carry-over/31 March condition with page-2 citations. Desktop additionally shows 15-day probation notice, PARTIAL sick leave with absent stock options named, and paternity abstention.", "",
              "Source pages and complete results were decoded from the actual MP4 for visual checks. Confidence is uncalibrated; the 0.99 ceiling is presentation only and does not establish correct screening. Generation/verification can use a verified extractive fallback.", "",
              "Raw current captures: [desktop](../reports/walkthrough-policy5-desktop.json) and [overview](../reports/walkthrough-policy5-overview.json). The [evidence ledger](EVIDENCE.md) separates seen, fresh and historical stages.", "",
              "The [policy-4 desktop video](https://github.com/tusharg007/mymanah-journal-intelligence/blob/submission-v1/docs/walkthrough-desktop.mp4) and [original raw capture](../reports/walkthrough-recording.json) remain historical evidence; the previous submission-v1 tag is unchanged. The old mobile file is left untouched, not re-recorded or promoted here.", "",
              "## Reproduce Desktop", "",
              "With the real API/models ready, Playwright available to Node and FFmpeg/libass/FFprobe installed:", "",
              "```powershell", "node web/record-walkthrough.cjs --desktop-only",
              r".venv\Scripts\python.exe scripts\render_walkthrough.py --desktop-only",
              r".venv\Scripts\python.exe scripts\export_video_results.py",
              r".venv\Scripts\python.exe scripts\export_walkthrough_guide.py", "```", "",
              "This uses an isolated headless Edge context and does not run mobile. Decoded checkpoints are in `artifacts/walkthrough-policy5-desktop/`. Avoid concurrent inference jobs. Use `--overview` instead of `--desktop-only` only to reproduce the short recording.", ""]
    (ROOT / "docs/WALKTHROUGH.md").write_text("\n".join(lines), encoding="utf8")


if __name__ == "__main__":
    main()
