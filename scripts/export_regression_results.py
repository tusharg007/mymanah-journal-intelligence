"""Compile post-correction inputs and actual responses without rewriting old results."""
from __future__ import annotations

import json

from mymanah.config import ROOT


def block(value):
    return ["```json", json.dumps(value, ensure_ascii=False, indent=2), "```", ""]


def main():
    journals = json.loads((ROOT / "reports/journal-policy3-regression.json").read_text(encoding="utf8"))
    cases = journals["cases"]
    pack = [r for r in cases if r["id"].startswith("J")]
    valid = [r for r in pack if r["http_status"] == 200]
    disagreements = [r for r in valid if r["outcome"] == "LABEL_DISAGREEMENT"]
    lines = ["# Journal Policy 3 Regression", "",
             "Workflow: `POST /analyze-journal`. Actual local pinned Hugging Face models and Ollama; CPU NLI uses float32.", "",
             "The 20-case pack is an **AI-assisted self-test pack with predicted expectations** supplied by the candidate.",
             "These predictions are not ground truth. Mood ranges are provisional guesses, not label failures.",
             "The additional cases are development-only; frozen held-out inputs and pre-change results are unchanged.", "",
             f"The 20 pack inputs returned {len(valid)}/20 valid responses and {20 - len(valid)} service errors.",
             f"{len(valid) - len(disagreements)} valid responses agreed with predicted sentiment, emotion and risk; {len(disagreements)} disagreed.",
             "Summary support checks are fallible; label agreement is not a guarantee of summary completeness or clinical safety.", "",
             "| Input | HTTP | Sentiment | Emotion | Mood | Risk | Seconds | Label Comparison |",
             "| --- | ---: | --- | --- | ---: | --- | ---: | --- |"]
    for row in cases:
        actual = row["actual"]
        lines.append(f"| {row['id']} | {row['http_status']} | {actual.get('sentiment', '-')} | {actual.get('emotion', '-')} | {actual.get('moodScore', '-')} | {actual.get('crisisRisk', '-')} | {row['seconds']:.3f} | {row['outcome']} |")
    lines += ["", "## Inputs and Responses", ""]
    for row in cases:
        lines += [f"### {row['id']}", "", "Request:", ""] + block({"text": row["text"]})
        lines += ["Predicted expectations (not ground truth):", ""] + block(row["expected"])
        lines += [f"Actual HTTP {row['http_status']}, {row['seconds']:.3f} seconds:", ""] + block(row["actual"])
        if "mood_within_predicted_range" in row:
            lines += [f"Within provisional mood range: {row['mood_within_predicted_range']}. This is a calibration observation only.", ""]
    lines += ["## Reproduce", "", "```powershell", ".venv\\Scripts\\python.exe -m scripts.journal_regression", ".venv\\Scripts\\python.exe -m scripts.export_regression_results", "```", ""]
    (ROOT / "reports/JOURNAL_POLICY3_REGRESSION.md").write_text("\n".join(lines), encoding="utf8")

    policy = json.loads((ROOT / "reports/policy-condition-regression.json").read_text(encoding="utf8"))
    lines = ["# Policy Condition Regression", "", "Workflow: fresh `POST /documents`, then document-scoped question answering.", "",
             "This is a targeted post-change check, not a full rerun of the 76-case pack. The pack is an AI-assisted self-test pack with predicted expectations, not independent ground truth.", "",
             "After original claim/citation verification, qualified-policy answers preserve the complete cited policy sentence. Conditions outside that quote can still be missed. Original observations remain in `reviewer-protocol.json`.", "",
             "## Fresh Upload", ""] + block(policy["upload"])
    for row in policy["cases"]:
        lines += [f"## {row['id']}", "", "Question request:", ""] + block({"question": row["question"]})
        lines += ["Predicted expectation:", ""] + block(row["predicted_expectation"])
        lines += ["Actual response and latency:", ""] + block(row["actual"])
        lines += ["Checks:", ""] + block(row["checks"])
    lines += ["## Reproduce", "", "```powershell", ".venv\\Scripts\\python.exe -m scripts.policy_condition_regression", "```", ""]
    (ROOT / "reports/POLICY_CONDITION_REGRESSION.md").write_text("\n".join(lines), encoding="utf8")


if __name__ == "__main__":
    main()
