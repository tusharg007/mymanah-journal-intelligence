import asyncio
import json
from types import SimpleNamespace

import pytest

from mymanah.errors import ServiceError
from mymanah.rag import RAG
from mymanah.schemas import AnswerDraft
from tests.test_documents import WordTokenizer


@pytest.mark.parametrize("claim,quote", [
    ("Unused leave can be carried over.", "Carry-over: Up to 5 unused days may be carried over and must be used by\n31 March."),
    ("Up to 2 days per week.", "Employees may work remotely up to 2 days per week with prior approval from their line\nmanager."),
    ("Employees can take unpaid leave.", "Up to 15 days of unpaid leave may be granted with director approval."),
    ("Sick leave is 10 days.", "Sick leave is 10 days. A medical certificate is required after 3 consecutive days."),
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


@pytest.mark.parametrize("question", ["How many days of paternity leave are offered?", "What is the stock option policy?"])
def test_absent_content_modifier_abstains_before_generation(question):
    supported, missing = RAG.supported_question(question, [{"text": "Sick leave: 10 days. Maternity leave: 26 weeks."}])
    assert not supported
    assert missing == [question]


def test_mixed_question_keeps_supported_part_and_marks_missing_topic():
    question = "What is the sick leave policy and what is the stock option policy?"
    supported, missing = RAG.supported_question(question, [{"text": "Sick leave: 10 days. Maternity leave: 26 weeks."}])
    assert supported == "What is the sick leave policy"
    assert missing == ["what is the stock option policy?"]


def test_question_guard_preserves_qualifying_conditions_and_synonyms():
    evidence = [{"text": "Annual leave is 24 days. Carry-over is 5 days with expiry on 31 March."}]
    question = "What is the vacation allowance and when does carry-over expire?"
    assert RAG.supported_question(question, evidence) == (question, [])


class AnswerModels:
    nli_tokenizer = WordTokenizer()

    def __init__(self):
        self.calls = 0

    def require(self):
        pass

    def token_count(self, text):
        return len(text.split())

    def support(self, pairs):
        return [1.0] * len(pairs)

    async def generate(self, system, prompt, schema, **kwargs):
        self.calls += 1
        assert json.loads(prompt)["question"] == "What is the sick leave policy"
        return AnswerDraft(answerable=True, complete=True, claims=[{
            "text": "Employees receive 10 days of sick leave.", "quote": "Employees receive 10 days of sick leave.", "chunk_id": "chunk"}])


def answer_fixture():
    models = AnswerModels()
    storage = SimpleNamespace(get=lambda *args, **kwargs: {"id": "doc", "generation": "gen", "filename": "handbook.pdf"})
    rag = RAG(None, storage, models)
    rag.retrieve = lambda *args: [{"id": "chunk", "page": 2,
                                 "text": "Employees receive 10 days of sick leave. Maternity leave is 26 weeks."}]
    return rag, models


def test_unsupported_topic_returns_empty_abstention_without_generator_call():
    rag, models = answer_fixture()
    result = asyncio.run(rag.answer("doc", "alice", "How much paternity leave is available?"))
    assert result.status == "INSUFFICIENT_EVIDENCE"
    assert result.citations == []
    assert models.calls == 0


def test_partial_answer_verifies_supported_claim_and_names_uncovered_part():
    rag, models = answer_fixture()
    result = asyncio.run(rag.answer("doc", "alice", "What is the sick leave policy and what is the stock option policy?"))
    assert result.status == "PARTIAL"
    assert result.citations[0].quote == "Employees receive 10 days of sick leave."
    assert "stock option" in result.answer
    assert models.calls == 1
