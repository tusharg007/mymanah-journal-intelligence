"""Post-hoc selected-score diagnostics; never fit calibration on the held-out split."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from evals.benchmark import proportion


def summarize(report: dict) -> dict:
    successful = [row for row in report["cases"] if row["success"]]
    edges = [0, .5, .7, .8, .9, .95, 1.00001]
    bins = []
    for lower, upper in zip(edges[:-1], edges[1:], strict=True):
        rows = [row for row in successful if lower <= row["actual"]["confidence"] < upper]
        matched = sum(all(row["actual"][field] == row["expected"][field]
                          for field in ("sentiment", "emotion")) for row in rows)
        bins.append({"lower_inclusive": lower, "upper_bound": min(upper, 1), "upper_inclusive": upper > 1, "count": len(rows),
                     "mean_selected_score": sum(row["actual"]["confidence"] for row in rows) / len(rows) if rows else None,
                     "joint_sentiment_emotion_agreement": proportion(matched, len(rows)) if rows else None})
    return {"split": report["split"], "total": len(report["cases"]), "validated_responses": len(successful),
            "service_errors_excluded_from_bins": len(report["cases"]) - len(successful), "bins": bins,
            "interpretation": "Returned confidence is the uncalibrated minimum selected sentiment/emotion score. Bins compare joint label agreement on provisional synthetic annotations, not correctness of summary, risk or every field. Small counts cannot establish calibration; no fitting was performed.",
            "brier_score": None,
            "brier_limitation": "Per-class probability vectors were not retained. Do not invent task-wise Brier scores from a minimum-selected-score heuristic."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.write_text(json.dumps(summarize(json.loads(args.input.read_text())), indent=2), encoding="utf-8")
    print("Recorded selected-score bins without tuning the held-out model or labels.")
