"""Pydantic schemas for researcher analytics responses (§21)."""

from pydantic import BaseModel


class EmergingAuthorItem(BaseModel):
    id: str
    display_name: str
    openalex_id: str | None = None
    orcid: str | None = None
    first_pub: str | None = None
    paper_count: int
    total_citations: int
    h_index: int | None = None


class EmergingAuthorsResponse(BaseModel):
    authors: list[EmergingAuthorItem]


class YearlyPub(BaseModel):
    year: int
    count: int


class PaperSummary(BaseModel):
    id: str
    title: str
    doi: str | None = None
    arxiv_id: str | None = None
    s2_paper_id: str | None = None
    abstract: str | None = None
    keywords: list[str] = []
    published_at: str | None = None
    year: int | None = None
    citation_count: int = 0
    venue: str | None = None
    # Library presence flags
    in_library: bool = False
    library_paper_id: str | None = None
    has_full_text: bool = False
    author_position: int | None = None
    is_corresponding: bool = False


class TopicItem(BaseModel):
    id: str
    label: str
    years: str
    paperCount: int
    active: bool


class AffiliationItem(BaseModel):
    name: str


class CoAuthorItem(BaseModel):
    id: str
    display_name: str
    affiliation: str = ""
    paper_count: int
    last_collab_year: int | None = None


class AuthorProfileResponse(BaseModel):
    id: str
    display_name: str
    openalex_id: str | None = None
    semantic_scholar_id: str | None = None
    scholar_url: str | None = None
    orcid: str | None = None
    h_index: int | None = None
    paper_count: int | None = None
    citation_count: int | None = None
    paper_count_in_library: int
    total_citations_in_library: int
    aliases: list[str] = []
    homepage: str | None = None
    affiliations: list[AffiliationItem] = []
    enriched_at: str | None = None
    timeline: list[YearlyPub]
    top_papers: list[PaperSummary]
    papers: list[PaperSummary] = []
    topics: list[TopicItem] = []
    co_authors: list[CoAuthorItem] = []


class NetworkNode(BaseModel):
    id: str
    label: str
    paper_count: int


class NetworkEdge(BaseModel):
    source: str
    target: str
    weight: int


class CollaborationNetworkResponse(BaseModel):
    nodes: list[NetworkNode]
    edges: list[NetworkEdge]
    center_author_id: str | None = None
