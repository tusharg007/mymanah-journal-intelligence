import pytest

from mymanah.errors import ServiceError
from mymanah.rag import RAG
from mymanah.schemas import AnswerDraft


@pytest.mark.parametrize("claim,quote", [
    ("Unused leave can be carried over.", "Carry-over: Up to 5 unused days may be carried over and must be used by\n31 March."),
    ("Up to 2 days per week.", "Employees may work remotely up to 2 days per week with prior approval from their line\nmanager."),
    ("Employees can take unpaid leave.", "Up to 15 days of unpaid leave may be granted with director approval."),
])
def test_verified_policy_conditions_are_preserved_in_answer(claim, quote):
    assert RAG.policy_answer_text(claim, quote) == " ".join(quote.split())


def test_nonconditional_answer_keeps_verified_paraphrase():
    assert RAG.policy_answer_text("Annual leave is 24 days.", "Employees receive 24 days annually.") == "Annual leave is 24 days."


def test_invalid_evidence_is_rejected_before_answer_assembly():
    draft = AnswerDraft(answerable=True, complete=True, claims=[{
        "text": "Leave is permitted.", "chunk_id": "chunk", "quote": "Leave is permitted with approval."}])
    with pytest.raises(ServiceError, match="evidence"):
        RAG(None, None, None).verify(draft, [{"id": "chunk", "text": "No leave is permitted."}], {})
