"""Real persisted-index restore and keyed-access rehearsal using the synthetic browser fixture."""
from __future__ import annotations

import asyncio
import hashlib
import json
import secrets
import time
from dataclasses import replace

import httpx

from mymanah.api import create_app
from mymanah.config import ROOT, Settings
from mymanah.storage import Storage
from scripts.backup import backup, require_stopped, restore


async def main():
    source = Settings.from_env()
    require_stopped(source)
    storage = Storage(source.data_dir / "metadata.sqlite3", source.global_disk_bytes)
    document = next((d for d in storage.list("local")
                     if d["filename"] == "delta-workshop-policy.pdf" and d["state"] == "READY"), None)
    if document is None:
        raise RuntimeError("Run the real browser verification with its synthetic Delta PDF first")
    stamp = str(time.time_ns())
    archive = ROOT / "backups" / ("rehearsal-" + stamp + ".zip")
    destination = ROOT / "tmp" / ("restored-" + stamp)
    backup(source.data_dir, archive)
    restore(archive, destination)
    pdf = document["id"] + ".pdf"
    raw_hash = hashlib.sha256((source.data_dir / "uploads" / pdf).read_bytes()).hexdigest()
    assert hashlib.sha256((destination / "uploads" / pdf).read_bytes()).hexdigest() == raw_hash
    tokens = {name: secrets.token_urlsafe(32) for name in ("local", "other")}
    settings = replace(source, data_dir=destination,
                       keys={name: hashlib.sha256(token.encode()).hexdigest() for name, token in tokens.items()})
    app = create_app(settings)
    async with app.router.lifespan_context(app):
        started = time.monotonic()
        while not app.state.models.ready and time.monotonic() - started < 160:
            await asyncio.sleep(.5)
        app.state.models.require()
        restored = app.state.storage.get(document["id"], "local", ready=True)
        assert restored["generation"] == document["generation"]
        count_before = app.state.documents.collection(restored["generation"]).count()
        assert count_before == document["chunks"]
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app), base_url="http://127.0.0.1:8000", timeout=70) as client:
            path = "/documents/" + document["id"]
            denied = await client.post("/analyze-journal", json={"text": "Today was a normal working day."})
            assert denied.status_code == 401
            other = {"Authorization": "Bearer " + tokens["other"]}
            owner = {"Authorization": "Bearer " + tokens["local"]}
            assert (await client.get(path, headers=other)).status_code == 404
            assert (await client.get(path + "/file", headers=other)).status_code == 404
            preview = await client.get(path + "/file", headers=owner)
            assert preview.status_code == 200 and hashlib.sha256(preview.content).hexdigest() == raw_hash
            answer = await client.post(path + "/questions", headers=owner,
                                       json={"question": "How many annual leave days do Delta workshop employees receive?"})
            assert answer.status_code == 200, answer.text
            result = answer.json()
            assert result["status"] == "ANSWERED" and "18" in result["answer"] and result["citations"]
            assert all(c["document_id"] == document["id"] and c["page"] == 1 for c in result["citations"])
            count_after = app.state.documents.collection(restored["generation"]).count()
            assert count_after == count_before
            report = {"generator": settings.generator, "backup_quiesced": True, "raw_pdf_hash_preserved": True,
                      "generation_preserved": True, "vectors_before": count_before, "vectors_after": count_after,
                      "query_without_reingestion": result, "unauthenticated_journal_status": denied.status_code,
                      "other_principal_metadata_status": 404, "other_principal_pdf_status": 404,
                      "scope": "Real models and restored SQLite/Chroma/PDF data through in-process ASGI API; ephemeral keys are not retained."}
            (ROOT / "reports/backup-restore-smoke.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("Quiesced restore, real persisted-index query, source integrity and keyed owner isolation passed.")


if __name__ == "__main__":
    asyncio.run(main())
