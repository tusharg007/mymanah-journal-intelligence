"""Measured local model comparison, never a generated or assumed evaluation report."""
from __future__ import annotations

import argparse
import asyncio
import json
import math
import time
from dataclasses import replace
from importlib.metadata import version
from pathlib import Path

import numpy as np
from sklearn.metrics import classification_report, confusion_matrix

from mymanah.config import ROOT, Settings
from mymanah.journal import JournalService
from mymanah.models import Models
from mymanah.policy import POLICY_VERSION, distribution
from mymanah.text import windows


def nli_sentiment(models: Models, text: str) -> str:
    labels = ["negative", "neutral", "positive"]
    hypotheses = ["The writer expresses negative sentiment.", "The writer expresses neutral sentiment.", "The writer expresses positive sentiment."]
    pieces = windows(text, models.nli_tokenizer)
    raw = models.support([(piece.text, h) for piece in pieces for h in hypotheses])
    totals = [0.0] * 3
    for i, piece in enumerate(pieces):
        scores = distribution(raw[i * 3:(i + 1) * 3])
        for j, score in enumerate(scores):
            totals[j] += score * piece.weight
    return labels[int(np.argmax(totals))]


def proportion(correct: int, total: int) -> dict:
    z = 1.959963984540054
    p = correct / total
    scale = 1 + z * z / total
    center = (p + z * z / (2 * total)) / scale
    half = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / scale
    return {"correct": correct, "total": total, "fraction": p, "wilson_95": [center - half, center + half]}


async def run(args):
    cases = json.loads(args.cases.read_text(encoding="utf-8"))
    models = Models(replace(Settings.from_env(), generator=args.generator))
    loading_started = time.perf_counter()
    await models.load()
    cold_seconds = time.perf_counter() - loading_started
    models.require()
    rows = []
    try:
        service = JournalService(models)
        for case in cases:
            row = {"id": case["id"], "expected": {k: case[k] for k in ("sentiment", "emotion", "crisisRisk")}}
            start = time.perf_counter()
            baseline = await asyncio.to_thread(models.sentiment_scores, case["text"])
            row["roberta"] = max(baseline, key=baseline.get)
            row["roberta_seconds"] = time.perf_counter() - start
            start = time.perf_counter()
            row["nli_sentiment"] = await asyncio.to_thread(nli_sentiment, models, case["text"])
            row["nli_sentiment_seconds"] = time.perf_counter() - start
            start = time.perf_counter()
            try:
                result = await service.analyze(case["text"])
                row["actual"] = result.model_dump()
                row["success"] = True
            except Exception as exc:
                row["success"] = False
                row["error"] = getattr(exc, "code", type(exc).__name__)
            row["journal_seconds"] = time.perf_counter() - start
            rows.append(row)
            print(f"{case['id']}: success={row['success']} seconds={row['journal_seconds']:.2f}", flush=True)
        labels = ["negative", "neutral", "positive"]
        expected = [r["expected"]["sentiment"] for r in rows]
        report = {"split": args.cases.name, "generator": args.generator, "policy": POLICY_VERSION,
                  "packages": {name: version(name) for name in ("torch", "transformers", "sentence-transformers", "chromadb")},
                  "cold_load_seconds": cold_seconds, "torch_threads": models.settings.torch_threads,
                  "count": len(rows), "cases": rows,
                  "models": models.manifest, "interpretation": "Curated engineering cases, not clinical validation or deployment accuracy"}
        for field in ("roberta", "nli_sentiment"):
            actual = [r[field] for r in rows]
            report[field] = {"classification": classification_report(expected, actual, labels=labels, output_dict=True, zero_division=0),
                             "confusion_matrix": confusion_matrix(expected, actual, labels=labels).tolist(), "label_order": labels}
        for field, label_order in (("sentiment", labels),
                                   ("emotion", ["happy", "sad", "anxiety", "stress", "anger", "fear", "neutral"]),
                                   ("crisisRisk", ["LOW", "MEDIUM", "HIGH"])):
            wanted = [row["expected"][field] for row in rows]
            predicted = [row["actual"][field] if row["success"] else "SERVICE_ERROR" for row in rows]
            report["journal_" + field] = {
                "agreement": proportion(sum(a == b for a, b in zip(wanted, predicted, strict=True)), len(rows)),
                "classification": classification_report(wanted, predicted, labels=label_order, output_dict=True, zero_division=0),
                "confusion_matrix": confusion_matrix(wanted, predicted, labels=label_order + ["SERVICE_ERROR"]).tolist(),
                "label_order": label_order + ["SERVICE_ERROR"], "denominator": len(rows),
                "warning": "Service errors count as missed predictions and remain visible; labels are provisional engineering annotations",
            }
        timings = [r["journal_seconds"] for r in rows if r["success"]]
        report["latency"] = {"successful_count": len(timings), "failure_count": len(rows) - len(timings),
                             "p50": float(np.percentile(timings, 50)) if timings else None,
                             "p95": float(np.percentile(timings, 95)) if timings else None}
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
        if args.rag_output:
            from evals.rag_benchmark import run as run_rag
            await run_rag(models, args.rag_output)
    finally:
        await models.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--generator", choices=["qwen4b", "qwen1b"], default="qwen4b")
    parser.add_argument("--cases", type=Path, default=ROOT / "evals" / "development.json")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--rag-output", type=Path)
    asyncio.run(run(parser.parse_args()))
