"""Compile measured final development results while preserving original assessments."""
from __future__ import annotations

import json

from mymanah.config import ROOT
from scripts.export_policy4_results import block, journal_report, metrics


def main():
    data = json.loads((ROOT / "reports/journal-policy5-regression.json").read_text(encoding="utf8"))
    diagnostic = json.loads((ROOT / "reports/policy4-hopelessness-diagnostic.json").read_text(encoding="utf8"))
    assert data["policy_version"] == "journal-policy-5" and len(data["cases"]) == 30
    text = journal_report(data).replace("Journal Policy 4 Regression", "Journal Policy 5 Seen Regression", 1)
    text = text.replace(
        "These 20 self-test inputs, four J1 regressions and the 512-word entry are development cases; original reports and the frozen held-out set are preserved.",
        "These 20 self-test inputs, four J1 regressions, the 512-word entry and U6-U10 are SEEN development cases. "
        "The original AI-assisted ten-input assessment ran once before tuning; its reports and the frozen held-out set remain unchanged. "
        "The requested follow-up uses U6/U10 to correct risk and U7-U9 as controls, not to claim generalization.", 1)
    text = text.replace("## Current Latency", "## Current Latency on the Tested GPU Laptop", 1)
    text = text.replace(
        "Neither score is calibrated or covers screening risk or summary correctness.",
        "Policy 5 caps either score at 0.99 for presentation only. Neither score is calibrated or covers screening risk or summary correctness.", 1)
    by_id = {row["id"]: row for row in data["cases"]}
    for row in data["cases"]:
        if row["http_status"] == 200:
            assert row["actual"]["confidence"] <= .99
    for key, risk in {"U6": "HIGH", "U10": "HIGH", "U7": "LOW", "U8": "LOW", "U9": "MEDIUM",
                      "J1": "HIGH"}.items():
        assert by_id[key]["actual"]["crisisRisk"] == risk
    for key in ("J5", "J6", "J7", "J14"):
        assert by_id[key]["actual"]["crisisRisk"] != "HIGH"
    lines = ["", "## Pre-Change Signal Diagnostic", "",
             "The old rule used max(distress) >= 0.65; it did not require persistence and impairment together.",
             "U6/U10 exceeded 0.65 hopelessness but reached only 0.628/0.572 overwhelm, explaining their MEDIUM outputs.",
             "The requested NLI path now accepts hopelessness >= 0.65 with overwhelm >= 0.50, or persistence/impairment >= 0.65. The existing lexical path is retained.", "",
             "Four signal columns: own-life intent, immediate danger, unable to cope, hopelessness.",
             "Three distress columns: overwhelm, persistence, impairment. Full precision is preserved below.", ""]
    lines += block(diagnostic)
    lines += ["## Final Review", "",
              "U6/U10 now return HIGH. U7/U8/U9 retain LOW/LOW/MEDIUM. J5/J6/J7/J14 do not escalate to HIGH.",
              "U6 still returns anger rather than predicted sad. J14 remains a figurative-emotion disagreement. These are model errors, not fixed by the risk threshold.",
              "All 25 original policy-4 development cases retain their risk labels, including J11 at HIGH (the pack permits MEDIUM or HIGH). Only the two previously missed seen inputs change to HIGH.",
              "All cases here are synthetic development/self-test aids, not independently validated risk labels. A fresh unseen set is required for new generalization claims.",
              "Confidence clipping reduces displayed certainty but cannot fix misclassification or validate confidence calibration.",
              "CPU-only timings are not measured by this run. Historical CPU journal smoke took 19.69 seconds; long entries can hit the 60-second deadline.", "",
              "All current valid-request timing observations:", ""] + block(metrics(data["cases"]))
    followup = json.loads((ROOT / "reports/policy5-summary-followup.json").read_text(encoding="utf8"))
    lines += ["## J12 Summary Follow-Up", "",
              "The first 30-case run above reproduced J12's abstract emotional-state wording. It remains preserved in the raw report.",
              "A narrow verification check now sends positive/negative emotional-state filler through the existing single-repair path. This is an additional seen-input style check, not another unseen assessment or a rewrite of the original measurement.", ""] + block(followup)
    (ROOT / "reports/JOURNAL_POLICY5_REGRESSION.md").write_text(text + "\n" + "\n".join(lines), encoding="utf8")
    print(json.dumps({"cases": len(data["cases"]), "timings": metrics(data["cases"])}))


if __name__ == "__main__":
    main()
