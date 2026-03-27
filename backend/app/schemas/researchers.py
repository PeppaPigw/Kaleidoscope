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
    published_at: str | None = None
    citation_count: int
    author_position: int
    is_corresponding: bool


class AuthorProfileResponse(BaseModel):
    id: str
    display_name: str
    openalex_id: str | None = None
    orcid: str | None = None
    h_index: int | None = None
    paper_count_in_library: int
    total_citations_in_library: int
    timeline: list[YearlyPub]
    top_papers: list[PaperSummary]


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
