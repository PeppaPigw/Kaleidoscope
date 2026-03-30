"""Content API — paper content retrieval and URL-based import.

Provides:
- GET /papers/{id}/content — retrieve markdown content + metadata
- POST /papers/import-url — import paper from URL via MinerU
- POST /papers/{id}/reparse — re-parse existing paper via MinerU
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db

router = APIRouter(prefix="/papers", tags=["content"])


class ImportUrlRequest(BaseModel):
    url: str
    title: str | None = None
    is_html: bool = False


class ReparseRequest(BaseModel):
    url: str | None = None
    is_html: bool | None = None  # None = auto-detect from stored URL metadata


class ContentResponse(BaseModel):
    paper_id: str
    title: str | None
    abstract: str | None
    has_full_text: bool
    markdown: str
    format: str  # "markdown", "reconstructed", "abstract_only", "metadata_only"
    remote_urls: list[dict] | None = None
    markdown_provenance: dict | None = None
    sections: list[dict] = []
    figures: list[dict] = []


class ImportUrlResponse(BaseModel):
    paper_id: str
    title: str
    status: str
    error: str | None = None
    markdown_length: int | None = None
    sections: int | None = None
    references: int | None = None


@router.get("/{paper_id}/content", response_model=ContentResponse)
async def get_paper_content(
    paper_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get paper content as markdown + structured metadata.

    Returns the full markdown text, sections, and provenance.
    """
    from app.models.paper import Paper

    result = await db.execute(
        select(Paper).where(Paper.id == paper_id, Paper.deleted_at.is_(None))
    )
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    # Build content response with fallback chain
    if paper.full_text_markdown:
        markdown = paper.full_text_markdown
        fmt = "markdown"
    elif paper.parsed_sections:
        # Reconstruct from parsed_sections
        md_parts = []
        for sec in paper.parsed_sections:
            level = sec.get("level", 1)
            heading = sec.get("title") or sec.get("heading", "")
            md_parts.append(f"{'#' * level} {heading}\n")
            for p in sec.get("paragraphs", []):
                md_parts.append(p + "\n")
            md_parts.append("")
        markdown = "\n".join(md_parts)
        fmt = "reconstructed"
    elif paper.abstract:
        markdown = f"# {paper.title}\n\n{paper.abstract}"
        fmt = "abstract_only"
    else:
        markdown = f"# {paper.title}\n\n*No full text available.*"
        fmt = "metadata_only"

    return ContentResponse(
        paper_id=str(paper.id),
        title=paper.title,
        abstract=paper.abstract,
        has_full_text=paper.has_full_text,
        markdown=markdown,
        format=fmt,
        remote_urls=paper.remote_urls,
        markdown_provenance=paper.markdown_provenance,
        sections=paper.parsed_sections or [],
        figures=paper.parsed_figures or [],
    )


@router.post("/import-url", response_model=ImportUrlResponse, status_code=201)
async def import_from_url(
    req: ImportUrlRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Import a paper from URL using MinerU for content extraction.

    Creates a new paper record and extracts content as markdown.
    Raises HTTP 502 if MinerU extraction fails.
    """
    from app.models.paper import Paper
    from app.services.parsing.mineru_service import MinerUParsingService
    from app.utils.doi import extract_doi_from_url

    # Try to extract DOI from URL
    doi = extract_doi_from_url(req.url)

    # Check for duplicates
    if doi:
        existing = await db.execute(
            select(Paper).where(Paper.doi == doi, Paper.deleted_at.is_(None))
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=409,
                detail=f"Paper with DOI {doi} already exists",
            )

    # Create paper record
    paper = Paper(
        title=req.title or f"Importing from {req.url[:60]}...",
        doi=doi,
        source_type="remote",
        ingestion_status="importing",
        remote_urls=[{"url": req.url, "source": "user_import", "type": "html" if req.is_html else "pdf"}],
    )
    db.add(paper)
    await db.flush()

    # Parse via MinerU
    svc = MinerUParsingService(db)
    try:
        result = await svc.parse_from_url(
            paper_id=str(paper.id),
            url=req.url,
            is_html=req.is_html,
        )
    finally:
        await svc.close()

    # Propagate parse failures as HTTP errors
    if result.get("status") == "error":
        # NOTE: Intentional explicit commit — saves the paper record and failure
        # state before raising, so the import attempt is traceable even on error.
        await db.commit()
        raise HTTPException(
            status_code=502,
            detail=result.get("error", "MinerU extraction failed"),
        )

    # NOTE: Intentional explicit commit for import completion.
    await db.commit()

    return ImportUrlResponse(
        paper_id=str(paper.id),
        title=paper.title,
        status=result["status"],
        markdown_length=result.get("markdown_length"),
        sections=result.get("sections"),
        references=result.get("references"),
    )


@router.post("/{paper_id}/reparse", response_model=ImportUrlResponse)
async def reparse_paper(
    paper_id: uuid.UUID,
    req: ReparseRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Re-parse an existing paper via MinerU.

    Uses the paper's stored URL or a provided override URL.
    Auto-detects is_html from stored URL metadata if not explicitly set.
    """
    from app.models.paper import Paper
    from app.services.parsing.mineru_service import MinerUParsingService

    result = await db.execute(
        select(Paper).where(Paper.id == paper_id, Paper.deleted_at.is_(None))
    )
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    # Determine URL and is_html
    url = req.url
    is_html = req.is_html

    if not url and paper.remote_urls:
        stored = paper.remote_urls[0]
        url = stored.get("url")
        # Auto-detect is_html from stored metadata if not explicitly set
        if is_html is None:
            is_html = stored.get("type") == "html"

    if not url:
        raise HTTPException(
            status_code=400,
            detail="No URL available for reparsing. Provide a URL in the request.",
        )

    if is_html is None:
        is_html = False

    svc = MinerUParsingService(db)
    try:
        parse_result = await svc.parse_from_url(
            paper_id=str(paper_id),
            url=url,
            is_html=is_html,
        )
    finally:
        await svc.close()

    # Propagate parse failures as HTTP errors
    if parse_result.get("status") == "error":
        # NOTE: Intentional explicit commit — saves the paper record and failure
        # state before raising, so the import attempt is traceable even on error.
        await db.commit()
        raise HTTPException(
            status_code=502,
            detail=parse_result.get("error", "MinerU extraction failed"),
        )

    # NOTE: Intentional explicit commit for import completion.
    await db.commit()

    return ImportUrlResponse(
        paper_id=str(paper_id),
        title=paper.title,
        status=parse_result["status"],
        markdown_length=parse_result.get("markdown_length"),
        sections=parse_result.get("sections"),
        references=parse_result.get("references"),
    )


@router.get("/{paper_id}/import-status")
async def get_import_status(
    paper_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Return current ingestion status for a paper.

    Clients can poll this after POST /papers/import-url to track progress.
    Status values: 'pending', 'importing', 'parsed', 'ready', 'error'.
    """
    from app.models.paper import Paper

    result = await db.execute(
        select(Paper).where(Paper.id == paper_id, Paper.deleted_at.is_(None))
    )
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    return {
        "paper_id": str(paper.id),
        "title": paper.title,
        "ingestion_status": paper.ingestion_status,
        "has_full_text": paper.has_full_text,
        "created_at": paper.created_at.isoformat() if paper.created_at else None,
        "updated_at": paper.updated_at.isoformat() if paper.updated_at else None,
        "error_message": (paper.raw_metadata or {}).get("import_error"),
    }
