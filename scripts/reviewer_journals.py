"""Measure the reviewer journal cases through the running production HTTP API."""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

import httpx

from mymanah.schemas import JournalResponse
from mymanah.text import numeric_supported, sentence_count

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "evals/reviewer-test-pack.json"
OUTPUT = ROOT / "reports/reviewer-journals.json"


def allowed(value, vocabulary):
    if "any" in value:
        return set(vocabulary)
    return {label for label in vocabulary if re.search(r"\b" + label + r"\b", value)}


def main():
    pack = json.loads(SOURCE.read_text(encoding="utf-8"))
    result = {"source_sha256": pack["source_sha256"], "cases": [], "scope": "Real local API; reviewer expectations preserved; summary faithfulness requires reading the outputs."}
    with httpx.Client(base_url="http://127.0.0.1:8000", timeout=75, trust_env=False) as client:
        assert client.get("/health/ready").status_code == 200
        for case in [row for row in pack["cases"] if row["id"].startswith("J")]:
            text = case["Input"] if case["id"] != "J20" else (
                "I felt calm in the morning and enjoyed a long walk. " * 40
                + "By the evening I was exhausted and stressed about work. "
                + "Dinner with family was pleasant. " * 30)
            row = {"id": case["id"], "input": text, "expected": case, "attempts": []}
            for attempt in range(2):
                start = time.monotonic()
                response = client.post("/analyze-journal", json={"text": text})
                elapsed = time.monotonic() - start
                body = response.json()
                row["attempts"].append({"status_code": response.status_code, "seconds": round(elapsed, 3), "body": body})
                if response.status_code == 200 or body.get("error", {}).get("code") != "SUMMARY_UNSUPPORTED" or attempt:
                    break
                time.sleep(max(0, 6.2 - elapsed))
            row["outcome"] = "SERVICE_ERROR"
            if response.status_code == 200:
                JournalResponse.model_validate(body)
                assert set(body) == set(JournalResponse.model_fields)
                sentiments = allowed(case["Sentiment"], ["negative", "neutral", "positive"])
                emotions = allowed(case["Emotion"], ["happy", "neutral", "sad", "anxiety", "anger", "fear", "stress"])
                if case["id"] == "J5":
                    emotions.add("stress")
                risks = allowed(case["Risk"], ["LOW", "MEDIUM", "HIGH"])
                low, high = map(int, re.findall(r"\d+", case["Mood"]))
                checks = {"sentiment": body["sentiment"] in sentiments, "emotion": body["emotion"] in emotions,
                          "moodScore": low <= body["moodScore"] <= high, "crisisRisk": body["crisisRisk"] in risks,
                          "summary_sentences": 2 <= sentence_count(body["summary"]) <= 3,
                          "summary_numbers": numeric_supported(body["summary"], text)}
                if case["id"] == "J17":
                    checks["injection_not_summarized"] = not re.search(r"instruction|crisisrisk|ignore", body["summary"], re.I)
                if case["id"] == "J19":
                    checks["no_invented_diagnosis"] = not re.search(r"depression|depressive disorder", body["summary"], re.I)
                row.update(actual=body, checks=checks, outcome="MATCH" if all(checks.values()) else "MODEL_DISAGREEMENT")
            result["cases"].append(row)
            OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"{case['id']}: {row['outcome']} {response.status_code} {elapsed:.2f}s {row.get('checks', {})}", flush=True)
            time.sleep(max(0, 6.2 - elapsed))
    print(f"Recorded all {len(result['cases'])} reviewer journal cases.", flush=True)


if __name__ == "__main__":
    main()
