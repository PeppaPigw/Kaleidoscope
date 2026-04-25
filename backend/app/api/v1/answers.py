"""Grounded answer APIs."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.answers.grounded_answer_service import AnswerStyle, GroundedAnswerService

router = APIRouter(prefix="/answers", tags=["answers"])


class GroundedAnswerRequest(BaseModel):
    """Request body for non-streaming grounded answer generation."""

    question: str = Field(..., min_length=1, max_length=2000)
    evidence_pack: dict[str, Any] | None = None
    evidence: list[dict[str, Any]] = Field(default_factory=list, max_length=50)
    style: AnswerStyle = "concise"
    max_sources: int = Field(default=8, ge=1, le=30)
    max_answer_chars: int = Field(default=4000, ge=200, le=12000)


@router.post("/grounded")
async def grounded_answer(body: GroundedAnswerRequest) -> dict[str, Any]:
    """Produce a cited answer and grounding diagnostics from supplied evidence."""
    return GroundedAnswerService().build_answer(
        question=body.question,
        evidence_pack=body.evidence_pack,
        evidence=body.evidence,
        style=body.style,
        max_sources=body.max_sources,
        max_answer_chars=body.max_answer_chars,
    )
