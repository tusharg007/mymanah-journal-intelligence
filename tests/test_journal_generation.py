import asyncio

import pytest

from mymanah.errors import ServiceError
from mymanah.journal import JournalService
from mymanah.schemas import SummaryDraft


class JournalModels:
    nli_tokenizer = None

    def __init__(self, failure=None):
        self.calls = 0
        self.failure = failure

    def require(self):
        pass

    def token_count(self, text):
        return 20

    def support(self, pairs, deadline=None):
        return [1.0] * len(pairs)

    async def generate(self, system, prompt, schema, **kwargs):
        self.calls += 1
        if self.failure:
            raise self.failure
        return SummaryDraft(sentences=[
            {"text": "The writer feels overwhelmed by work.", "quote": "I feel overwhelmed by work."},
            {"text": "The writer is struggling with sleep.", "quote": "I cannot sleep properly."}])


class JournalUnderTest(JournalService):
    def classify(self, text, deadline=None, safety_only=False):
        return {"sentiment": {"negative": .95, "neutral": .04, "positive": .01},
                "emotion": {"stress": .9, "sad": .1}, "risk": "HIGH", "distress": .9}

    def verify_summary(self, source, draft, deadline=None):
        # Only the verification boundary is replaced; generation/control flow is exercised.
        assert all(sentence.quote in source for sentence in draft.sentences)


def test_high_risk_entry_calls_generator_and_retains_verified_third_person_summary():
    models = JournalModels()
    result = asyncio.run(JournalUnderTest(models).analyze("I feel overwhelmed by work. I cannot sleep properly."))
    assert models.calls == 1
    assert result.summary == "The writer feels overwhelmed by work. The writer is struggling with sleep."
    assert result.confidence == .9


def test_two_generation_failures_use_verified_extracts_without_repeated_single_fact():
    models = JournalModels(ServiceError("GENERATION_FAILED", "Generation failed"))
    result = asyncio.run(JournalUnderTest(models).analyze("I feel overwhelmed by work."))
    assert models.calls == 2
    assert result.summary == "I feel overwhelmed by work. No further details are given."


def test_generation_deadline_does_not_return_an_unverified_fallback():
    models = JournalModels(ServiceError("INFERENCE_TIMEOUT", "Deadline exceeded", 504))
    with pytest.raises(ServiceError) as failure:
        asyncio.run(JournalUnderTest(models).analyze("I feel overwhelmed by work."))
    assert failure.value.status == 504


def test_positive_neutral_consistency_uses_winning_sentiment_without_arbitrary_cutoff():
    class PositiveJournal(JournalUnderTest):
        def classify(self, text, deadline=None, safety_only=False):
            return {"sentiment": {"positive": .72, "neutral": .27, "negative": .01},
                    "emotion": {"neutral": .96, "happy": .0026, "sad": .0374}, "risk": "LOW", "distress": 0}

    result = asyncio.run(PositiveJournal(JournalModels()).analyze("I feel overwhelmed by work. I cannot sleep properly."))
    assert result.emotion == "happy"
    assert result.confidence == .72
