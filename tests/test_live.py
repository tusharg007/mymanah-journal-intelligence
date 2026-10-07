import os

import httpx
import pytest

from tests.pdf_helpers import make_pdf

pytestmark = pytest.mark.live


@pytest.fixture
def live():
    origin = os.getenv("LIVE_API_URL", "http://127.0.0.1:8000")
    headers = {"Authorization": "Bearer " + os.environ["LIVE_API_KEY"]} if os.getenv("LIVE_API_KEY") else {}
    with httpx.Client(base_url=origin, headers=headers, timeout=70, trust_env=False) as client:
        assert client.get("/health/ready").status_code == 200, "Real downloaded models and Ollama must be ready"
        yield client


def test_live_journal_exact_contract(live):
    response = live.post("/analyze-journal", json={"text": "I finished my project today and feel proud of my progress. The review went well."})
    assert response.status_code == 200, response.text
    data = response.json()
    assert set(data) == {"sentiment", "emotion", "moodScore", "summary", "crisisRisk", "confidence"}
    assert data["sentiment"] == "positive"
    # Per-emotion semantic agreement is measured with counts in evals, not a single-case gate.
    assert data["emotion"] in {"happy", "sad", "anxiety", "stress", "anger", "fear", "neutral"}
    assert 1 <= data["moodScore"] <= 10 and 0 <= data["confidence"] <= 1


def test_live_upload_immediate_question_and_abstention(live, tmp_path):
    pdf = make_pdf(tmp_path / "leave-policy.pdf", [
        "Northwind staff receive 17 days of annual leave. Contractors receive no annual leave. Leave requires approval from the line manager.",
        "The equipment reimbursement limit is 275 dollars per calendar year. Receipts must be submitted within 21 days."
    ])
    with pdf.open("rb") as file:
        upload = live.post("/documents", files={"file": (pdf.name, file, "application/pdf")})
    assert upload.status_code in {200, 201}, upload.text
    assert upload.json()["status"] == "READY"
    document_id = upload.json()["document"]["id"]
    try:
        answer = live.post(f"/documents/{document_id}/questions", json={"question": "How many annual leave days do Northwind staff receive?"})
        assert answer.status_code == 200, answer.text
        data = answer.json()
        assert data["status"] == "ANSWERED" and "17" in data["answer"]
        assert data["citations"] and all(c["document_id"] == document_id and c["page"] == 1 for c in data["citations"])
        unsupported = live.post(f"/documents/{document_id}/questions", json={"question": "What was Northwind's revenue in 2019?"})
        assert unsupported.status_code == 200, unsupported.text
        assert unsupported.json()["status"] == "INSUFFICIENT_EVIDENCE"
        assert unsupported.json()["citations"] == []
    finally:
        assert live.delete(f"/documents/{document_id}").status_code == 204
