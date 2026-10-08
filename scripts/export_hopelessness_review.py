"""Publish the single fresh assessment without running inference or tuning."""
from __future__ import annotations

import json

from mymanah.config import ROOT
from scripts.export_policy4_results import block
from scripts.unseen_review import fingerprint


def main():
    data = json.loads((ROOT / "reports/unseen-hopelessness-8.json").read_text(encoding="utf8"))
    assert len(data["cases"]) == 8 and data.get("finished_utc")
    assert data["implementation_sha256"] == fingerprint(), "Inference code changed after the fresh assessment"
    valid = [row for row in data["cases"] if row["http_status"] == 200]
    matching = sum(all(row.get("label_checks", {}).values()) for row in valid)
    lines = ["# Fresh Policy-5 Hopelessness Assessment", "",
             "Workflow: `POST /analyze-journal` with real pinned local models on the tested GPU laptop.", "",
             "Eight AI-assisted inputs supplied by the candidate were run ONCE, unchanged, without request retries. "
             "Predicted expectations are not independently validated clinical ground truth. "
             "There was no tuning on these results. Inference code is now frozen at the source fingerprints below.", "",
             f"Valid responses: {len(valid)}/8. Matching all specified expectations: {matching}/8.",
             "W2 returned MEDIUM and W3 LOW instead of the predicted HIGH. These are retained screening misses.",
             "W4/W5/W7 returned MEDIUM/MEDIUM/LOW, with no false HIGH among the specified context controls.",
             "W8 returned positive/happy/LOW. No claim of broad generalization follows from this eight-input sample.", "",
             "| Case | Predicted Risk | Actual Risk | Sentiment | Emotion | Confidence | Seconds | Specified Expectations Match |",
             "| --- | --- | --- | --- | --- | ---: | ---: | --- |"]
    for row in data["cases"]:
        actual = row.get("actual", {})
        lines.append(f"| {row['id']} | {' / '.join(row['expected']['crisisRisk'])} | {actual.get('crisisRisk', '-')} | "
                     f"{actual.get('sentiment', '-')} | {actual.get('emotion', '-')} | {actual.get('confidence', '-')} | "
                     f"{row['seconds']:.6f} | {all(row.get('label_checks', {}).values()) if row['http_status'] == 200 else 'service error'} |")
    lines += ["", "## Interpretation", "",
              "Confidence is an uncalibrated selected-emotion decision score, capped at 0.99 for presentation. "
              "W2/W3 both have 0.99 sad-emotion confidence, despite their incorrect screening priority. "
              "The score does not establish screening correctness, diagnosis or summary faithfulness.", "",
              "All eight entries initiated real Qwen generation. Six returned generated summaries; W6/W7 used "
              "verified extractive fallbacks after two generation/verification attempts. They are not presented as generated third-person summaries.", "",
              "Additional qualitative limitations: W5's summary uses 'his' without gender evidence. W7 is negative/anger "
              "despite its mundane weather context; the supplied expectation prescribed only LOW risk, not sentiment or emotion. "
              "These outputs remain unchanged, not hidden by the six-of-eight expectation count.", "",
              "## Measured Timing", ""] + block(data["latency"])
    for row in data["cases"]:
        lines += [f"## {row['id']}", "", "Input:", ""] + block({"text": row["text"]})
        lines += ["Predicted expectations:", ""] + block(row["expected"])
        lines += [f"Actual HTTP {row['http_status']}, {row['seconds']:.6f} seconds:", ""] + block(row.get("actual", row.get("transport_error")))
        lines += ["Specified-label checks:", ""] + block(row.get("label_checks", {}))
        lines += ["Confidence interpretation:", ""] + block(row.get("confidence_check", {}))
        lines += ["Actual generation/path metadata:", ""] + block(row.get("inference_observations", []))
    lines += ["## Freeze Record", "",
              "The exporter checks these source-byte fingerprints against the current inference package. "
              "The approved plan, original held-out set and earlier unseen reports are preserved. "
              "Future policy changes require separate revalidation, not rewriting this assessment.", ""]
    lines += block({key: data[key] for key in ("policy_version", "started_utc", "finished_utc", "input_sha256", "implementation_sha256")})
    (ROOT / "reports/UNSEEN_HOPELESSNESS_8.md").write_text("\n".join(lines), encoding="utf8")


if __name__ == "__main__":
    main()
