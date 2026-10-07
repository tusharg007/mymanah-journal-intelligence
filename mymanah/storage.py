from __future__ import annotations

import json
import sqlite3
import threading
import time
from contextlib import contextmanager
from pathlib import Path

from .errors import ServiceError

SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_version(version INTEGER PRIMARY KEY);
INSERT OR IGNORE INTO schema_version VALUES(1);
CREATE TABLE IF NOT EXISTS documents(
 id TEXT PRIMARY KEY, owner TEXT NOT NULL, content_hash TEXT NOT NULL, pipeline TEXT NOT NULL,
 filename TEXT NOT NULL, state TEXT NOT NULL, generation TEXT NOT NULL,
 bytes INTEGER NOT NULL, reserved INTEGER NOT NULL, pages INTEGER NOT NULL DEFAULT 0,
 chunks INTEGER NOT NULL DEFAULT 0, created REAL NOT NULL, error TEXT,
 UNIQUE(owner,content_hash,pipeline));
CREATE TABLE IF NOT EXISTS chunks(
 id TEXT PRIMARY KEY, document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
 page INTEGER NOT NULL, ordinal INTEGER NOT NULL, text TEXT NOT NULL, start INTEGER NOT NULL,
 end INTEGER NOT NULL, generation TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS chunk_document ON chunks(document_id);
"""


class Storage:
    def __init__(self, path: Path, disk_limit: int):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path, self.disk_limit = path, disk_limit
        self.lock = threading.RLock()
        with self.connect() as db:
            db.executescript(SCHEMA)

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=5)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA journal_mode=WAL")
        try:
            with db:
                yield db
        finally:
            db.close()

    def get(self, document_id: str, owner: str, ready: bool = False) -> dict:
        with self.connect() as db:
            row = db.execute("SELECT * FROM documents WHERE id=? AND owner=? AND state!='DELETED'", (document_id, owner)).fetchone()
        if row is None:
            raise ServiceError("DOCUMENT_NOT_FOUND", "Document not found", 404)
        result = dict(row)
        if ready and result["state"] != "READY":
            raise ServiceError("DOCUMENT_UNAVAILABLE", "Document is unavailable", 409)
        return result

    def list(self, owner: str) -> list[dict]:
        with self.connect() as db:
            return [dict(row) for row in db.execute("SELECT * FROM documents WHERE owner=? AND state!='DELETED' ORDER BY created DESC", (owner,))]

    def by_hash(self, owner: str, digest: str, pipeline: str) -> dict | None:
        with self.connect() as db:
            row = db.execute("SELECT * FROM documents WHERE owner=? AND content_hash=? AND pipeline=?", (owner, digest, pipeline)).fetchone()
        return dict(row) if row else None

    def reserve(self, document: dict) -> None:
        with self.lock, self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            rows = db.execute("SELECT owner, reserved FROM documents WHERE state NOT IN ('DELETED','FAILED')").fetchall()
            owned = [row for row in rows if row["owner"] == document["owner"]]
            if len(owned) >= 20 or sum(r["reserved"] for r in owned) + document["reserved"] > 500 * 1024**2:
                raise ServiceError("STORAGE_QUOTA", "Document storage quota exceeded", 413)
            if sum(r["reserved"] for r in rows) + document["reserved"] > self.disk_limit:
                raise ServiceError("STORAGE_QUOTA", "Global storage quota exceeded", 413)
            db.execute("INSERT INTO documents(id,owner,content_hash,pipeline,filename,state,generation,bytes,reserved,created) VALUES(?,?,?,?,?,'INGESTING',?,?,?,?)",
                       (document["id"], document["owner"], document["content_hash"], document["pipeline"], document["filename"],
                        document["generation"], document["bytes"], document["reserved"], time.time()))

    def write_chunks(self, document_id: str, chunks: list[dict]) -> None:
        with self.connect() as db:
            db.executemany("INSERT INTO chunks(id,document_id,page,ordinal,text,start,end,generation) VALUES(?,?,?,?,?,?,?,?)",
                           [(c["id"], document_id, c["page"], c["ordinal"], c["text"], c["start"], c["end"], c["generation"]) for c in chunks])

    def publish(self, document_id: str, generation: str, pages: int, chunks: int) -> None:
        with self.lock, self.connect() as db:
            changed = db.execute("UPDATE documents SET state='READY',pages=?,chunks=?,error=NULL WHERE id=? AND generation=? AND state='INGESTING'",
                                 (pages, chunks, document_id, generation)).rowcount
            if changed != 1:
                raise ServiceError("INGESTION_CANCELLED", "Upload can no longer be published", 504)

    def fail(self, document_id: str, code: str) -> None:
        with self.lock, self.connect() as db:
            db.execute("UPDATE documents SET state='FAILED',error=? WHERE id=? AND state='INGESTING'", (code, document_id))

    def release_failed(self, document_id: str) -> None:
        with self.connect() as db:
            db.execute("DELETE FROM chunks WHERE document_id=?", (document_id,))
            db.execute("UPDATE documents SET reserved=0 WHERE id=? AND state='FAILED'", (document_id,))

    def forget_failed(self, document_id: str) -> None:
        with self.connect() as db:
            db.execute("DELETE FROM documents WHERE id=? AND state IN ('FAILED','DELETED') AND reserved=0", (document_id,))

    def canonical(self, document_id: str) -> list[dict]:
        with self.connect() as db:
            return [dict(row) for row in db.execute("SELECT * FROM chunks WHERE document_id=? ORDER BY ordinal", (document_id,))]

    def mark_deleting(self, document_id: str, owner: str) -> dict:
        with self.lock:
            document = self.get(document_id, owner)
            with self.connect() as db:
                db.execute("UPDATE documents SET state='DELETING' WHERE id=?", (document_id,))
            return document

    def finish_delete(self, document_id: str) -> None:
        with self.connect() as db:
            db.execute("DELETE FROM chunks WHERE document_id=?", (document_id,))
            db.execute("UPDATE documents SET state='DELETED',reserved=0 WHERE id=?", (document_id,))

    def interrupted(self) -> list[dict]:
        with self.connect() as db:
            return [dict(row) for row in db.execute("SELECT * FROM documents WHERE state IN ('INGESTING','FAILED','DELETING')")]


def public_document(document: dict) -> dict:
    return {key: document[key] for key in ("id", "filename", "state", "pages", "chunks", "created", "error")}


def pipeline_id(embedding_revision: str) -> str:
    return json.dumps({"parser": "pypdf-v1", "chunker": "page-token320-overlap48-v1", "embedding": embedding_revision}, sort_keys=True)
