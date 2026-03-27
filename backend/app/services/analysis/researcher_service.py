"""Researcher Analytics Service — §21 from FeasibilityAnalysis.md.

Provides:
- Emerging author ranking (new authors with high recent citation rates)
- Author profile with timeline and top papers
- Author collaboration network (co-authorship graph edges)

All queries run against the existing PostgreSQL library (no external APIs).
"""

from collections import defaultdict
from datetime import date, timedelta

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.paper import Paper
from app.models.author import Author, PaperAuthor

logger = structlog.get_logger(__name__)


class ResearcherService:
    """Analytics over the author/paper graph in the local library."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ─── Emerging Authors ─────────────────────────────────────────

    async def emerging_authors(
        self,
        top_k: int = 20,
        recent_years: int = 2,
    ) -> list[dict]:
        """
        Rank authors who have their earliest library paper within the last
        *recent_years*, sorted by cumulative citation count (descending).

        This is a §21 "Rising Stars" proxy: new-to-library authors with
        high-citation papers.
        """
        cutoff = date.today() - timedelta(days=recent_years * 365)

        # Subquery: earliest paper date per author in the library
        earliest_sq = (
            select(
                PaperAuthor.author_id,
                func.min(Paper.published_at).label("first_pub"),
                func.sum(Paper.citation_count).label("total_citations"),
                func.count(PaperAuthor.paper_id).label("paper_count"),
            )
            .join(Paper, PaperAuthor.paper_id == Paper.id)
            .where(
                Paper.deleted_at.is_(None),
                Paper.published_at.isnot(None),
            )
            .group_by(PaperAuthor.author_id)
            .subquery()
        )

        result = await self.db.execute(
            select(
                Author.id,
                Author.display_name,
                Author.openalex_id,
                Author.orcid,
                Author.institution_id,
                Author.h_index,
                earliest_sq.c.first_pub,
                earliest_sq.c.total_citations,
                earliest_sq.c.paper_count,
            )
            .join(earliest_sq, Author.id == earliest_sq.c.author_id)
            .where(
                earliest_sq.c.first_pub >= cutoff,
                earliest_sq.c.total_citations > 0,
            )
            .order_by(earliest_sq.c.total_citations.desc())
            .limit(top_k)
        )

        rows = result.all()
        return [
            {
                "id": str(r.id),
                "display_name": r.display_name,
                "openalex_id": r.openalex_id,
                "orcid": r.orcid,
                "first_pub": str(r.first_pub),
                "paper_count": r.paper_count,
                "total_citations": r.total_citations or 0,
                "h_index": r.h_index,
            }
            for r in rows
        ]

    # ─── Author Profile ───────────────────────────────────────────

    async def get_author_profile(self, author_id: str) -> dict | None:
        """
        Return a full profile for the given author: metadata, library papers,
        per-year publication timeline, and top papers by citation count.
        """
        result = await self.db.execute(
            select(Author).where(Author.id == author_id)
        )
        author = result.scalar_one_or_none()
        if not author:
            return None

        # All papers for this author in our library
        papers_result = await self.db.execute(
            select(Paper, PaperAuthor.position, PaperAuthor.is_corresponding)
            .join(PaperAuthor, Paper.id == PaperAuthor.paper_id)
            .where(
                PaperAuthor.author_id == author_id,
                Paper.deleted_at.is_(None),
            )
            .order_by(Paper.published_at.desc())
        )
        rows = papers_result.all()

        # Build timeline
        year_counts: dict[int, int] = defaultdict(int)
        top_papers = []
        total_citations = 0
        for paper, position, is_corr in rows:
            if paper.published_at:
                year_counts[paper.published_at.year] += 1
            total_citations += paper.citation_count or 0
            top_papers.append({
                "id": str(paper.id),
                "title": paper.title,
                "doi": paper.doi,
                "published_at": str(paper.published_at) if paper.published_at else None,
                "citation_count": paper.citation_count or 0,
                "author_position": position,
                "is_corresponding": is_corr,
            })

        # Sort top papers by citation count
        top_papers.sort(key=lambda x: x["citation_count"], reverse=True)

        timeline = [
            {"year": yr, "count": cnt}
            for yr, cnt in sorted(year_counts.items())
        ]

        return {
            "id": str(author.id),
            "display_name": author.display_name,
            "openalex_id": author.openalex_id,
            "orcid": author.orcid,
            "h_index": author.h_index,
            "paper_count_in_library": len(rows),
            "total_citations_in_library": total_citations,
            "timeline": timeline,
            "top_papers": top_papers[:10],
        }

    # ─── Collaboration Network ────────────────────────────────────

    async def collaboration_network(
        self,
        author_id: str | None = None,
        top_k: int = 50,
        min_collaborations: int = 2,
    ) -> dict:
        """
        Build a co-authorship network from shared papers.

        If *author_id* is given, returns the ego-network for that author
        (all co-authors and their mutual links within 1 hop).
        Otherwise returns the global co-authorship graph limited to the
        *top_k* most prolific authors.

        Returns:
            nodes: list of {id, label, paper_count}
            edges: list of {source, target, weight (paper count)}
        """
        if author_id:
            # Find all papers this author is on
            paper_ids_result = await self.db.execute(
                select(PaperAuthor.paper_id)
                .join(Paper, PaperAuthor.paper_id == Paper.id)
                .where(
                    PaperAuthor.author_id == author_id,
                    Paper.deleted_at.is_(None),
                )
            )
            paper_ids = [str(r[0]) for r in paper_ids_result.all()]

            # Get all co-authors on those papers
            co_result = await self.db.execute(
                select(PaperAuthor.author_id, PaperAuthor.paper_id)
                .join(Paper, PaperAuthor.paper_id == Paper.id)
                .where(
                    PaperAuthor.paper_id.in_(paper_ids),
                    Paper.deleted_at.is_(None),
                )
            )
            rows = co_result.all()
        else:
            # Global: restrict to most-published top_k authors
            top_author_sq = (
                select(PaperAuthor.author_id, func.count().label("n"))
                .join(Paper, PaperAuthor.paper_id == Paper.id)
                .where(Paper.deleted_at.is_(None))
                .group_by(PaperAuthor.author_id)
                .order_by(func.count().desc())
                .limit(top_k)
                .subquery()
            )

            co_result = await self.db.execute(
                select(PaperAuthor.author_id, PaperAuthor.paper_id)
                .join(Paper, PaperAuthor.paper_id == Paper.id)
                .join(top_author_sq, PaperAuthor.author_id == top_author_sq.c.author_id)
                .where(Paper.deleted_at.is_(None))
            )
            rows = co_result.all()

        # Build paper → author set mapping
        paper_to_authors: dict[str, set[str]] = defaultdict(set)
        for author_uid, paper_uid in rows:
            paper_to_authors[str(paper_uid)].add(str(author_uid))

        # All author IDs that appear in this dataset (guarantee nodes are always returned)
        all_dataset_authors: set[str] = set()
        for authors in paper_to_authors.values():
            all_dataset_authors.update(authors)
        if author_id:
            all_dataset_authors.add(author_id)

        # Count co-authorship edges
        from itertools import combinations
        edge_weight: dict[tuple[str, str], int] = defaultdict(int)
        for authors in paper_to_authors.values():
            sorted_authors = sorted(authors)
            for a, b in combinations(sorted_authors, 2):
                edge_weight[(a, b)] += 1

        # Filter edges by min_collaborations threshold
        filtered_edges = [
            (a, b, w)
            for (a, b), w in edge_weight.items()
            if w >= min_collaborations
        ]

        # Node set: for global network, ALL dataset authors appear as nodes even
        # if they have no edge above the threshold (fixes reviewer finding #3).
        # For ego network, only authors in the ego + filtered neighbors are shown.
        if author_id:
            author_ids_in_graph: set[str] = {author_id}
            for a, b, _ in filtered_edges:
                author_ids_in_graph.add(a)
                author_ids_in_graph.add(b)
        else:
            # Keep all top_k authors regardless of edge density
            author_ids_in_graph = all_dataset_authors

        # Fetch author display names
        if author_ids_in_graph:
            from uuid import UUID as UUIDType
            uuid_ids = []
            for aid in author_ids_in_graph:
                try:
                    uuid_ids.append(UUIDType(aid))
                except ValueError:
                    continue

            names_result = await self.db.execute(
                select(Author.id, Author.display_name)
                .where(Author.id.in_(uuid_ids))
            )
            name_map = {str(r.id): r.display_name for r in names_result.all()}
        else:
            name_map = {}

        # Count papers per author
        paper_count_map: dict[str, int] = defaultdict(int)
        for authors in paper_to_authors.values():
            for a in authors:
                if a in author_ids_in_graph:
                    paper_count_map[a] += 1

        nodes = [
            {
                "id": aid,
                "label": name_map.get(aid, aid),
                "paper_count": paper_count_map.get(aid, 0),
            }
            for aid in author_ids_in_graph
        ]
        edges = [
            {"source": a, "target": b, "weight": w}
            for a, b, w in sorted(filtered_edges, key=lambda x: -x[2])
        ]

        return {
            "nodes": nodes,
            "edges": edges,
            "center_author_id": author_id,
        }
