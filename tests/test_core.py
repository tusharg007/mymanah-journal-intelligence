import asyncio
import hashlib
import time

import pytest
from pydantic import ValidationError

from mymanah.admission import Admission
from mymanah.config import Settings
from mymanah.errors import ServiceError
from mymanah.policy import crisis_priority, distribution, explicit_current_danger, mood
from mymanah.schemas import JournalRequest, JournalResponse
from mymanah.storage import Storage
from mymanah.text import english_only, numeric_supported, sentence_count, source_quote, windows


def test_exact_journal_request():
    assert JournalRequest(text="A real entry").text == "A real entry"
    for payload in ({"text": ""}, {"text": "  "}, {"text": "secret\x00"}, {"text": "ok", "language": "en"}):
        with pytest.raises(ValidationError):
            JournalRequest(**payload)


def test_response_contract():
    value = JournalResponse(sentiment="neutral", emotion="neutral", moodScore=6,
                            summary="The writer recorded an event. They reported no feelings.", crisisRisk="LOW", confidence=.5)
    assert set(value.model_dump()) == {"sentiment", "emotion", "moodScore", "summary", "crisisRisk", "confidence"}
    with pytest.raises(ValidationError):
        JournalResponse(**{**value.model_dump(), "confidence": float("nan")})


@pytest.mark.parametrize("positive,negative", [(0, 1), (.2, .8), (.5, .5), (.8, .2), (1, 0)])
def test_mood_bounds_and_distress(positive, negative):
    score = mood({"positive": positive, "negative": negative}, 0)
    distressed = mood({"positive": positive, "negative": negative}, 1)
    assert 1 <= distressed <= score <= 10


def test_mood_monotonic():
    scores = [mood({"positive": p / 10, "negative": 1 - p / 10}, 0) for p in range(11)]
    assert scores == sorted(scores)


@pytest.mark.parametrize("text", ["I plan to end my life tonight.", "Tonight I am going to kill myself.", "I want to die."])
def test_explicit_danger(text):
    assert explicit_current_danger(text)
    assert crisis_priority(text, [0, 0, 0, 0], [0, 0, 0]) == "HIGH"


@pytest.mark.parametrize("text", ["I do not want to die.", "I used to want to die years ago.",
                                     "My friend said I want to die.", "I plan to end this puzzle.",
                                     "I quoted the line I want to die from a book."])
def test_danger_context_controls(text):
    assert not explicit_current_danger(text)


def test_priority_policy():
    assert crisis_priority("Ordinary entry", [.1, .1, .1, .1], [0, 0, 0]) == "LOW"
    assert crisis_priority("Distress", [.1, .1, .7, .4], [.5, .4, .4]) == "MEDIUM"
    assert crisis_priority("Persistent impairment and giving up", [.1, .1, .8, .8], [.7, .8, .8]) == "HIGH"
    assert crisis_priority("Supported overwhelming demands", [.1, .1, .1, .1], [.8, .2, .2]) == "MEDIUM"
    assert crisis_priority("Persistent impairment", [.1, .1, .1, .1], [.2, .8, .8]) == "MEDIUM"


def test_distribution_stable():
    probabilities = distribution([0, 1, .5])
    assert sum(probabilities) == pytest.approx(1)
    assert probabilities[1] > probabilities[2] > probabilities[0]


def test_numbers_not_substrings():
    assert not numeric_supported("The limit is 50", "The limit is 150")
    assert numeric_supported("The limit is 150", "The limit is 150 units")
    assert not numeric_supported("Pay 10%", "Pay 10 units")


def test_exact_quotes():
    assert source_quote("A line\nwith spacing", "A line with spacing") == "A line\nwith spacing"
    assert source_quote("The allowance is 100.", "The allowance is 200.") is None


def test_sentence_boundaries():
    assert sentence_count("It costs 2.5 dollars. Dr. Smith confirmed it.") == 2
    assert sentence_count("A short sentence.") == 1


def test_language_scope():
    english_only("I feel happy today!")
    with pytest.raises(ServiceError, match="English"):
        english_only("आज मैं खुश हूँ।")


class CharacterTokenizer:
    def __call__(self, text, **kwargs):
        return {"offset_mapping": [(i, i + 1) for i in range(len(text))]}


def test_full_window_coverage():
    text = "x" * 1700
    result = windows(text, CharacterTokenizer())
    assert result[0].start == 0 and result[-1].end == len(text)
    assert sum(piece.weight for piece in result) == len(text)
    assert all(a.end >= b.start for a, b in zip(result, result[1:]))


def test_window_limit_not_truncated():
    with pytest.raises(ServiceError):
        windows("x" * 10000, CharacterTokenizer())


def test_auth_settings(monkeypatch, tmp_path):
    monkeypatch.delenv("API_KEYS", raising=False)
    monkeypatch.setenv("HOST", "127.0.0.1")
    assert not Settings.from_env().auth_enabled
    monkeypatch.setenv("HOST", "0.0.0.0")
    with pytest.raises(ValueError, match="loopback"):
        Settings.from_env()
    monkeypatch.setenv("API_KEYS", "reviewer:" + "x" * 43)
    settings = Settings.from_env()
    assert settings.keys == {"reviewer": hashlib.sha256(("x" * 43).encode()).hexdigest()}


@pytest.mark.parametrize("value", ["", "reviewer:short", "a:" + "x" * 32 + ",a:" + "y" * 32,
                                    "a:" + "x" * 32 + ",b:" + "x" * 32])
def test_bad_auth_fails_closed(monkeypatch, value):
    monkeypatch.setenv("API_KEYS", value)
    with pytest.raises(ValueError):
        Settings.from_env()


def document():
    return {"id": "d1", "owner": "alice", "content_hash": "hash", "pipeline": "v1",
            "filename": "policy.pdf", "generation": "g1", "bytes": 10, "reserved": 100}


def test_storage_publication_and_ownership(tmp_path):
    store = Storage(tmp_path / "db.sqlite3", 10000)
    store.reserve(document())
    with pytest.raises(ServiceError) as not_ready:
        store.get("d1", "alice", ready=True)
    assert not_ready.value.status == 409
    with pytest.raises(ServiceError) as wrong_owner:
        store.get("d1", "bob")
    assert wrong_owner.value.status == 404
    store.publish("d1", "g1", 2, 3)
    assert store.get("d1", "alice", ready=True)["pages"] == 2


def test_cancelled_generation_cannot_publish(tmp_path):
    store = Storage(tmp_path / "db.sqlite3", 10000)
    store.reserve(document())
    store.fail("d1", "TIMEOUT")
    with pytest.raises(ServiceError):
        store.publish("d1", "g1", 2, 3)
    assert store.get("d1", "alice")["state"] == "FAILED"


def test_storage_quota(tmp_path):
    store = Storage(tmp_path / "db.sqlite3", 50)
    with pytest.raises(ServiceError) as failure:
        store.reserve(document())
    assert failure.value.code == "STORAGE_QUOTA"


def test_delete_hides_document_first(tmp_path):
    store = Storage(tmp_path / "db.sqlite3", 10000)
    store.reserve(document())
    store.publish("d1", "g1", 1, 1)
    store.mark_deleting("d1", "alice")
    with pytest.raises(ServiceError):
        store.get("d1", "alice", ready=True)
    store.finish_delete("d1")
    assert store.list("alice") == []


def test_admission_retains_capacity():
    async def exercise():
        gate = Admission(queue_size=0)
        started, finished = asyncio.Event(), asyncio.Event()

        async def work():
            async with gate.enter():
                started.set()
                await finished.wait()

        task = asyncio.create_task(work())
        await started.wait()
        with pytest.raises(TimeoutError):
            await asyncio.wait_for(asyncio.shield(task), .01)
        assert gate.count == 1
        with pytest.raises(ServiceError):
            async with gate.enter():
                pass
        finished.set()
        await task
        assert gate.count == 0
    asyncio.run(exercise())


def test_rate_limit():
    gate = Admission()
    gate.rate("alice", "upload", 2)
    gate.rate("alice", "upload", 2)
    with pytest.raises(ServiceError) as exc:
        gate.rate("alice", "upload", 2)
    assert exc.value.status == 429
    gate.rate("bob", "upload", 2)


def test_expired_waiter_releases_queue_without_starting_work():
    async def exercise():
        gate = Admission()
        active, finish = asyncio.Event(), asyncio.Event()
        started = []

        async def blocker():
            async with gate.enter():
                active.set()
                await finish.wait()

        async def expired():
            async with gate.enter(deadline=time.monotonic() + .02):
                started.append("expired")

        task = asyncio.create_task(blocker())
        await active.wait()
        with pytest.raises(ServiceError) as failure:
            await expired()
        assert failure.value.status == 504
        assert gate.count == 1 and started == []
        finish.set()
        await task
        async with gate.enter(deadline=time.monotonic() + 1):
            started.append("fresh")
        assert started == ["fresh"] and gate.count == 0
    asyncio.run(exercise())
