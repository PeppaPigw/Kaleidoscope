"""Paper deduplication — prevent duplicate entries using DOI and title matching."""

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.paper import Paper
from app.utils.doi import normalize_doi
from app.utils.text import normalize_title, titles_are_similar

logger = structlog.get_logger(__name__)


class DedupResult:
    """Result of a deduplication check."""

    def __init__(
        self,
        is_duplicate: bool,
        existing_paper_id: str | None = None,
        match_type: str | None = None,  # "doi", "title", None
        similarity_score: float | None = None,
    ):
        self.is_duplicate = is_duplicate
        self.existing_paper_id = existing_paper_id
        self.match_type = match_type
        self.similarity_score = similarity_score


class DeduplicatorService:
    """
    Deduplicate papers before insertion.

    Strategy:
    1. DOI exact match (highest confidence)
    2. arXiv ID exact match
    3. Title fuzzy match (token-sort ratio >= 0.90)
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def check_duplicate(
        self,
        doi: str | None = None,
        arxiv_id: str | None = None,
        title: str | None = None,
    ) -> DedupResult:
        """
        Check if a paper already exists in the database.

        Checks in order: DOI → arXiv ID → title fuzzy match.
        """
        # 1. DOI exact match
        if doi:
            normalized_doi = normalize_doi(doi)
            if normalized_doi:
                result = await self.db.execute(
                    select(Paper.id).where(
                        Paper.doi == normalized_doi,
                        Paper.deleted_at.is_(None),
                    )
                )
                existing = result.scalar_one_or_none()
                if existing:
                    logger.info("dedup_doi_match", doi=normalized_doi, existing_id=str(existing))
                    return DedupResult(
                        is_duplicate=True,
                        existing_paper_id=str(existing),
                        match_type="doi",
                        similarity_score=1.0,
                    )

        # 2. arXiv ID exact match
        if arxiv_id:
            result = await self.db.execute(
                select(Paper.id).where(
                    Paper.arxiv_id == arxiv_id,
                    Paper.deleted_at.is_(None),
                )
            )
            existing = result.scalar_one_or_none()
            if existing:
                logger.info("dedup_arxiv_match", arxiv_id=arxiv_id, existing_id=str(existing))
                return DedupResult(
                    is_duplicate=True,
                    existing_paper_id=str(existing),
                    match_type="arxiv_id",
                    similarity_score=1.0,
                )

        # 3. Title fuzzy match
        if title:
            normalized = normalize_title(title)
            if len(normalized) > 10:  # Skip very short titles to avoid false matches
                # Fetch candidate titles for comparison
                # Optimization: only compare with recent papers or use pg_trgm for DB-side matching
                result = await self.db.execute(
                    select(Paper.id, Paper.title).where(
                        Paper.deleted_at.is_(None),
                    ).limit(5000)  # Safety limit
                )
                candidates = result.all()

                for candidate_id, candidate_title in candidates:
                    if titles_are_similar(title, candidate_title, threshold=0.90):
                        logger.info(
                            "dedup_title_match",
                            new_title=title[:80],
                            existing_title=candidate_title[:80],
                            existing_id=str(candidate_id),
                        )
                        return DedupResult(
                            is_duplicate=True,
                            existing_paper_id=str(candidate_id),
                            match_type="title",
                        )

        return DedupResult(is_duplicate=False)
