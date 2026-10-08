import hashlib

import pytest
from fastapi.testclient import TestClient

pytest.importorskip("rank_bm25")

from mymanah.api import create_app
from mymanah.config import Settings
from mymanah.errors import ServiceError


class UnavailableModels:
    """Test-only outage injection; never used by the runtime."""
    def __init__(self, settings):
        self.ready = False
        self.failure = "TEST_OUTAGE"

    async def load(self):
        pass

    def require(self):
        raise ServiceError("MODELS_UNAVAILABLE", "Required local models are unavailable")

    async def close(self):
        pass


class NoDocuments:
    def __init__(self, settings, storage, models):
        self.flights = {}

    def recover(self):
        pass


def client(tmp_path, keys=None):
    return TestClient(create_app(Settings(data_dir=tmp_path, keys=keys or {}),
                                 model_factory=UnavailableModels, document_factory=NoDocuments), base_url="http://127.0.0.1")


def test_default_sample_curl_not_401(tmp_path):
    with client(tmp_path) as app:
        response = app.post("/analyze-journal", json={"text": "I feel happy today."})
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "MODELS_UNAVAILABLE"


def test_open_loopback_rejects_rebinding_host(tmp_path):
    with client(tmp_path) as app:
        assert app.get("/documents", headers={"Host": "attacker.example"}).status_code == 400
        assert app.get("/health/live", headers={"Host": "localhost:8000"}).status_code == 200
        assert app.get("/health/live", headers={"Host": "[::1]:8000"}).status_code == 200


def test_keyed_mode_requires_auth(tmp_path):
    secret = "x" * 43
    with client(tmp_path, {"alice": hashlib.sha256(secret.encode()).hexdigest()}) as app:
        assert app.post("/analyze-journal", json={"text": "entry"}).status_code == 401
        assert app.post("/analyze-journal", json={"text": "entry"}, headers={"Authorization": "Bearer wrong"}).status_code == 401
        response = app.post("/analyze-journal", json={"text": "entry"}, headers={"Authorization": "Bearer " + secret})
        assert response.status_code == 503


def test_validation_does_not_echo_sensitive_text(tmp_path):
    with client(tmp_path) as app:
        response = app.post("/analyze-journal", json={"text": "VERY_PRIVATE_SECRET", "extra": "PRIVATE_EXTRA"})
        assert response.status_code == 422
        assert "VERY_PRIVATE_SECRET" not in response.text
        assert "PRIVATE_EXTRA" not in response.text
        assert "X-Request-ID" in response.headers


def test_owner_scoped_document_lookup(tmp_path):
    a, b = "a" * 43, "b" * 43
    with client(tmp_path, {"alice": hashlib.sha256(a.encode()).hexdigest(), "bob": hashlib.sha256(b.encode()).hexdigest()}) as app:
        store = app.app.state.storage
        store.reserve({"id": "owned", "owner": "alice", "content_hash": "hash", "pipeline": "v1",
                       "filename": "private.pdf", "generation": "g", "bytes": 10, "reserved": 100})
        store.publish("owned", "g", 1, 1)
        assert app.get("/documents/owned", headers={"Authorization": "Bearer " + a}).status_code == 200
        assert app.get("/documents/owned", headers={"Authorization": "Bearer " + b}).status_code == 404
        assert app.get("/documents", headers={"Authorization": "Bearer " + b}).json() == {"documents": []}


def test_large_json_is_bounded(tmp_path):
    with client(tmp_path) as app:
        assert app.post("/analyze-journal", content=b"x" * 40000).status_code == 413


def test_health_is_non_sensitive_and_open(tmp_path):
    with client(tmp_path, {"alice": hashlib.sha256(b"x" * 43).hexdigest()}) as app:
        assert app.get("/health/live").status_code == 200
        response = app.get("/health/ready")
        assert response.status_code == 503
        assert response.json()["authEnabled"] is True


def test_language_and_token_limits_reject_before_full_inference_queue(tmp_path):
    class ReadyModels(UnavailableModels):
        def require(self):
            pass

        def token_count(self, text):
            return len(text)

    app = create_app(Settings(data_dir=tmp_path), model_factory=ReadyModels, document_factory=NoDocuments)
    with TestClient(app, base_url="http://127.0.0.1") as browser:
        app.state.admission.count = app.state.admission.limit
        unsupported = browser.post("/analyze-journal", json={"text": "\u092e\u0948\u0902 \u0906\u091c \u0926\u0941\u0916\u0940 \u0939\u0942\u0901"})
        assert unsupported.status_code == 422
        assert unsupported.json()["error"]["code"] == "UNSUPPORTED_LANGUAGE"
        too_long = browser.post("/analyze-journal", json={"text": "x" * 2001})
        assert too_long.status_code == 413
        assert too_long.json()["error"]["code"] == "TEXT_TOKEN_LIMIT"
