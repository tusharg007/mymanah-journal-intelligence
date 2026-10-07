"""Real PDF ingestion, retrieval, generation and evidence verification measurements."""
from __future__ import annotations

import asyncio
import hashlib
import json
import re
import time
from dataclasses import replace

from mymanah.config import ROOT
from mymanah.documents import Documents
from mymanah.rag import RAG
from mymanah.storage import Storage
from tests.pdf_helpers import make_pdf


def contains(text, fragment):
    return bool(re.search(r"(?<!\w)" + re.escape(fragment) + r"(?!\w)", text, re.I))


async def run(models, output):
    fixture = json.loads((ROOT / "evals/rag_cases.json").read_text())
    directory = ROOT / "tmp" / ("rag-eval-" + str(time.time_ns()))
    directory.mkdir(parents=True)
    settings = replace(models.settings, data_dir=directory)
    storage = Storage(directory / "metadata.sqlite3", settings.global_disk_bytes)
    documents = Documents(settings, storage, models)
    pdf = make_pdf(directory / "fixture.upload", fixture["pages"])
    digest = hashlib.sha256(pdf.read_bytes()).hexdigest()
    start = time.perf_counter()
    record, _ = await documents.upload(pdf, "evaluation", "aster-policy.pdf", digest, time.monotonic() + 60)
    upload_seconds = time.perf_counter() - start
    rag = RAG(documents, storage, models)
    rows = []
    for case in fixture["cases"]:
        row = {"id": case["id"], "expected": case}
        start = time.perf_counter()
        try:
            retrieved = await asyncio.to_thread(rag.retrieve, record, case["question"])
            row["retrieved_pages"] = [c["page"] for c in retrieved]
            row["retrieval_hit"] = set(case["pages"]).issubset(row["retrieved_pages"]) if case["pages"] else None
            result = await rag.answer(record["id"], "evaluation", case["question"])
            row["actual"] = result.model_dump()
            row["success"] = True
            cited = {c.page for c in result.citations}
            row["matches_expected"] = (
                result.status == case["status"] and set(case["pages"]).issubset(cited)
                and all(contains(result.answer, fragment) for fragment in case["contains"])
                and not any(contains(result.answer, fragment) for fragment in case.get("forbidden", []))
                and (bool(result.citations) if case["pages"] else not result.citations)
            )
        except Exception as exc:
            row.update(success=False, matches_expected=False, error=getattr(exc, "code", type(exc).__name__))
        row["seconds"] = time.perf_counter() - start
        rows.append(row)
        print(f"{case['id']}: success={row['success']} expected_match={row['matches_expected']} seconds={row['seconds']:.2f}", flush=True)
    report = {"generator": models.settings.generator, "models": models.manifest,
              "interpretation": "30 synthetic questions, provisional automated exact-fragment/page checks; human factuality review still required",
              "upload": {"seconds": upload_seconds, "pages": record["pages"], "chunks": record["chunks"], "state": record["state"]},
              "count": len(rows), "successful_service_responses": sum(r["success"] for r in rows),
              "expected_matches": sum(r["matches_expected"] for r in rows),
              "retrieval": {"hits": sum(r.get("retrieval_hit") is True for r in rows),
                            "eligible": sum(bool(r["expected"]["pages"]) for r in rows)},
              "cases": rows}
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    # Chroma owns open SQLite handles until process exit; keep evaluation data isolated.
    return report
