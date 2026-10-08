"""Compile the final desktop/mobile recording report into reviewer-friendly Markdown."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports/walkthrough-recording.json"
OUTPUT = ROOT / "docs/VIDEO_TEST_RESULTS.md"


def cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", "<br>")


def link(run: dict, title: str) -> str:
    evidence = next(row for row in run["evidence"] if row["title"] == title)
    seconds = evidence["visibleFrom"]
    return f"{int(seconds // 60):02}:{int(seconds % 60):02}"


def expected_labels(value: str) -> set[str]:
    if value.strip().lower() == "any":
        return {"any"}
    items = {re.sub(r"\s+ok$", "", item.strip().lower())
             for item in re.split(r"\s+or\s+|\s*\(|\s*\)", value)}
    return {item for item in items if item and item != "ok"}


def journal_outcome(expected: dict, actual: dict) -> list[str]:
    mismatches = []
    for field, actual_value in (("Sentiment", actual["sentiment"]),
                                ("Emotion", actual["emotion"]), ("Risk", actual["crisisRisk"])):
        labels = expected_labels(expected[field])
        if "any" not in labels and actual_value.lower() not in labels:
            mismatches.append(f"{field}: returned {actual_value}; expected {expected[field]}.")
    low, high = map(int, re.findall(r"\d+", expected["Mood"]))
    if not low <= actual["moodScore"] <= high:
        mismatches.append(f"Mood: returned {actual['moodScore']}; expected {low}-{high}.")
    return mismatches


def main() -> None:
    recordings = json.loads(REPORT.read_text(encoding="utf-8"))
    by_name = {run["name"]: run for run in recordings}
    desktop, mobile = by_name["desktop"], by_name["mobile"]
    lines = [
        "# Video Test Results",
        "",
        "This report compiles the actual model and document responses visible in the",
        "[desktop walkthrough](walkthrough-desktop.mp4) and [mobile walkthrough](walkthrough-mobile.mp4).",
        "Inputs and expected journal labels come from the supplied reviewer pack. Results are",
        "recorded as returned; a valid HTTP response does not mean the expected labels matched.",
        "Confidence is the system's uncalibrated score, not a probability of correctness.",
        "",
        "## Coverage",
        "",
        "| Workflow | Desktop | Mobile |",
        "| --- | ---: | ---: |",
        f"| Journal analysis | {len(desktop['journals'])} inputs | {len(mobile['journals'])} inputs |",
        "| PDF questions | 2 supported, 1 unsupported | 2 supported, 1 unsupported |",
        "| Uploaded document | Fresh upload, READY | Reused indexed document, READY |",
        "",
        "The videos contain 16 journal requests across 11 distinct test inputs: five inputs",
        "are repeated in the mobile workflow. The PDF is the three-page `Employee_Handbook_Test.pdf`.",
        "",
        "## Journal Analysis",
        "",
        "The expected fields below reproduce the test-pack annotations. Actual values and",
        "summaries come from each recorded HTTP 200 response.",
        "",
    ]

    order = [row["id"] for row in desktop["journals"]]
    for case_id in order:
        drow = next(row for row in desktop["journals"] if row["id"] == case_id)
        mrow = next((row for row in mobile["journals"] if row["id"] == case_id), None)
        expected = drow["expected"]
        actual = drow["actual"]
        lines += [
            f"### {case_id}: {drow['title']}",
            "",
            f"> **Input:** {cell(drow['input'])}",
            "",
            "| Field | Expected | Desktop result | Mobile result |",
            "| --- | --- | --- | --- |",
            f"| Sentiment | {cell(expected['Sentiment'])} | {cell(actual['sentiment'])} | {cell(mrow['actual']['sentiment']) if mrow else '-'} |",
            f"| Emotion | {cell(expected['Emotion'])} | {cell(actual['emotion'])} | {cell(mrow['actual']['emotion']) if mrow else '-'} |",
            f"| Mood score | {cell(expected['Mood'])} | {actual['moodScore']}/10 | {mrow['actual']['moodScore']}/10 |" if mrow else f"| Mood score | {cell(expected['Mood'])} | {actual['moodScore']}/10 | - |",
            f"| Crisis risk | {cell(expected['Risk'])} | {cell(actual['crisisRisk'])} | {cell(mrow['actual']['crisisRisk']) if mrow else '-'} |",
            f"| Confidence | Not specified | {actual['confidence']:.4f} | {mrow['actual']['confidence']:.4f} |" if mrow else f"| Confidence | Not specified | {actual['confidence']:.4f} | - |",
            f"| HTTP / latency | HTTP 200 | HTTP 200 / {drow['journalSeconds']:.2f}s | HTTP 200 / {mrow['journalSeconds']:.2f}s |" if mrow else f"| HTTP / latency | HTTP 200 | HTTP 200 / {drow['journalSeconds']:.2f}s | - |",
            "",
            f"**Desktop summary:** {cell(actual['summary'])}",
            "",
        ]
        if mrow:
            lines += [f"**Mobile summary:** {cell(mrow['actual']['summary'])}", ""]
        if expected.get("Notes"):
            lines += [f"**Test note:** {cell(expected['Notes'])}", ""]
        desktop_mismatches = journal_outcome(expected, actual)
        mobile_mismatches = journal_outcome(expected, mrow["actual"]) if mrow else []
        if not desktop_mismatches and (not mrow or not mobile_mismatches):
            qualifier = "Desktop and mobile" if mrow else "Desktop"
            lines += [f"**Expected-label check:** {qualifier} matched the pack's allowed labels and mood range.", ""]
        else:
            lines += ["**Expected-label check:** Disagreement with one or more pack annotations.", ""]
            if desktop_mismatches:
                lines += ["- Desktop: " + " ".join(desktop_mismatches)]
            if mobile_mismatches:
                lines += ["- Mobile: " + " ".join(mobile_mismatches)]
            lines.append("")
        lines.append(f"Video result: desktop {link(desktop, case_id + ' - completed analysis')}; mobile {link(mobile, case_id + ' - completed analysis') if mrow else 'not shown'}.")
        lines.append("")

    lines += [
        "## Document Question Answering",
        "",
        "Both workflows selected the same three-page handbook. Desktop uploaded a fresh",
        "copy and received HTTP 201 with status `READY`, three pages and three chunks.",
        "Mobile reused that indexed document. Both then asked the same three questions.",
        "",
        "| Input question | Workflow | HTTP / status | Actual answer | Citation and source quote | Latency |",
        "| --- | --- | --- | --- | --- | ---: |",
    ]
    for name, run in (("Desktop", desktop), ("Mobile", mobile)):
        for result in run["responses"]:
            citation = result["result"]["citations"][0]
            quote = cell(citation["quote"])
            lines.append(
                f"| {cell(result['question'])} | {name} | HTTP 200 / `{result['result']['status']}` | "
                f"{cell(result['result']['answer'])} | Page {citation['page']}: “{quote}” | {result['seconds']:.2f}s |"
            )
        result = run["unsupported"]
        question = "What is the stock option vesting schedule?"
        lines.append(
            f"| {question} | {name} | HTTP 200 / `{result['status']}` | {cell(result['answer'])} | None (no citations) | - |"
        )
    lines += [
        "",
        "The annual-leave answer gives the 24-day allowance and cites page 2. The answer",
        "does not mention the separate carry-over cap or expiry. The probation answer gives",
        "15 days and cites page 3. The unsupported stock-option question is declined without",
        "citations. These observed answers should be read alongside the full 76-case",
        "[reviewer test-pack report](../reports/REVIEWER_TEST_PACK.md), which includes other",
        "document questions and mismatches.",
        "",
        "## Recording Details",
        "",
        "| Recording | Viewport | Duration | Journal cases |",
        "| --- | ---: | ---: | ---: |",
        f"| Desktop | {desktop['viewport']['width']} x {desktop['viewport']['height']} | {desktop['videoDurationSeconds'] / 60:.2f} min | {len(desktop['journals'])} |",
        f"| Mobile | {mobile['viewport']['width']} x {mobile['viewport']['height']} | {mobile['videoDurationSeconds'] / 60:.2f} min | {len(mobile['journals'])} |",
        "",
        "Journal processing ran at normal playback speed. Completed results remain visible",
        "for reading; captions are embedded in the video. The raw response payloads, expected",
        "annotations, exact timestamps and per-request timings are in",
        "[`walkthrough-recording.json`](../reports/walkthrough-recording.json).",
        "",
    ]
    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
