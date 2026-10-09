"""Compile current policy-5 desktop and overview responses without rewriting historical evidence."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", "<br>")


def expected_labels(value: str) -> set[str]:
    items = {re.sub(r"\s+ok$", "", item.strip().lower())
             for item in re.split(r"\s+or\s+|\s*\(|\s*\)", value)}
    return {item for item in items if item and item != "ok"}


def journal_outcome(expected: dict, actual: dict) -> list[str]:
    mismatches = []
    for field, key in (("Sentiment", "sentiment"), ("Emotion", "emotion"), ("Risk", "crisisRisk")):
        labels = expected_labels(expected[field])
        if "any" not in labels and actual[key].lower() not in labels:
            mismatches.append(f"{field}: returned {actual[key]}; expected {expected[field]}.")
    return mismatches


def timestamp(run: dict, title: str) -> str:
    seconds = next(row["visibleFrom"] for row in run["evidence"] if row["title"] == title)
    return f"{int(seconds // 60):02}:{int(seconds % 60):02}"


def json_block(value: object) -> list[str]:
    return ["```json", json.dumps(value, ensure_ascii=False, indent=2), "```", ""]


def run_section(run: dict, name: str, source: str) -> list[str]:
    lines = [f"## {name}: Journal Analysis", "",
             'Workflow: `POST /analyze-journal`, with `{"text": "..."}`.', ""]
    for row in run["journals"]:
        expected = row["expected"]
        lines += [f"### {name} {row['id']}: {row['title']}", "", "Input:", ""]
        lines += json_block({"text": row["input"]})
        lines += ["| Field | Predicted expectation | Actual response |", "| --- | --- | --- |"]
        actual = row["actual"]
        if row["statusCode"] == 200:
            for field, key in (("Sentiment", "sentiment"), ("Emotion", "emotion"),
                               ("Risk", "crisisRisk"), ("Mood", "moodScore")):
                lines.append(f"| {field} | {cell(expected[field])} | {cell(actual[key])} |")
            lines += [f"| Confidence | Uncalibrated decision score | {actual['confidence']:.4f} |", "",
                      f"HTTP 200, {row['journalSeconds']:.3f} seconds on the tested GPU laptop.",
                      f"Completed result visible at {timestamp(run, row['id'] + ' - completed analysis')}.", "",
                      "Full six-field response:", ""]
            lines += json_block(actual)
            mismatches = journal_outcome(expected, actual)
            lines += ["**Predicted-label comparison:** " +
                      (" ".join(mismatches) if mismatches else "Sentiment, emotion and risk match the supplied predictions."), "",
                      "Mood ranges are provisional and are not counted as failed label checks.", ""]
        else:
            lines += ["", f"HTTP {row['statusCode']}, {row['journalSeconds']:.3f} seconds. No successful analysis:", ""]
            lines += json_block(actual)
    lines += [f"## {name}: Document Upload and Questions", "",
              "Workflow: `POST /documents`, then `POST /documents/{document_id}/questions`.", "",
              "Input: supplied three-page `Employee_Handbook_Test.pdf`, with fresh creation metadata.",
              "Actual fresh upload response: HTTP 201 READY.", ""]
    lines += json_block(run["upload"])
    for index, row in enumerate(run["responses"], start=1):
        lines += [f"### {name} Question {index}", "", "Input:", ""]
        lines += json_block({"question": row["question"]})
        lines += [f"HTTP 200, {row['seconds']:.3f} seconds. Full response, including every citation:", ""]
        lines += json_block(row["result"])
    lines += [f"### {name} Unsupported Stock-Option Question", "", "Input:", ""]
    lines += json_block({"question": "What is the stock option vesting schedule?"})
    lines += ["HTTP 200. Request latency was not separately recorded. Full response:", ""]
    lines += json_block(run["unsupported"])
    lines += [f"Raw requests, timestamps, policy and source fingerprints: [{source}](../reports/{source}).", ""]
    return lines


def main() -> None:
    desktop_name = "walkthrough-policy5-desktop.json"
    overview_name = "walkthrough-policy5-overview.json"
    desktop = json.loads((ROOT / "reports" / desktop_name).read_text(encoding="utf8"))[0]
    overview = json.loads((ROOT / "reports" / overview_name).read_text(encoding="utf8"))[0]
    assessment = json.loads((ROOT / "reports/unseen-hopelessness-8.json").read_text(encoding="utf8"))
    for run in (desktop, overview):
        assert run["policy_version"] == "journal-policy-5"
        assert run["implementation_sha256"] == assessment["implementation_sha256"]
    valid = sum(row["statusCode"] == 200 for row in desktop["journals"])
    paths = [(desktop, "Desktop", desktop_name), (overview, "Overview", overview_name)]
    lines = [
        "# Video Test Results", "",
        "Actual inputs and full responses from the new [desktop walkthrough](walkthrough-desktop.mp4)",
        "and [overview](walkthrough-short.mp4), both on frozen policy 5. Mobile is not part of this submission walkthrough.", "",
        "Inputs are AI-assisted self-test/development cases with predicted expectations, not ground truth.",
        "These rerecorded, already-seen inputs are not new independent evaluation evidence.",
        "Every journal starts real local generation; verification can select an extractive fallback.",
        "Confidence is uncalibrated, capped at 0.99, and does not score risk or summary correctness.", "",
        "**Known fresh misses remain:** W2 returned MEDIUM and W3 LOW instead of predicted HIGH.",
        "The [once-only fresh report](../reports/UNSEEN_HOPELESSNESS_8.md) is unchanged; there was no inference tuning.", "",
        "## Coverage", "", "| Recording | Policy | Journal responses | PDF questions | Duration |",
        "| --- | --- | --- | --- | --- |",
        f"| Desktop | 5 | {valid}/{len(desktop['journals'])} valid | 2 answered, 1 partial, 2 abstentions | {desktop['videoDurationSeconds']:.2f} s |",
        f"| Overview | 5 | {len(overview['journals'])} repeated inputs | 1 answered, 1 abstention | {overview['videoDurationSeconds']:.2f} s |", "",
        "Desktop covers 13 distinct inputs, including J17 and the complete 512-word development journal.",
        "Overview repeats J1/J2. Each recording uses its own fresh HTTP 201 READY handbook upload.",
        "All processing waits and result-reading holds remain at normal speed with permanently embedded captions.", "",
    ]
    for run, name, source in paths:
        lines += run_section(run, name, source)
    lines += ["## Historical Evidence", "",
              "The [original policy-4 video/results](https://github.com/tusharg007/mymanah-journal-intelligence/tree/submission-v1/docs)",
              "and [original raw desktop/mobile capture](../reports/walkthrough-recording.json) remain preserved.",
              "Historical values were not rewritten as current responses. The old mobile file was not re-recorded.",
              "See the [evidence ledger](EVIDENCE.md) for evaluation stage boundaries.", "",
              "Regenerate this report with `python scripts/export_video_results.py`.", ""]
    (ROOT / "docs/VIDEO_TEST_RESULTS.md").write_text("\n".join(lines), encoding="utf8")
    print("Wrote docs/VIDEO_TEST_RESULTS.md")


if __name__ == "__main__":
    main()
