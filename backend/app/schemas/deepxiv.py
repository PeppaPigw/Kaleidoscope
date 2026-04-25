"""Pydantic schemas for DeepXiv API endpoints."""

from pydantic import BaseModel, Field


# ── Search ────────────────────────────────────────────


class DeepXivSearchResult(BaseModel):
    arxiv_id: str
    title: str
    abstract: str | None = None
    authors: list = []
    categories: list[str] = []
    citations: int = 0
    score: float = 0.0
    token_count: int | None = None


class DeepXivSearchResponse(BaseModel):
    total: int = 0
    results: list[DeepXivSearchResult] = []


# ── Paper metadata ────────────────────────────────────


class DeepXivSection(BaseModel):
    name: str
    idx: int = 0
    tldr: str | None = None
    token_count: int = 0


class DeepXivHeadResponse(BaseModel):
    arxiv_id: str
    title: str
    abstract: str | None = None
    authors: list = []
    sections: list[DeepXivSection] = []
    token_count: int = 0
    citations: int = 0
    publish_at: str | None = None
    venue: str | None = None
    journal_name: str | None = None
    keywords: list[str] = []
    tldr: str | None = None
    github_url: str | None = None
    src_url: str | None = None
    categories: list[str] = []


class DeepXivBriefResponse(BaseModel):
    arxiv_id: str
    title: str
    tldr: str | None = None
    keywords: list[str] = []
    publish_at: str | None = None
    citations: int = 0
    src_url: str | None = None
    github_url: str | None = None


class DeepXivSectionResponse(BaseModel):
    arxiv_id: str
    section_name: str
    content: str


class DeepXivPreviewResponse(BaseModel):
    arxiv_id: str | None = None
    text: str = ""
    is_truncated: bool = False
    total_characters: int = 0
    preview_characters: int = 0


# ── PMC ───────────────────────────────────────────────


class DeepXivPMCHeadResponse(BaseModel):
    pmc_id: str
    title: str
    doi: str | None = None
    abstract: str | None = None
    authors: list = []
    categories: list[str] = []
    publish_at: str | None = None


# ── Trending ──────────────────────────────────────────


class DeepXivTrendingResponse(BaseModel):
    days: int = 7
    generated_at: str | None = None
    papers: list[dict] = []
    total: int = 0


# ── Social Impact ─────────────────────────────────────


class DeepXivSocialImpactResponse(BaseModel):
    arxiv_id: str
    total_tweets: int = 0
    total_likes: int = 0
    total_views: int = 0
    total_replies: int = 0
    first_seen_date: str | None = None
    last_seen_date: str | None = None


# ── Agent ─────────────────────────────────────────────


class DeepXivAgentRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    reset_papers: bool = False


class DeepXivAgentResponse(BaseModel):
    answer: str
    papers_loaded: int = 0
