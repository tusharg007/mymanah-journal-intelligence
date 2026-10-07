from __future__ import annotations

import asyncio
import json
import shutil
import subprocess
import sys
import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from .config import ROOT, Settings
from .errors import ServiceError
from .storage import Storage, pipeline_id
from .text import english_only


@dataclass
class Flight:
    abort: threading.Event = field(default_factory=threading.Event)
    document_id: str | None = None
    task: asyncio.Task | None = None


class Documents:
    def __init__(self, settings: Settings, storage: Storage, models):
        import chromadb
        from chromadb.config import Settings as ChromaSettings

        self.settings, self.storage, self.models = settings, storage, models
        self.raw = settings.data_dir / "uploads"
        self.raw.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(str(settings.data_dir / "chroma"),
                                               settings=ChromaSettings(anonymized_telemetry=False))
        self.pipeline = pipeline_id(models.manifest["embedding"]["revision"])
        self.lane = threading.Lock()
        self.flights: dict[tuple[str, str, str], Flight] = {}

    @staticmethod
    def collection_name(generation: str) -> str:
        return "doc_" + generation

    def collection(self, generation: str):
        return self.client.get_collection(self.collection_name(generation), embedding_function=None)

    def remove_artifacts(self, document: dict) -> None:
        name = self.collection_name(document["generation"])
        existing = {c.name for c in self.client.list_collections()}
        if name in existing:
            self.client.delete_collection(name)
        (self.raw / (document["id"] + ".pdf")).unlink(missing_ok=True)

    def recover(self) -> None:
        for document in self.storage.interrupted():
            if document["state"] == "DELETING":
                self.remove_artifacts(document)
                self.storage.finish_delete(document["id"])
            else:
                self.storage.fail(document["id"], "INGESTION_INTERRUPTED")
                self.remove_artifacts(document)
                self.storage.release_failed(document["id"])
        with self.storage.connect() as db:
            active = {self.collection_name(row[0]) for row in db.execute("SELECT generation FROM documents WHERE state='READY'")}
            file_ids = {row[0] for row in db.execute("SELECT id FROM documents WHERE state='READY'")}
        for collection in self.client.list_collections():
            if collection.name.startswith("doc_") and collection.name not in active:
                self.client.delete_collection(collection.name)
        for file in self.raw.glob("*.pdf"):
            if file.stem not in file_ids:
                file.unlink()
        temporary = self.settings.data_dir / "temporary"
        if temporary.exists():
            for file in temporary.glob("*.upload"):
                file.unlink()

    def check(self, flight: Flight, deadline: float) -> None:
        if flight.abort.is_set() or time.monotonic() >= deadline:
            raise ServiceError("INGESTION_TIMEOUT", "Upload exceeded its deadline", 504)

    def chunk(self, pages: list[str], generation: str) -> list[dict]:
        tokenizer = self.models.embedding.tokenizer
        chunks = []
        for page, text in enumerate(pages, 1):
            if not text.strip():
                continue
            english_only(text)
            offsets = tokenizer(text, add_special_tokens=False, return_offsets_mapping=True)["offset_mapping"]
            offsets = [(a, b) for a, b in offsets if b > a]
            start = 0
            while start < len(offsets):
                end = min(start + 320, len(offsets))
                a, b = offsets[start][0], offsets[end - 1][1]
                content = text[a:b]
                if len(tokenizer.encode("passage: " + content)) > 512:
                    raise ServiceError("CHUNK_TOKEN_LIMIT", "A document chunk exceeds embedding capacity", 422)
                chunks.append({"id": generation + "_" + str(len(chunks)), "page": page,
                               "ordinal": len(chunks), "text": content, "start": a, "end": b,
                               "generation": generation})
                if len(chunks) > 5000:
                    raise ServiceError("CHUNK_LIMIT", "Document exceeds 5000 chunks", 413)
                if end == len(offsets):
                    break
                start = end - 48
        if not chunks:
            raise ServiceError("NO_EXTRACTABLE_TEXT", "The PDF has no usable text", 422)
        return chunks

    def ingest(self, file: Path, owner: str, filename: str, digest: str, flight: Flight, deadline: float) -> tuple[dict, bool]:
        document = None
        try:
            remaining = deadline - time.monotonic()
            if remaining <= 0 or not self.lane.acquire(timeout=remaining):
                raise ServiceError("INGESTION_TIMEOUT", "Upload admission timed out", 504)
            try:
                self.check(flight, deadline)
                existing = self.storage.by_hash(owner, digest, self.pipeline)
                if existing and existing["state"] == "READY":
                    return existing, False
                if existing:
                    self.remove_artifacts(existing)
                    self.storage.release_failed(existing["id"])
                    self.storage.forget_failed(existing["id"])
                size = file.stat().st_size
                reserve = size + 24 * 1024**2
                physical = sum(p.stat().st_size for p in self.settings.data_dir.rglob("*") if p.is_file())
                if physical + reserve > self.settings.global_disk_bytes:
                    raise ServiceError("STORAGE_QUOTA", "Global disk quota exceeded", 413)
                if shutil.disk_usage(self.settings.data_dir).free < reserve * 2:
                    raise ServiceError("DISK_FULL", "Insufficient disk space for ingestion", 503)
                document = {"id": uuid.uuid4().hex, "owner": owner, "content_hash": digest,
                            "pipeline": self.pipeline, "filename": filename, "generation": uuid.uuid4().hex,
                            "bytes": size, "reserved": reserve}
                self.storage.reserve(document)
                flight.document_id = document["id"]
                shutil.move(str(file), str(self.raw / (document["id"] + ".pdf")))
                try:
                    parsed = subprocess.run([sys.executable, "-m", "mymanah.parse_pdf", str(self.raw / (document["id"] + ".pdf"))],
                                            cwd=ROOT, capture_output=True, timeout=min(15, max(0.1, deadline - time.monotonic())))
                except subprocess.TimeoutExpired as exc:
                    raise ServiceError("PDF_EXTRACTION_TIMEOUT", "PDF extraction timed out", 504) from exc
                try:
                    payload = json.loads(parsed.stdout)
                except ValueError as exc:
                    raise ServiceError("CORRUPT_PDF", "Unable to extract PDF text", 422) from exc
                if parsed.returncode or "error" in payload:
                    raise ServiceError(payload.get("error", "CORRUPT_PDF"), "PDF is unsupported, corrupt, encrypted or requires OCR", 422)
                self.check(flight, deadline)
                chunks = self.chunk(payload["pages"], document["generation"])
                self.storage.write_chunks(document["id"], chunks)
                collection = self.client.create_collection(self.collection_name(document["generation"]),
                                                          embedding_function=None, metadata={"hnsw:space": "cosine"})
                for start in range(0, len(chunks), 16):
                    self.check(flight, deadline)
                    batch = chunks[start:start + 16]
                    vectors = self.models.embed([c["text"] for c in batch])
                    if any(len(vector) != 384 for vector in vectors):
                        raise ServiceError("EMBEDDING_DIMENSION", "Embedding dimensions do not match the manifest")
                    collection.add(ids=[c["id"] for c in batch], embeddings=vectors,
                                   metadatas=[{"page": c["page"], "generation": c["generation"]} for c in batch])
                if collection.count() != len(chunks):
                    raise ServiceError("INDEX_INCOMPLETE", "Index verification failed")
                probe = self.models.embed([chunks[0]["text"]], query=True)
                result = collection.query(query_embeddings=probe, n_results=1)
                if not result["ids"][0]:
                    raise ServiceError("INDEX_INCOMPLETE", "Index retrieval probe failed")
                with self.storage.lock:
                    self.check(flight, deadline)
                    self.storage.publish(document["id"], document["generation"], len(payload["pages"]), len(chunks))
                return self.storage.get(document["id"], owner, ready=True), True
            finally:
                self.lane.release()
        except Exception as exc:
            if document:
                self.storage.fail(document["id"], exc.code if isinstance(exc, ServiceError) else "INGESTION_FAILED")
                self.remove_artifacts(document)
                self.storage.release_failed(document["id"])
            if isinstance(exc, ServiceError):
                raise
            raise ServiceError("INGESTION_FAILED", "Document ingestion failed") from exc
        finally:
            file.unlink(missing_ok=True)

    async def upload(self, file: Path, owner: str, filename: str, digest: str, deadline: float) -> tuple[dict, bool]:
        self.models.require()
        key = (owner, digest, self.pipeline)
        flight = self.flights.get(key)
        owns = flight is None
        if owns:
            if len(self.flights) >= 3:
                file.unlink(missing_ok=True)
                raise ServiceError("INGESTION_BUSY", "Ingestion capacity is busy; retry later", 429)
            flight = Flight()
            self.flights[key] = flight

            async def run():
                try:
                    return await asyncio.to_thread(self.ingest, file, owner, filename, digest, flight, deadline)
                finally:
                    self.flights.pop(key, None)

            flight.task = asyncio.create_task(run())
            flight.task.add_done_callback(lambda task: task.exception() if not task.cancelled() else None)
        else:
            file.unlink(missing_ok=True)
        try:
            return await asyncio.wait_for(asyncio.shield(flight.task), max(0.001, deadline - time.monotonic()))
        except (TimeoutError, asyncio.CancelledError) as exc:
            if owns:
                with self.storage.lock:
                    flight.abort.set()
                    if flight.document_id:
                        self.storage.fail(flight.document_id, "INGESTION_TIMEOUT")
            if isinstance(exc, asyncio.CancelledError):
                raise
            raise ServiceError("INGESTION_TIMEOUT", "Upload exceeded its 60-second deadline", 504) from exc

    def delete(self, document_id: str, owner: str) -> None:
        document = self.storage.mark_deleting(document_id, owner)
        with self.lane:
            self.remove_artifacts(document)
            self.storage.finish_delete(document_id)
