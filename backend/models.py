from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field


class Case(SQLModel, table=True):
    __tablename__ = "cases"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    story: str
    media_url: str
    media_type: str  # "image", "video", "audio"
    correct_answer: str  # "real" or "fake"
    explanation: str


class Clue(SQLModel, table=True):
    __tablename__ = "clues"

    id: Optional[int] = Field(default=None, primary_key=True)
    case_id: int = Field(foreign_key="cases.id")
    tool_type: str  # "lighting", "metadata", "reverse_image", "voice_artifacts"
    clue_text: str


class Score(SQLModel, table=True):
    __tablename__ = "scores"

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str
    score: int
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ── Pydantic response schemas (no table=True) ──────────────────────────────

class CaseSummary(SQLModel):
    id: int
    title: str
    media_type: str
    media_url: str


class CaseDetail(SQLModel):
    id: int
    title: str
    story: str
    media_url: str
    media_type: str


class ClueResponse(SQLModel):
    tool_type: str
    clue_text: str


class VerifyRequest(SQLModel):
    guess: str   # "real" or "fake"
    username: Optional[str] = None


class VerifyResponse(SQLModel):
    correct: bool
    correct_answer: str
    explanation: str
    points_earned: int


class DetectResponse(SQLModel):
    confidence: float        # 0.0 – 1.0
    percentage: str          # e.g. "87%"
    verdict: str             # "Likely AI-generated" | "Likely Real"
    file_type: str


class LeaderboardEntry(SQLModel):
    username: str
    score: int
    created_at: datetime
