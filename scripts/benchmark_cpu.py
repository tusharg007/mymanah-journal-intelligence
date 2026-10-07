"""Measure downloaded CPU classifiers independently of generator availability."""
import asyncio
import json
import time

from sklearn.metrics import classification_report

from evals.benchmark import nli_sentiment
from mymanah.config import ROOT, Settings
from mymanah.journal import JournalService
from mymanah.models import Models


async def main():
    models = Models(Settings.from_env())
    try:
        await asyncio.to_thread(models.load_cpu)
        cases = json.loads((ROOT / "evals" / "development.json").read_text())
        rows = []
        journal = JournalService(models)
        for case in cases:
            start = time.perf_counter()
            result = await asyncio.to_thread(journal.classify, case["text"])
            seconds = time.perf_counter() - start
            start = time.perf_counter()
            nli = await asyncio.to_thread(nli_sentiment, models, case["text"])
            nli_seconds = time.perf_counter() - start
            row = {"id": case["id"], "expected": case,
                   "sentiment": max(result["sentiment"], key=result["sentiment"].get),
                   "emotion": max(result["emotion"], key=result["emotion"].get),
                   "crisisRisk": result["risk"], "classification_seconds": seconds,
                   "nli_sentiment": nli, "nli_sentiment_seconds": nli_seconds}
            rows.append(row)
            print(f"{row['id']}: {row['sentiment']} {row['emotion']} {row['crisisRisk']} {seconds:.2f}s", flush=True)
        report = {"scope": "CPU classification only; not end-to-end API or generator validation",
                  "split": "development", "count": len(rows), "cases": rows}
        for field in ("sentiment", "emotion", "crisisRisk"):
            report[field] = classification_report([r["expected"][field] for r in rows], [r[field] for r in rows],
                                                  output_dict=True, zero_division=0)
        report["nli_sentiment"] = classification_report([r["expected"]["sentiment"] for r in rows],
                                                        [r["nli_sentiment"] for r in rows], output_dict=True, zero_division=0)
        target = ROOT / "reports" / "cpu-development.json"
        target.parent.mkdir(exist_ok=True)
        target.write_text(json.dumps(report, indent=2), encoding="utf-8")
    finally:
        await models.close()


if __name__ == "__main__":
    asyncio.run(main())
