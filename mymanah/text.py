from __future__ import annotations

import re
from dataclasses import dataclass

from .errors import ServiceError


@dataclass(frozen=True)
class Window:
    text: str
    weight: int
    start: int
    end: int


def windows(text: str, tokenizer, size: int = 384, overlap: int = 64) -> list[Window]:
    offsets = tokenizer(text, add_special_tokens=False, return_offsets_mapping=True)["offset_mapping"]
    offsets = [(a, b) for a, b in offsets if b > a]
    if not offsets:
        raise ServiceError("UNUSABLE_TEXT", "No usable model tokens", 422)
    result = []
    start, previous_end = 0, 0
    while start < len(offsets):
        end = min(start + size, len(offsets))
        a, b = offsets[start][0], offsets[end - 1][1]
        result.append(Window(text[a:b], end - max(start, previous_end), a, b))
        previous_end = end
        if end == len(offsets):
            break
        start = end - overlap
    if len(result) > 24:
        raise ServiceError("WINDOW_LIMIT", "Entry exceeds 24 classifier windows", 413)
    return result


def normalized(text: str) -> str:
    return " ".join(text.split()).casefold()


def words(text: str) -> list[str]:
    return re.findall(r"[^\W_]+(?:['-][^\W_]+)*", text.casefold(), re.UNICODE)


def english_only(text: str) -> None:
    letters = [c for c in text if c.isalpha()]
    if letters and sum("a" <= c.casefold() <= "z" for c in letters) / len(letters) < 0.7:
        raise ServiceError("UNSUPPORTED_LANGUAGE", "The current release supports English text", 422)


def sentence_count(text: str) -> int:
    safe = re.sub(r"(?<=\d)\.(?=\d)", "", text)
    safe = re.sub(r"\b(?:Mr|Mrs|Ms|Dr|Prof|e\.g|i\.e)\.", "", safe, flags=re.I)
    return len([part for part in re.split(r"[.!?\u0964]+(?:\s|$)", safe) if part.strip()])


def numeric_supported(claim: str, evidence: str) -> bool:
    pattern = r"\b\d+(?:[.,]\d+)*(?:%|\b)"
    numbers = set(re.findall(pattern, claim))
    return numbers.issubset(set(re.findall(pattern, evidence)))


def source_quote(source: str, quote: str) -> str | None:
    if not quote.strip():
        return None
    pattern = r"\s+".join(re.escape(part) for part in quote.split())
    match = re.search(pattern, source)
    return match.group(0) if match else None


def evidence_context(source: str, quote: str, tokenizer) -> str:
    for piece in windows(source, tokenizer):
        if source_quote(piece.text, quote) is not None:
            return piece.text
    raise ServiceError("EVIDENCE_TOO_LONG", "Evidence quote cannot fit a contextual verification window")
