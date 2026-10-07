from __future__ import annotations

import math
import re

POLICY_VERSION = "journal-policy-2"
EMOTIONS = {
    "happy": "The writer currently feels pleased, proud, grateful or happy.",
    "sad": "The writer currently feels sad, lonely, sorrowful or low in spirits.",
    "anxiety": "The writer currently feels anxious and worried about uncertain future outcomes.",
    "stress": "The writer currently feels stressed, overloaded or pressured by demands.",
    "anger": "The writer currently feels angry, irritated, frustrated or resentful.",
    "fear": "The writer currently feels afraid of an immediate threat or danger.",
    "neutral": "The writer reports routine activities with no emotional reaction.",
}
CRISIS = [
    "The writer currently expresses personal intent or a plan to end their own life.",
    "The writer is currently harming themselves or is in immediate personal danger.",
    "The writer currently feels unable to cope with severe personal distress.",
    "The writer currently feels personally hopeless or like giving up on life.",
]
DISTRESS = [
    "The writer feels overwhelmed by their current difficulties.",
    "The writer describes distress persisting for days or weeks.",
    "The writer describes difficulties sleeping or functioning in everyday life.",
]


def distribution(scores: list[float]) -> list[float]:
    logits = [math.log(max(1e-7, p) / max(1e-7, 1 - p)) for p in scores]
    largest = max(logits)
    values = [math.exp(v - largest) for v in logits]
    total = sum(values)
    return [v / total for v in values]


def mood(sentiment: dict[str, float], distress: float) -> int:
    base = 5.5 + 4.5 * (sentiment["positive"] - sentiment["negative"])
    return max(1, min(10, math.floor(base - 1.5 * max(0, min(1, distress)) + 0.5)))


def explicit_current_danger(text: str) -> bool:
    for sentence in re.split(r"[.!?\n]+", text.casefold()):
        sentence = sentence.strip()
        if not re.match(r"^(?:tonight |right now |today )?i\b", sentence):
            continue
        if re.search(r"\b(?:not|never|used to|last year|years ago|back then|quote|quoted|story)\b", sentence):
            continue
        if re.search(r"\bi (?:want|intend|plan|am planning|am going) to (?:die|kill myself|end my life|hurt myself)\b", sentence):
            return True
    return False


def crisis_priority(text: str, signals: list[float], distress: list[float]) -> str:
    if explicit_current_danger(text) or max(signals[:2]) >= 0.80:
        return "HIGH"
    # The brief's sample uses a broad distress/impairment/giving-up interpretation.
    if signals[3] >= 0.65 and distress[1] >= 0.65 and distress[2] >= 0.65:
        return "HIGH"
    if max(signals) >= 0.55 or distress[0] >= 0.65 or (distress[1] >= 0.65 and distress[2] >= 0.65):
        return "MEDIUM"
    return "LOW"
