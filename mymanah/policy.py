from __future__ import annotations

import math
import re

POLICY_VERSION = "journal-policy-4"
EMOTIONS = {
    "happy": "The writer feels good, pleased, joyful, grateful or happy about their experience.",
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
    "The writer currently feels personally hopeless, defeated or like giving up.",
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


def mood(sentiment: dict[str, float], distress: float, risk: str = "LOW", emotion: str = "neutral") -> int:
    base = 6 + 3 * (sentiment["positive"] - sentiment["negative"])
    score = math.floor(base - 0.75 * max(0, min(1, distress)) + 0.5)
    if risk == "HIGH":
        return max(1, min(2, score))
    ceiling = 7 if sentiment["positive"] >= 0.7 and emotion not in {"happy", "neutral"} else 9
    return max(3, min(ceiling, score))


def current_giving_up(text: str) -> bool:
    for sentence in re.split(r"[.!?\n]+", text.casefold().replace("\u2019", "'")):
        if not re.match(r"\s*(?:(?:sometimes|lately|right now|today|tonight|now)\s+)?i\b", sentence):
            continue
        if re.search(r"\b(?:used to|years? ago|last year|back then|quoted?|fiction|no longer)\b", sentence):
            continue
        if re.search(r"\b(?:not|never) (?:feel |feeling )?(?:hopeless|giving up)|\bdon't (?:feel (?:hopeless|like giving up)|want to give up)\b", sentence):
            continue
        if re.search(r"\b(?:give|giving|given) up (?:this |the |a |my |on (?:this |the |a |my )?)?(?:puzzle|game|book|hobby)\b", sentence):
            continue
        if re.search(r"\bi\b.*\b(?:hopeless|no hope|(?:give|giving|given) up)\b", sentence):
            return True
    return False


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
    if (current_giving_up(text) or signals[3] >= 0.65) and max(distress) >= 0.65:
        return "HIGH"
    if max(signals) >= 0.55 or distress[0] >= 0.65 or (distress[1] >= 0.65 and distress[2] >= 0.65):
        return "MEDIUM"
    return "LOW"
