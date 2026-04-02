"""Pydantic schemas for trend and topic analytics responses (§10)."""

from pydantic import BaseModel


# ─── Keywords ──────────────────────────────────────────────────────────────


class YearCount(BaseModel):
    year: int
    count: int


class KeywordTrendItem(BaseModel):
    keyword: str
    total_count: int
    growth_rate: float
    trend: str  # "rising" | "stable" | "declining"
    per_year: dict[str, int]


class HotKeywordsResponse(BaseModel):
    keywords: list[KeywordTrendItem]


class KeywordTimePoint(BaseModel):
    year: int
    count: int


class KeywordTimeseriesItem(BaseModel):
    keyword: str
    series: list[KeywordTimePoint]
    total: int


class KeywordTimeseriesResponse(BaseModel):
    keywords: list[KeywordTimeseriesItem]
    years_covered: list[int]


class CooccurrenceEdge(BaseModel):
    keyword_a: str
    keyword_b: str
    count: int


class KeywordCooccurrenceResponse(BaseModel):
    edges: list[CooccurrenceEdge]
    total_papers_analyzed: int


# ─── Topics ────────────────────────────────────────────────────────────────


class TopicItem(BaseModel):
    id: str
    label: str
    keywords: list[str]
    paper_count: int
    trend_direction: str
    description: str | None = None


class TopicsResponse(BaseModel):
    topics: list[TopicItem]


class TopicPaperItem(BaseModel):
    id: str
    title: str
    doi: str | None = None
    published_at: str | None = None
    probability: float


class TopicDetailResponse(TopicItem):
    papers: list[TopicPaperItem]


# ─── Sleeping papers ───────────────────────────────────────────────────────


class SleepingPaperItem(BaseModel):
    id: str
    title: str
    doi: str | None = None
    published_at: str | None = None
    citation_count: int
    years_old: int | None = None
    # Proxy score: citation_count / sqrt(years_old) if available
    proxy_score: float | None = None


class SleepingPapersResponse(BaseModel):
    papers: list[SleepingPaperItem]
    note: str = (
        "Ranking by proxy score (citation_count normalized by age). "
        "True spike detection requires citation history."
    )
