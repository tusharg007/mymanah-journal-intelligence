import asyncio
import hashlib
import re
import threading
import time
from types import SimpleNamespace

import pytest

from mymanah.config import Settings
from mymanah.documents import Documents, Flight
from mymanah.errors import ServiceError
from mymanah.parse_pdf import extract
from mymanah.rag import RAG
from mymanah.schemas import AnswerDraft
from mymanah.storage import Storage
from tests.pdf_helpers import make_pdf


class WordTokenizer:
    def __call__(self, text, **kwargs):
        return {"offset_mapping": [(match.start(), match.end()) for match in re.finditer(r"\S+", text)]}

    def encode(self, text):
        return text.split()


class FixtureEmbeddings:
    """Deterministic test adapter for index transactions, not a quality evaluation."""
    def __init__(self):
        self.manifest = {"embedding": {"revision": "test-only"}}
        self.embedding = SimpleNamespace(tokenizer=WordTokenizer())
        self.nli_tokenizer = WordTokenizer()

    def require(self):
        pass

    def embed(self, texts, query=False):
        vectors = []
        for text in texts:
            vector = [0.0] * 384
            for word in text.lower().split():
                index = int(hashlib.sha256(word.encode()).hexdigest()[:8], 16) % 384
                vector[index] += 1
            norm = sum(x * x for x in vector)**.5 or 1
            vectors.append([x / norm for x in vector])
        return vectors

    def support(self, pairs):
        return [1.0] * len(pairs)

    def token_count(self, text):
        return len(text.split())


@pytest.fixture
def documents(tmp_path):
    settings = Settings(data_dir=tmp_path)
    store = Storage(tmp_path / "metadata.sqlite3", settings.global_disk_bytes)
    service = Documents(settings, store, FixtureEmbeddings())
    yield service
    service.client._system.stop()
    service.client.clear_system_cache()


def ingest(documents, tmp_path, text="Employees receive 14 days of annual leave. Contractors receive no annual leave.", owner="alice"):
    file = make_pdf(tmp_path / "input.upload", [text])
    digest = hashlib.sha256(file.read_bytes()).hexdigest()
    return documents.ingest(file, owner, "policy.pdf", digest, Flight(), time.monotonic() + 60)


def test_extract_real_pdf(tmp_path):
    path = make_pdf(tmp_path / "policy.pdf", ["Employees receive 14 days of leave.", "Approval is required before travel."])
    pages = extract(path)
    assert len(pages) == 2
    assert "14 days" in pages[0]


def test_real_index_is_ready_before_return(documents, tmp_path):
    document, created = ingest(documents, tmp_path)
    assert created and document["state"] == "READY"
    assert documents.collection(document["generation"]).count() == document["chunks"]
    assert documents.storage.get(document["id"], "alice", ready=True)["pages"] == 1
    evidence = RAG(documents, documents.storage, documents.models).retrieve(document, "annual leave days employees")
    assert evidence and "14 days" in evidence[0]["text"]


def test_duplicate_reuses_ready_index(documents, tmp_path):
    first, _ = ingest(documents, tmp_path)
    second, created = ingest(documents, tmp_path)
    assert not created and first["id"] == second["id"]
    assert len(documents.storage.list("alice")) == 1


def test_owner_same_file_has_isolated_collection(documents, tmp_path):
    alice, _ = ingest(documents, tmp_path, owner="alice")
    bob, _ = ingest(documents, tmp_path, owner="bob")
    assert alice["generation"] != bob["generation"]
    with pytest.raises(ServiceError) as exc:
        documents.storage.get(alice["id"], "bob")
    assert exc.value.status == 404


def test_aborted_upload_never_ready(documents, tmp_path):
    file = make_pdf(tmp_path / "input.upload", ["Employees receive 14 days of annual leave."])
    flight = Flight()
    flight.abort.set()
    with pytest.raises(ServiceError) as exc:
        documents.ingest(file, "alice", "policy.pdf", "hash", flight, time.monotonic() + 60)
    assert exc.value.status == 504
    assert not documents.storage.list("alice")
    assert not file.exists()


def test_invalid_pdf_cleans_partial_artifacts(documents, tmp_path):
    file = tmp_path / "bad.upload"
    file.write_bytes(b"%PDF-1.7\ncorrupt contents")
    with pytest.raises(ServiceError):
        documents.ingest(file, "alice", "bad.pdf", "bad-hash", Flight(), time.monotonic() + 60)
    record = documents.storage.list("alice")[0]
    assert record["state"] == "FAILED" and record["reserved"] == 0
    assert not documents.client.list_collections()
    assert not list(documents.raw.glob("*.pdf"))


def test_delete_removes_source_chunks_and_vectors(documents, tmp_path):
    document, _ = ingest(documents, tmp_path)
    documents.delete(document["id"], "alice")
    assert not documents.storage.list("alice")
    assert not documents.storage.canonical(document["id"])
    assert not documents.client.list_collections()


def test_claims_cannot_cite_another_document(documents, tmp_path):
    document, _ = ingest(documents, tmp_path)
    evidence = documents.storage.canonical(document["id"])
    draft = AnswerDraft(answerable=True, complete=True, claims=[{"text": "Employees receive 14 days of annual leave.",
                       "chunk_id": "other_document_chunk", "quote": "Employees receive 14 days of annual leave."}])
    with pytest.raises(ServiceError):
        RAG(documents, documents.storage, documents.models).verify(draft, evidence, document)


def test_claim_number_must_match_quote(documents, tmp_path):
    document, _ = ingest(documents, tmp_path)
    evidence = documents.storage.canonical(document["id"])
    draft = AnswerDraft(answerable=True, complete=True, claims=[{"text": "Employees receive 40 days of annual leave.",
                       "chunk_id": evidence[0]["id"], "quote": "Employees receive 14 days of annual leave."}])
    with pytest.raises(ServiceError):
        RAG(documents, documents.storage, documents.models).verify(draft, evidence, document)


def test_recovery_removes_unpublished_generation(documents):
    record = {"id": "interrupted", "owner": "alice", "content_hash": "hash", "pipeline": "v",
              "filename": "policy.pdf", "generation": "interruptedgen", "bytes": 10, "reserved": 100}
    documents.storage.reserve(record)
    documents.client.create_collection(documents.collection_name(record["generation"]), embedding_function=None)
    documents.recover()
    assert documents.storage.get("interrupted", "alice")["state"] == "FAILED"
    assert not documents.client.list_collections()


def test_joining_waiter_timeout_does_not_abort_owner(documents, tmp_path, monkeypatch):
    started = threading.Event()
    release = threading.Event()
    original = documents.ingest

    def blocked(*args):
        started.set()
        release.wait(5)
        return original(*args)

    monkeypatch.setattr(documents, "ingest", blocked)

    async def run():
        first = make_pdf(tmp_path / "first.upload", ["Employees receive 14 days of annual leave."])
        second = tmp_path / "second.upload"
        second.write_bytes(first.read_bytes())
        digest = hashlib.sha256(first.read_bytes()).hexdigest()
        owner = asyncio.create_task(documents.upload(first, "alice", "policy.pdf", digest, time.monotonic() + 60))
        await asyncio.to_thread(started.wait, 2)
        with pytest.raises(ServiceError) as timeout:
            await documents.upload(second, "alice", "policy.pdf", digest, time.monotonic() + .02)
        assert timeout.value.status == 504
        assert not next(iter(documents.flights.values())).abort.is_set()
        release.set()
        record, _ = await owner
        assert record["state"] == "READY"
    asyncio.run(run())


def test_owner_cancel_never_publishes_after_worker_finishes(documents, tmp_path, monkeypatch):
    started, release = threading.Event(), threading.Event()
    original = documents.ingest

    def blocked(*args):
        started.set()
        release.wait(5)
        return original(*args)

    monkeypatch.setattr(documents, "ingest", blocked)

    async def run():
        pdf = make_pdf(tmp_path / "cancel.upload", ["Employees receive 14 days of annual leave."])
        digest = hashlib.sha256(pdf.read_bytes()).hexdigest()
        owner = asyncio.create_task(documents.upload(pdf, "alice", "policy.pdf", digest, time.monotonic() + 60))
        assert await asyncio.to_thread(started.wait, 2)
        flight = next(iter(documents.flights.values()))
        owner.cancel()
        with pytest.raises(asyncio.CancelledError):
            await owner
        assert flight.abort.is_set()
        release.set()
        with pytest.raises(ServiceError):
            await flight.task
        assert not documents.storage.list("alice")
        assert not documents.client.list_collections()
    asyncio.run(run())
