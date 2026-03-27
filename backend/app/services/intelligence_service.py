"""Paper intelligence service — similarity, reading paths, and citation timelines."""

from collections import defaultdict, deque

import structlog
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.author import PaperAuthor
from app.models.paper import Paper, PaperReference

logger = structlog.get_logger(__name__)


class IntelligenceService:
    """Query-oriented paper intelligence helpers for the local library."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_similar_papers(self, paper_id: str, top_k: int = 10) -> list[dict]:
        """Find similar papers via keyword overlap, then shared authors as fallback."""
        if top_k <= 0:
            return []

        paper = await self._get_paper(paper_id)
        if not paper:
            logger.debug("similar_papers_root_missing", paper_id=paper_id)
            return []

        similar = await self._find_keyword_similar_papers(
            paper,
            top_k=top_k,
            exclude_ids={paper_id},
        )
        if similar:
            return similar

        return await self._find_author_overlap_papers(
            paper_id,
            top_k=top_k,
            exclude_ids={paper_id},
        )

    async def get_reading_order(self, paper_id: str, max_papers: int = 20) -> list[dict]:
        """Build a natural reading order from a paper and its citation neighborhood."""
        if max_papers <= 0:
            return []

        root_paper = await self._get_paper(paper_id)
        if not root_paper:
            logger.debug("reading_order_root_missing", paper_id=paper_id)
            return []

        depths, _ = await self._bfs_citation_tree(paper_id, max_depth=2)
        papers = await self._load_papers(depths.keys())

        ordered_ids = sorted(
            papers.keys(),
            key=lambda pid: (
                self._sortable_date(papers[pid].published_at),
                depths.get(pid, 0),
                papers[pid].title.lower(),
            ),
        )

        if len(ordered_ids) > max_papers and paper_id not in ordered_ids[:max_papers]:
            ordered_ids = ordered_ids[: max_papers - 1] + [paper_id]
            ordered_ids.sort(
                key=lambda pid: (
                    self._sortable_date(papers[pid].published_at),
                    depths.get(pid, 0),
                    papers[pid].title.lower(),
                )
            )
        else:
            ordered_ids = ordered_ids[:max_papers]

        return [
            {
                "id": pid,
                "title": papers[pid].title,
                "doi": papers[pid].doi,
                "published_at": self._serialize_date(papers[pid].published_at),
                "depth": depths.get(pid, 0),
                "is_root": pid == paper_id,
            }
            for pid in ordered_ids
        ]

    async def get_prerequisites(self, paper_id: str, top_k: int = 10) -> list[dict]:
        """Return foundational cited papers published before the root paper."""
        if top_k <= 0:
            return []

        root_paper = await self._get_paper(paper_id)
        if not root_paper:
            logger.debug("prerequisites_root_missing", paper_id=paper_id)
            return []

        ref_result = await self.db.execute(
            select(PaperReference.cited_paper_id).where(
                PaperReference.citing_paper_id == paper_id,
                PaperReference.cited_paper_id.is_not(None),
            )
        )
        cited_ids = [str(row.cited_paper_id) for row in ref_result.all() if row.cited_paper_id]
        if not cited_ids:
            return []

        query = select(Paper).where(
            Paper.id.in_(cited_ids),
            Paper.deleted_at.is_(None),
        )
        if root_paper.published_at:
            query = query.where(
                Paper.published_at.is_not(None),
                Paper.published_at < root_paper.published_at,
            )

        result = await self.db.execute(
            query.order_by(
                Paper.citation_count.desc().nullslast(),
                Paper.published_at.asc().nullslast(),
            )
        )
        papers = list(result.scalars().all())[:top_k]

        return [
            {
                "id": str(paper.id),
                "title": paper.title,
                "doi": paper.doi,
                "published_at": self._serialize_date(paper.published_at),
                "citation_count": paper.citation_count or 0,
                "rationale": "highly cited foundational work",
            }
            for paper in papers
        ]

    async def get_related_work_pack(self, paper_id: str, max_papers: int = 30) -> dict:
        """Combine direct references with keyword-similar papers into one pack."""
        root_paper = await self._get_paper(paper_id)
        if not root_paper:
            logger.debug("related_work_root_missing", paper_id=paper_id)
            return {
                "root_paper": None,
                "pack": [],
                "total": 0,
            }

        if max_papers <= 0:
            return {
                "root_paper": {"id": str(root_paper.id), "title": root_paper.title},
                "pack": [],
                "total": 0,
            }

        pack: list[dict] = []
        seen_ids: set[str] = {paper_id}

        ref_result = await self.db.execute(
            select(Paper, PaperReference.position)
            .join(PaperReference, Paper.id == PaperReference.cited_paper_id)
            .where(
                PaperReference.citing_paper_id == paper_id,
                PaperReference.cited_paper_id.is_not(None),
                Paper.deleted_at.is_(None),
            )
            .order_by(
                PaperReference.position.asc().nullslast(),
                Paper.citation_count.desc().nullslast(),
            )
        )
        for paper, _position in ref_result.all():
            pid = str(paper.id)
            if pid in seen_ids or len(pack) >= max_papers:
                continue
            seen_ids.add(pid)
            pack.append({
                "id": pid,
                "title": paper.title,
                "doi": paper.doi,
                "published_at": self._serialize_date(paper.published_at),
                "citation_count": paper.citation_count or 0,
                "source": "reference",
            })

        if len(pack) < max_papers:
            similar = await self._find_keyword_similar_papers(
                root_paper,
                top_k=max_papers,
                exclude_ids=seen_ids,
            )
            for item in similar:
                if len(pack) >= max_papers:
                    break
                pack.append({
                    "id": item["id"],
                    "title": item["title"],
                    "doi": item["doi"],
                    "published_at": item["published_at"],
                    "citation_count": item["citation_count"],
                    "source": "similar",
                })

        return {
            "root_paper": {"id": str(root_paper.id), "title": root_paper.title},
            "pack": pack,
            "total": len(pack),
        }

    async def get_citation_timeline(self, paper_id: str) -> dict:
        """Count citing papers by year for the given root paper."""
        paper = await self._get_paper(paper_id)
        if not paper:
            logger.debug("citation_timeline_root_missing", paper_id=paper_id)
            return {
                "paper_id": paper_id,
                "title": None,
                "publication_year": None,
                "cited_by_year": [],
            }

        result = await self.db.execute(
            select(Paper.published_at)
            .join(PaperReference, Paper.id == PaperReference.citing_paper_id)
            .where(
                PaperReference.cited_paper_id == paper_id,
                Paper.deleted_at.is_(None),
            )
        )

        year_counts: dict[int, int] = defaultdict(int)
        for row in result.all():
            if row.published_at:
                year_counts[row.published_at.year] += 1

        return {
            "paper_id": str(paper.id),
            "title": paper.title,
            "publication_year": paper.published_at.year if paper.published_at else None,
            "cited_by_year": [
                {"year": year, "count": count}
                for year, count in sorted(year_counts.items())
            ],
        }

    async def get_reading_path(
        self, from_id: str, to_id: str, max_hops: int = 5
    ) -> list[dict]:
        """Find the shortest citation path from one paper to another."""
        if max_hops < 0:
            return []

        if from_id == to_id:
            paper = await self._get_paper(from_id)
            if not paper:
                return []
            return [{
                "id": str(paper.id),
                "title": paper.title,
                "doi": paper.doi,
                "hop": 0,
            }]

        from_paper = await self._get_paper(from_id)
        to_paper = await self._get_paper(to_id)
        if not from_paper or not to_paper:
            logger.debug(
                "reading_path_endpoint_missing",
                from_id=from_id,
                to_id=to_id,
                from_exists=bool(from_paper),
                to_exists=bool(to_paper),
            )
            return []

        _depths, parents = await self._bfs_citation_tree(from_id, max_depth=max_hops)
        if to_id not in parents:
            return []

        path_ids: list[str] = []
        current_id: str | None = to_id
        while current_id is not None:
            path_ids.append(current_id)
            current_id = parents[current_id]
        path_ids.reverse()

        papers = await self._load_papers(path_ids)
        if any(pid not in papers for pid in path_ids):
            return []

        return [
            {
                "id": pid,
                "title": papers[pid].title,
                "doi": papers[pid].doi,
                "hop": hop,
            }
            for hop, pid in enumerate(path_ids)
        ]

    async def get_bridge_papers(
        self, keyword_a: str, keyword_b: str, top_k: int = 10
    ) -> list[dict]:
        """Find papers that explicitly bridge two keywords."""
        if top_k <= 0:
            return []

        left = keyword_a.strip().casefold()
        right = keyword_b.strip().casefold()
        if not left or not right:
            return []

        result = await self.db.execute(
            select(Paper)
            .where(
                Paper.deleted_at.is_(None),
                Paper.keywords.is_not(None),
            )
            .order_by(
                Paper.citation_count.desc().nullslast(),
                Paper.published_at.desc().nullslast(),
            )
        )

        matches = []
        for paper in result.scalars().all():
            keywords = self._keyword_list(paper.keywords)
            keyword_set = {kw.casefold() for kw in keywords}
            if left not in keyword_set or right not in keyword_set:
                continue
            matches.append({
                "id": str(paper.id),
                "title": paper.title,
                "doi": paper.doi,
                "published_at": self._serialize_date(paper.published_at),
                "citation_count": paper.citation_count or 0,
                "keywords": keywords,
            })
            if len(matches) >= top_k:
                break

        return matches

    async def compare_papers(self, paper_ids: list[str]) -> dict:
        """Return a compact comparison view for up to five papers."""
        unique_ids: list[str] = []
        seen_ids: set[str] = set()
        for paper_id in paper_ids:
            if paper_id in seen_ids:
                continue
            unique_ids.append(paper_id)
            seen_ids.add(paper_id)
            if len(unique_ids) >= 5:
                break

        papers = await self._load_papers(unique_ids)
        ordered_papers = [papers[pid] for pid in unique_ids if pid in papers]

        serialized: list[dict] = []
        keyword_sets: list[set[str]] = []
        publication_years: set[int] = set()
        citation_values: list[int] = []

        for paper in ordered_papers:
            keywords = self._keyword_list(paper.keywords)
            keyword_sets.append({kw.casefold() for kw in keywords})
            if paper.published_at:
                publication_years.add(paper.published_at.year)

            citations = paper.citation_count or 0
            citation_values.append(citations)
            serialized.append({
                "id": str(paper.id),
                "title": paper.title,
                "doi": paper.doi,
                "published_at": self._serialize_date(paper.published_at),
                "citation_count": citations,
                "keywords": keywords,
                "abstract_preview": self._preview_text(paper.abstract),
                "venue_id": str(paper.venue_id) if paper.venue_id else None,
                "has_full_text": paper.has_full_text,
                "summary": paper.summary,
                "contributions": paper.contributions or [],
            })

        common_keywords = sorted(set.intersection(*keyword_sets)) if keyword_sets else []

        return {
            "papers": serialized,
            "comparison": {
                "common_keywords": common_keywords,
                "publication_years": sorted(publication_years),
                "citation_range": {
                    "min": min(citation_values) if citation_values else None,
                    "max": max(citation_values) if citation_values else None,
                },
            },
        }

    async def _get_paper(self, paper_id: str) -> Paper | None:
        result = await self.db.execute(
            select(Paper).where(
                Paper.id == paper_id,
                Paper.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def _load_papers(self, paper_ids) -> dict[str, Paper]:
        ids = list(dict.fromkeys(str(paper_id) for paper_id in paper_ids))
        if not ids:
            return {}

        result = await self.db.execute(
            select(Paper).where(
                Paper.id.in_(ids),
                Paper.deleted_at.is_(None),
            )
        )
        return {str(paper.id): paper for paper in result.scalars().all()}

    async def _find_keyword_similar_papers(
        self,
        paper: Paper,
        top_k: int = 10,
        exclude_ids: set[str] | None = None,
    ) -> list[dict]:
        raw_keywords = self._keyword_list(paper.keywords)
        root_keywords = {kw.casefold() for kw in raw_keywords}
        if top_k <= 0 or not raw_keywords:
            return []

        query = select(Paper).where(
            Paper.id != paper.id,
            Paper.deleted_at.is_(None),
            Paper.keywords.is_not(None),
            or_(*[Paper.keywords.contains([kw]) for kw in raw_keywords]),
        )
        if exclude_ids:
            query = query.where(~Paper.id.in_(list(exclude_ids)))

        result = await self.db.execute(query)
        candidates = list(result.scalars().all())

        if not candidates:
            fallback_query = select(Paper).where(
                Paper.id != paper.id,
                Paper.deleted_at.is_(None),
                Paper.keywords.is_not(None),
            )
            if exclude_ids:
                fallback_query = fallback_query.where(~Paper.id.in_(list(exclude_ids)))
            fallback_result = await self.db.execute(fallback_query)
            candidates = list(fallback_result.scalars().all())

        scored = []
        for candidate in candidates:
            candidate_keywords = self._keyword_list(candidate.keywords)
            shared_keywords = sorted(
                root_keywords.intersection({kw.casefold() for kw in candidate_keywords})
            )
            if not shared_keywords:
                continue

            scored.append({
                "id": str(candidate.id),
                "title": candidate.title,
                "doi": candidate.doi,
                "published_at": self._serialize_date(candidate.published_at),
                "citation_count": candidate.citation_count or 0,
                "similarity_score": len(shared_keywords),
                "reason": (
                    f"shared keywords: {', '.join(shared_keywords[:3])}"
                    if shared_keywords
                    else "keyword overlap"
                ),
            })

        scored.sort(
            key=lambda item: (
                item["similarity_score"],
                item["citation_count"],
                item["published_at"] or "",
                item["title"].lower(),
            ),
            reverse=True,
        )
        return scored[:top_k]

    async def _find_author_overlap_papers(
        self,
        paper_id: str,
        top_k: int = 10,
        exclude_ids: set[str] | None = None,
    ) -> list[dict]:
        if top_k <= 0:
            return []

        author_result = await self.db.execute(
            select(PaperAuthor.author_id).where(PaperAuthor.paper_id == paper_id)
        )
        author_ids = [row.author_id for row in author_result.all()]
        if not author_ids:
            return []

        query = (
            select(Paper, PaperAuthor.author_id)
            .join(PaperAuthor, PaperAuthor.paper_id == Paper.id)
            .where(
                Paper.deleted_at.is_(None),
                Paper.id != paper_id,
                PaperAuthor.author_id.in_(author_ids),
            )
        )
        if exclude_ids:
            query = query.where(~Paper.id.in_(list(exclude_ids)))

        result = await self.db.execute(query)

        shared_authors: dict[str, set[str]] = defaultdict(set)
        paper_map: dict[str, Paper] = {}
        for candidate, author_id in result.all():
            pid = str(candidate.id)
            paper_map[pid] = candidate
            shared_authors[pid].add(str(author_id))

        ranked_ids = sorted(
            paper_map.keys(),
            key=lambda pid: (
                len(shared_authors[pid]),
                paper_map[pid].citation_count or 0,
                self._sortable_date(paper_map[pid].published_at),
                paper_map[pid].title.lower(),
            ),
            reverse=True,
        )

        return [
            {
                "id": pid,
                "title": paper_map[pid].title,
                "doi": paper_map[pid].doi,
                "published_at": self._serialize_date(paper_map[pid].published_at),
                "citation_count": paper_map[pid].citation_count or 0,
                "similarity_score": len(shared_authors[pid]),
                "reason": "shared authors",
            }
            for pid in ranked_ids[:top_k]
        ]

    async def _bfs_citation_tree(
        self, start_id: str, max_depth: int
    ) -> tuple[dict[str, int], dict[str, str | None]]:
        depths: dict[str, int] = {start_id: 0}
        parents: dict[str, str | None] = {start_id: None}
        queue = deque([(start_id, 0)])

        while queue:
            current_id, depth = queue.popleft()
            if depth >= max_depth:
                continue

            ref_result = await self.db.execute(
                select(PaperReference.cited_paper_id)
                .join(Paper, Paper.id == PaperReference.cited_paper_id)
                .where(
                    PaperReference.citing_paper_id == current_id,
                    PaperReference.cited_paper_id.is_not(None),
                    Paper.deleted_at.is_(None),
                )
            )

            for row in ref_result.all():
                cited_id = str(row.cited_paper_id)
                if cited_id in depths:
                    continue
                depths[cited_id] = depth + 1
                parents[cited_id] = current_id
                queue.append((cited_id, depth + 1))

        return depths, parents

    @staticmethod
    def _keyword_list(raw_keywords) -> list[str]:
        if raw_keywords is None:
            return []

        if isinstance(raw_keywords, dict):
            if isinstance(raw_keywords.get("keywords"), list):
                items = raw_keywords["keywords"]
            else:
                items = list(raw_keywords.values())
        elif isinstance(raw_keywords, list | tuple | set):
            items = list(raw_keywords)
        else:
            return []

        keywords: list[str] = []
        seen: set[str] = set()
        for item in items:
            if isinstance(item, dict):
                value = item.get("keyword") or item.get("name") or item.get("display_name")
            else:
                value = item
            if not isinstance(value, str):
                continue
            cleaned = value.strip()
            normalized = cleaned.casefold()
            if not cleaned or normalized in seen:
                continue
            seen.add(normalized)
            keywords.append(cleaned)
        return keywords

    @staticmethod
    def _preview_text(text: str | None, limit: int = 280) -> str | None:
        if not text:
            return None
        compact = " ".join(text.split())
        if len(compact) <= limit:
            return compact
        return f"{compact[:limit].rstrip()}..."

    @staticmethod
    def _serialize_date(value) -> str | None:
        return str(value) if value else None

    @staticmethod
    def _sortable_date(value) -> str:
        return str(value) if value else "9999-12-31"