"""Response models for the Kaleidoscope SDK."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class Paper(BaseModel):
    """A single paper record."""

    id: str
    title: str
    abstract: str | None = None
    doi: str | None = None
    arxiv_id: str | None = None
    authors: list[dict[str, Any]] = []

    model_config = {"extra": "allow"}


class SearchResult(BaseModel):
    """Search response envelope."""

    results: list[dict[str, Any]] = []
    total: int = 0
    query: str = ""


class ImportResult(BaseModel):
    """Paper import response."""

    paper_id: str | None = None
    status: str
    message: str = ""


class PaperList(BaseModel):
    """Paginated paper list."""

    papers: list[dict[str, Any]] = []
    total: int = 0


class AnswerResult(BaseModel):
    """QA answer response."""

    answer: str
    sources: list[dict[str, Any]] = []
    confidence: float | None = None


class EvidenceResult(BaseModel):
    """Evidence search response."""

    evidence: list[dict[str, Any]] = []
    query: str = ""


class ClaimResult(BaseModel):
    """Claim verification response."""

    verdict: str = ""
    confidence: float | None = None
    evidence: list[dict[str, Any]] = []


class ResolveResult(BaseModel):
    """Identifier resolution response."""

    matches: list[dict[str, Any]] = []
    action: str = ""
