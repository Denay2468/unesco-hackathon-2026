from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from database import get_session
from models import (
    Case, Clue, Score,
    CaseSummary, CaseDetail, ClueResponse,
    VerifyRequest, VerifyResponse, LeaderboardEntry,
)

router = APIRouter(prefix="/api", tags=["Academy"])

POINTS_MAP = {1: 100, 2: 75, 3: 50}  # points based on tools used (placeholder)


# ── GET /api/cases ─────────────────────────────────────────────────────────

@router.get("/cases", response_model=List[CaseSummary])
def list_cases(session: Session = Depends(get_session)):
    cases = session.exec(select(Case).order_by(Case.id)).all()
    return cases


# ── GET /api/cases/{case_id} ───────────────────────────────────────────────

@router.get("/cases/{case_id}", response_model=CaseDetail)
def get_case(case_id: int, session: Session = Depends(get_session)):
    case = session.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


# ── GET /api/cases/{case_id}/tools/{tool_type} ─────────────────────────────

@router.get("/cases/{case_id}/tools/{tool_type}", response_model=ClueResponse)
def get_clue(case_id: int, tool_type: str, session: Session = Depends(get_session)):
    case = session.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    clue = session.exec(
        select(Clue).where(Clue.case_id == case_id, Clue.tool_type == tool_type)
    ).first()

    if not clue:
        raise HTTPException(
            status_code=404,
            detail=f"No clue found for tool '{tool_type}' on this case",
        )
    return clue


# ── POST /api/cases/{case_id}/verify ──────────────────────────────────────

@router.post("/cases/{case_id}/verify", response_model=VerifyResponse)
def verify_guess(
    case_id: int,
    body: VerifyRequest,
    session: Session = Depends(get_session),
):
    case = session.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    guess = body.guess.strip().lower()
    correct = guess == case.correct_answer.lower()
    points = 100 if correct else 0

    # Persist score if username provided
    if body.username and correct:
        session.add(Score(username=body.username, score=points))
        session.commit()

    return VerifyResponse(
        correct=correct,
        correct_answer=case.correct_answer,
        explanation=case.explanation,
        points_earned=points,
    )


# ── GET /api/leaderboard ───────────────────────────────────────────────────

@router.get("/leaderboard", response_model=List[LeaderboardEntry])
def leaderboard(session: Session = Depends(get_session)):
    scores = session.exec(
        select(Score).order_by(Score.score.desc()).limit(10)  # type: ignore[arg-type]
    ).all()
    return scores
