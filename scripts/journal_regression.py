"""Measure journal policy changes against development and AI-assisted self-test inputs."""
from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path

import httpx

from mymanah.config import ROOT
from mymanah.policy import POLICY_VERSION
from mymanah.schemas import JournalResponse
from mymanah.text import numeric_supported, sentence_count
from scripts.reviewer_journals import allowed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", nargs="*")
    parser.add_argument("--output", default="reports/journal-policy3-regression.json")
    args = parser.parse_args()
    pack = json.loads((ROOT / "evals/reviewer-test-pack.json").read_text(encoding="utf8"))
    original = json.loads((ROOT / "reports/reviewer-journals.json").read_text(encoding="utf8"))
    inputs = {row["id"]: row["input"] for row in original["cases"]}
    rows = [{"id": row["id"], "text": inputs[row["id"]],
             "expected": {key: row[key] for key in ("Sentiment", "Emotion", "Mood", "Risk")}}
            for row in pack["cases"] if row["id"].startswith("J")]
    development = json.loads((ROOT / "evals/development.json").read_text(encoding="utf8"))
    rows += [{"id": row["id"], "text": row["text"], "expected": {
        "Sentiment": row["sentiment"], "Emotion": row["emotion"], "Risk": row["crisisRisk"]}}
             for row in development if int(row["id"][3:]) > 50]
    rows.append({"id": "long01", "text": (ROOT / "evals/long-journal-development.txt").read_text(encoding="utf8"),
                 "expected": {"Sentiment": "positive", "Emotion": "happy", "Risk": "LOW"}})
    if args.cases:
        lookup = {row["id"]: row for row in rows}
        rows = [lookup[key] for key in args.cases]
    report = {"policy_version": POLICY_VERSION, "scope": "Post-change development regression; AI-assisted predicted expectations, not ground truth; mood guesses reported separately", "cases": []}
    output = ROOT / Path(args.output)
    with httpx.Client(base_url="http://127.0.0.1:8000", timeout=75, trust_env=False) as client:
        assert client.get("/health/ready").status_code == 200
        for case in rows:
            start = time.monotonic()
            response = client.post("/analyze-journal", json={"text": case["text"]})
            elapsed = time.monotonic() - start
            body = response.json()
            row = {**case, "http_status": response.status_code, "seconds": round(elapsed, 3), "actual": body}
            if response.status_code == 200:
                JournalResponse.model_validate(body)
                checks = {}
                for key, field, vocabulary in (("Sentiment", "sentiment", ["positive", "neutral", "negative"]),
                                               ("Emotion", "emotion", ["happy", "sad", "stress", "anxiety", "fear", "anger", "neutral"]),
                                               ("Risk", "crisisRisk", ["LOW", "MEDIUM", "HIGH"])):
                    accepted = allowed(case["expected"][key], vocabulary)
                    if case["id"] == "J5" and key == "Emotion":
                        accepted.add("stress")
                    checks[field] = body[field] in accepted
                row["label_checks"] = checks
                summary_checks = {"sentence_count": 2 <= sentence_count(body["summary"]) <= 3,
                                  "numbers_supported": numeric_supported(body["summary"], case["text"])}
                if case["id"] == "J17":
                    summary_checks["injection_not_summarized"] = not re.search(r"instruction|crisisrisk|ignore", body["summary"], re.I)
                if case["id"] == "J19":
                    summary_checks["no_invented_diagnosis"] = not re.search(r"depression|depressive disorder", body["summary"], re.I)
                row["summary_checks"] = summary_checks
                row["outcome"] = "LABELS_MATCH_PREDICTIONS" if all(checks.values()) else "LABEL_DISAGREEMENT"
                if not all(summary_checks.values()):
                    row["outcome"] = "SUMMARY_CHECK_FAILURE"
                if "Mood" in case["expected"]:
                    low, high = map(int, re.findall(r"\d+", case["expected"]["Mood"]))
                    row["mood_within_predicted_range"] = low <= body["moodScore"] <= high
            else:
                row["outcome"] = "SERVICE_ERROR"
            report["cases"].append(row)
            output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf8")
            print(json.dumps(row, ensure_ascii=True), flush=True)
            time.sleep(max(0, 6.2 - elapsed))


if __name__ == "__main__":
    main()
