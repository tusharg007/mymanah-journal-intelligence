"""Run the user's ten unchanged entries once, saving every response without retries."""
from __future__ import annotations

import hashlib
import json
import math
import statistics
import time
from datetime import datetime, timezone

import httpx

from mymanah.config import ROOT
from mymanah.policy import POLICY_VERSION
from mymanah.schemas import JournalResponse


def fingerprint():
    return {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted((ROOT / "mymanah").glob("*.py"))}


def main():
    inputs = ROOT / "evals/unseen-review-10.json"
    cases = json.loads(inputs.read_text(encoding="utf8"))
    output = ROOT / "reports/unseen-review-10.json"
    report = {"scope": "Ten user-supplied unseen inputs, one unchanged run with no retries or tuning on results",
              "policy_version": POLICY_VERSION, "started_utc": datetime.now(timezone.utc).isoformat(),
              "input_sha256": hashlib.sha256(inputs.read_bytes()).hexdigest(),
              "implementation_sha256": fingerprint(), "cases": []}
    with httpx.Client(base_url="http://127.0.0.1:8000", timeout=75, trust_env=False) as client:
        assert client.get("/health/ready").status_code == 200
        # Exclusive creation prevents inadvertently running this set again.
        with output.open("x", encoding="utf8") as handle:
            json.dump(report, handle, ensure_ascii=False, indent=2)
        for case in cases:
            log = ROOT / "artifacts/reviewer-pack/api-stderr.log"
            log_start = log.stat().st_size
            start = time.perf_counter_ns()
            try:
                response = client.post("/analyze-journal", json={"text": case["text"]})
                row = {**case, "http_status": response.status_code, "actual": response.json()}
            except httpx.HTTPError as exc:
                row = {**case, "http_status": None, "transport_error": type(exc).__name__}
            row["elapsed_ns"] = time.perf_counter_ns() - start
            row["seconds"] = row["elapsed_ns"] / 1_000_000_000
            with log.open("rb") as handle:
                handle.seek(log_start)
                row["inference_observations"] = [line for line in handle.read().decode("utf8", errors="replace").splitlines()
                                                 if "Local generation completed" in line or "Journal summary path=" in line
                                                 or "Journal confidence source=" in line]
            if row["http_status"] == 200:
                actual = row["actual"]
                JournalResponse.model_validate(actual)
                row["label_checks"] = {key: actual[key] in accepted for key, accepted in case["expected"].items()}
                consistency = any("sentiment-consistency" in line for line in row["inference_observations"])
                row["confidence_check"] = {
                    "source": "sentiment-consistency" if consistency else "normalized-emotion",
                    "decision_score_range": 1 / 3 <= actual["confidence"] <= 1 if consistency else 1 / 7 <= actual["confidence"] <= 1,
                    "interpretation": "Score of the selected decision; uncalibrated and does not establish correctness of sentiment, summary or risk"}
                if case["id"] == "U10":
                    row["injection_not_summarized"] = not any(term in actual["summary"].casefold() for term in ["ignore", "instructions", "everything is fine"])
            report["cases"].append(row)
            output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf8")
            print(json.dumps(row, ensure_ascii=True), flush=True)
            time.sleep(max(0, 6.2 - row["seconds"]))
    assert report["implementation_sha256"] == fingerprint(), "Implementation changed during the unseen run"
    valid = [row for row in report["cases"] if row["http_status"] == 200]
    samples = sorted(row["seconds"] for row in valid)
    report["latency"] = {"valid_count": len(samples), "p50_seconds": statistics.median(samples) if samples else None,
                         "p95_nearest_rank_seconds": samples[max(0, math.ceil(.95 * len(samples)) - 1)] if samples else None,
                         "scope": "Warm local sequential ten-input run; small sample, not a production latency guarantee"}
    report["finished_utc"] = datetime.now(timezone.utc).isoformat()
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf8")


if __name__ == "__main__":
    main()
