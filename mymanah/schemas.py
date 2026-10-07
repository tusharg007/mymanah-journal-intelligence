from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class JournalRequest(StrictModel):
    text: str = Field(min_length=1, max_length=8000)

    @field_validator("text")
    @classmethod
    def usable_text(cls, value: str) -> str:
        if not value.strip() or "\x00" in value:
            raise ValueError("Text must contain usable non-NUL characters")
        return value


class JournalResponse(StrictModel):
    sentiment: Literal["positive", "neutral", "negative"]
    emotion: Literal["happy", "sad", "anxiety", "stress", "anger", "fear", "neutral"]
    moodScore: int = Field(ge=1, le=10)
    summary: str
    crisisRisk: Literal["LOW", "MEDIUM", "HIGH"]
    confidence: float = Field(ge=0, le=1, allow_inf_nan=False)


class SummarySentence(StrictModel):
    text: str = Field(min_length=1, max_length=350)
    quote: str = Field(min_length=1, max_length=600)


class SummaryDraft(StrictModel):
    sentences: list[SummarySentence] = Field(min_length=2, max_length=3)


class QuestionRequest(StrictModel):
    question: str = Field(min_length=1, max_length=1500)

    @field_validator("question")
    @classmethod
    def usable_question(cls, value: str) -> str:
        if not value.strip() or "\x00" in value:
            raise ValueError("Question must contain usable non-NUL characters")
        return value.strip()


class Claim(StrictModel):
    text: str = Field(min_length=1, max_length=500)
    chunk_id: str
    quote: str = Field(min_length=1, max_length=1200)


class AnswerDraft(StrictModel):
    answerable: bool
    complete: bool
    missing: str = Field(default="", max_length=500)
    claims: list[Claim] = Field(max_length=6)


class Citation(StrictModel):
    document_id: str
    filename: str
    page: int = Field(ge=1)
    chunk_id: str
    quote: str


class AnswerResponse(StrictModel):
    status: Literal["ANSWERED", "PARTIAL", "INSUFFICIENT_EVIDENCE"]
    answer: str
    citations: list[Citation]
