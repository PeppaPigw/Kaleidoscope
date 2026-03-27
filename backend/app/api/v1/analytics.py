"""Analytics API — real-time paper library statistics and insights.

Provides aggregated analytics over the paper library:
- Overview metrics (totals, status breakdown)
- Timeline analysis (papers over time)
- Category distribution
- Top authors by paper count
- Keyword frequency cloud
- Citation network summary
"""

from collections import Counter
from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.models.paper import Paper, PaperReference
from app.models.author import Author, PaperAuthor

router = APIRouter(prefix="/analytics", tags=["analytics"])


# ─── Response Schemas ──────────────────────────────────────────


class OverviewResponse(BaseModel):
    total_papers: int
    with_fulltext: int
    by_status: dict[str, int]
    by_source_type: dict[str, int]
    avg_citation_count: float
    total_authors: int
    total_references: int


class TimelinePoint(BaseModel):
    date: str
    count: int


class TimelineResponse(BaseModel):
    points: list[TimelinePoint]
    granularity: str


class CategoryItem(BaseModel):
    name: str
    count: int


class CategoriesResponse(BaseModel):
    categories: list[CategoryItem]
    total: int


class AuthorItem(BaseModel):
    id: str
    name: str
    paper_count: int
    total_citations: int


class TopAuthorsResponse(BaseModel):
    authors: list[AuthorItem]


class KeywordItem(BaseModel):
    keyword: str
    count: int


class KeywordCloudResponse(BaseModel):
    keywords: list[KeywordItem]
    total_papers_with_keywords: int


class TopCitedItem(BaseModel):
    paper_id: str
    title: str
    internal_citations: int


class CitationNetworkResponse(BaseModel):
    total_nodes: int
    total_edges: int
    resolved_edges: int
    avg_references_per_paper: float
    top_cited: list[TopCitedItem]


class CoverageField(BaseModel):
    field: str
    present: int
    total: int
    pct: float


class DataCoverageResponse(BaseModel):
    total_papers: int
    fields: list[CoverageField]
    institution_coverage_note: str


# ─── Endpoints ─────────────────────────────────────────────────

@router.get("/overview", response_model=OverviewResponse)
async def get_overview(
    db: AsyncSession = Depends(get_db),
):
    """
    Get overview metrics for the entire paper library.

    Returns totals, status breakdown, source types, and citation stats.
    """
    base = select(Paper).where(Paper.deleted_at.is_(None))

    # Total papers
    total = (await db.execute(
        select(func.count()).select_from(base.subquery())
    )).scalar() or 0

    # With full text
    fulltext = (await db.execute(
        select(func.count()).select_from(
            select(Paper).where(
                Paper.deleted_at.is_(None),
                Paper.has_full_text.is_(True),
            ).subquery()
        )
    )).scalar() or 0

    # By ingestion status
    status_rows = (await db.execute(
        select(
            Paper.ingestion_status,
            func.count(),
        ).where(Paper.deleted_at.is_(None))
        .group_by(Paper.ingestion_status)
    )).all()
    by_status = {row[0]: row[1] for row in status_rows}

    # By source type
    source_rows = (await db.execute(
        select(
            Paper.source_type,
            func.count(),
        ).where(Paper.deleted_at.is_(None))
        .group_by(Paper.source_type)
    )).all()
    by_source = {row[0]: row[1] for row in source_rows}

    # Average citation count
    avg_cite = (await db.execute(
        select(func.avg(Paper.citation_count)).where(
            Paper.deleted_at.is_(None)
        )
    )).scalar() or 0.0

    # Total authors (only those linked to live papers)
    total_authors = (await db.execute(
        select(func.count(func.distinct(PaperAuthor.author_id))).select_from(
            PaperAuthor.__table__.join(
                Paper.__table__,
                PaperAuthor.paper_id == Paper.id,
            )
        ).where(Paper.deleted_at.is_(None))
    )).scalar() or 0

    # Total references (only from live papers)
    total_refs = (await db.execute(
        select(func.count()).select_from(
            PaperReference.__table__.join(
                Paper.__table__,
                PaperReference.citing_paper_id == Paper.id,
            )
        ).where(Paper.deleted_at.is_(None))
    )).scalar() or 0

    return OverviewResponse(
        total_papers=total,
        with_fulltext=fulltext,
        by_status=by_status,
        by_source_type=by_source,
        avg_citation_count=round(float(avg_cite), 2),
        total_authors=total_authors,
        total_references=total_refs,
    )


@router.get("/timeline", response_model=TimelineResponse)
async def get_timeline(
    days: int = Query(90, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
):
    """Papers added over time, grouped by week."""
    cutoff = date.today() - timedelta(days=days)

    rows = (await db.execute(
        select(
            func.date_trunc("week", Paper.created_at).label("week"),
            func.count().label("cnt"),
        ).where(
            Paper.deleted_at.is_(None),
            Paper.created_at >= cutoff,
        ).group_by("week").order_by("week")
    )).all()

    points = [
        TimelinePoint(date=row[0].strftime("%Y-%m-%d"), count=row[1])
        for row in rows
    ]
    return TimelineResponse(points=points, granularity="week")


@router.get("/categories", response_model=CategoriesResponse)
async def get_categories(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Category/keyword distribution across the paper library."""
    rows = (await db.execute(
        select(Paper.keywords).where(
            Paper.deleted_at.is_(None),
            Paper.keywords.isnot(None),
        )
    )).all()

    counter: Counter[str] = Counter()
    for (kw_list,) in rows:
        if isinstance(kw_list, list):
            for kw in kw_list:
                if isinstance(kw, str) and kw.strip():
                    counter[kw.strip()] += 1

    top = counter.most_common(limit)
    items = [CategoryItem(name=k, count=v) for k, v in top]
    return CategoriesResponse(categories=items, total=len(counter))


@router.get("/top-authors", response_model=TopAuthorsResponse)
async def get_top_authors(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Authors ranked by paper count in the library (live papers only)."""
    rows = (await db.execute(
        select(
            Author.id,
            Author.display_name,
            func.count(PaperAuthor.paper_id).label("paper_count"),
            func.coalesce(Author.citation_count, 0).label("total_cites"),
        )
        .join(PaperAuthor, Author.id == PaperAuthor.author_id)
        .join(Paper, PaperAuthor.paper_id == Paper.id)
        .where(Paper.deleted_at.is_(None))
        .group_by(Author.id, Author.display_name, Author.citation_count)
        .order_by(func.count(PaperAuthor.paper_id).desc())
        .limit(limit)
    )).all()

    items = [
        AuthorItem(
            id=str(r[0]),
            name=r[1],
            paper_count=r[2],
            total_citations=r[3],
        )
        for r in rows
    ]
    return TopAuthorsResponse(authors=items)


@router.get("/keyword-cloud", response_model=KeywordCloudResponse)
async def get_keyword_cloud(
    limit: int = Query(50, ge=10, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Keyword frequency for word-cloud visualization."""
    rows = (await db.execute(
        select(Paper.keywords).where(
            Paper.deleted_at.is_(None),
            Paper.keywords.isnot(None),
        )
    )).all()

    counter: Counter[str] = Counter()
    papers_with_kw = 0
    for (kw_list,) in rows:
        if isinstance(kw_list, list) and kw_list:
            papers_with_kw += 1
            for kw in kw_list:
                if isinstance(kw, str) and kw.strip():
                    counter[kw.strip().lower()] += 1

    top = counter.most_common(limit)
    items = [KeywordItem(keyword=k, count=v) for k, v in top]
    return KeywordCloudResponse(
        keywords=items,
        total_papers_with_keywords=papers_with_kw,
    )


@router.get("/citation-network", response_model=CitationNetworkResponse)
async def get_citation_network(
    db: AsyncSession = Depends(get_db),
):
    """Citation network summary statistics."""
    total_papers = (await db.execute(
        select(func.count()).select_from(
            select(Paper.id).where(Paper.deleted_at.is_(None)).subquery()
        )
    )).scalar() or 0

    total_refs = (await db.execute(
        select(func.count()).select_from(PaperReference)
    )).scalar() or 0

    resolved = (await db.execute(
        select(func.count()).select_from(
            select(PaperReference.cited_paper_id).where(
                PaperReference.cited_paper_id.isnot(None)
            ).subquery()
        )
    )).scalar() or 0

    avg_refs = total_refs / total_papers if total_papers > 0 else 0.0

    # Top cited papers within library (join to live papers)
    cited_rows = (await db.execute(
        select(
            PaperReference.cited_paper_id,
            func.count().label("cite_count"),
        )
        .join(Paper, PaperReference.citing_paper_id == Paper.id)
        .where(
            PaperReference.cited_paper_id.isnot(None),
            Paper.deleted_at.is_(None),
        )
        .group_by(PaperReference.cited_paper_id)
        .order_by(func.count().desc())
        .limit(10)
    )).all()

    # Batch-fetch titles to avoid N+1
    cited_ids = [row[0] for row in cited_rows]
    if cited_ids:
        title_rows = (await db.execute(
            select(Paper.id, Paper.title).where(Paper.id.in_(cited_ids))
        )).all()
        title_map = {str(r[0]): r[1] for r in title_rows}
    else:
        title_map = {}

    top_cited = [
        TopCitedItem(
            paper_id=str(row[0]),
            title=title_map.get(str(row[0]), "Unknown"),
            internal_citations=row[1],
        )
        for row in cited_rows
    ]

    return CitationNetworkResponse(
        total_nodes=total_papers,
        total_edges=total_refs,
        resolved_edges=resolved,
        avg_references_per_paper=round(avg_refs, 1),
        top_cited=top_cited,
    )


@router.get("/data-coverage", response_model=DataCoverageResponse)
async def get_data_coverage(
    db: AsyncSession = Depends(get_db),
) -> DataCoverageResponse:
    """
    Report field-level data coverage across the paper library.

    Use this to understand what downstream analytics are reliable:
    - published_at needed for timeline/trend analytics
    - keywords needed for keyword-cloud and hot-topic detection
    - abstract needed for BERTopic clustering and QA
    - citation_count needed for sleeping-beauty and emerging-author signals
    - authors/institutions needed for researcher analytics
    """
    total = (await db.execute(
        select(func.count()).select_from(
            select(Paper.id).where(Paper.deleted_at.is_(None)).subquery()
        )
    )).scalar() or 0

    if total == 0:
        return DataCoverageResponse(
            total_papers=0,
            fields=[],
            institution_coverage_note="No papers in library.",
        )

    async def _count(condition) -> int:
        return (await db.execute(
            select(func.count()).select_from(
                select(Paper.id).where(Paper.deleted_at.is_(None), condition).subquery()
            )
        )).scalar() or 0

    with_date = await _count(Paper.published_at.isnot(None))
    # Non-empty keyword array (jsonb_array_length > 0 guards against [] entries)
    with_kw = (await db.execute(
        select(func.count()).select_from(
            select(Paper.id).where(
                Paper.deleted_at.is_(None),
                Paper.keywords.isnot(None),
                func.jsonb_array_length(Paper.keywords) > 0,
            ).subquery()
        )
    )).scalar() or 0
    # Non-blank abstract
    with_abs = (await db.execute(
        select(func.count()).select_from(
            select(Paper.id).where(
                Paper.deleted_at.is_(None),
                Paper.abstract.isnot(None),
                func.length(func.coalesce(Paper.abstract, "")) > 0,
            ).subquery()
        )
    )).scalar() or 0
    # Citation data ready means the field was fetched/updated (not just defaulting to 0)
    with_cite = await _count(Paper.citation_count_updated_at.isnot(None))
    with_fulltext = await _count(Paper.has_full_text.is_(True))

    # Authors coverage: papers with ≥1 linked author
    with_authors = (await db.execute(
        select(func.count(func.distinct(PaperAuthor.paper_id))).select_from(
            PaperAuthor.__table__.join(
                Paper.__table__, PaperAuthor.paper_id == Paper.id
            )
        ).where(Paper.deleted_at.is_(None))
    )).scalar() or 0

    # Institution coverage: papers with ≥1 author having institution
    from app.models.author import Institution
    with_inst = (await db.execute(
        select(func.count(func.distinct(PaperAuthor.paper_id))).select_from(
            PaperAuthor.__table__
            .join(Paper.__table__, PaperAuthor.paper_id == Paper.id)
            .join(Author.__table__, PaperAuthor.author_id == Author.id)
        ).where(
            Paper.deleted_at.is_(None),
            Author.institution_id.isnot(None),
        )
    )).scalar() or 0

    def _pct(n: int) -> float:
        return round(100.0 * n / total, 1) if total else 0.0

    fields = [
        CoverageField(field="published_at",  present=with_date,     total=total, pct=_pct(with_date)),
        CoverageField(field="keywords",       present=with_kw,       total=total, pct=_pct(with_kw)),
        CoverageField(field="abstract",       present=with_abs,      total=total, pct=_pct(with_abs)),
        CoverageField(field="citation_count", present=with_cite,     total=total, pct=_pct(with_cite)),
        CoverageField(field="full_text",      present=with_fulltext, total=total, pct=_pct(with_fulltext)),
        CoverageField(field="authors_linked", present=with_authors,  total=total, pct=_pct(with_authors)),
        CoverageField(field="institution_linked", present=with_inst, total=total, pct=_pct(with_inst)),
    ]

    inst_pct = _pct(with_inst)
    if inst_pct >= 50:
        note = f"Good ({inst_pct}% papers have institution). Institution analytics are reliable."
    elif inst_pct >= 20:
        note = f"Partial ({inst_pct}% papers have institution). Institution analytics may be biased."
    else:
        note = f"Low ({inst_pct}% papers have institution). Skip institution analytics for now."

    return DataCoverageResponse(
        total_papers=total,
        fields=fields,
        institution_coverage_note=note,
    )
