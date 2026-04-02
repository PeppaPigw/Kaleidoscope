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
        result = await self.db.execute(select(Author).where(Author.id == author_id))
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

        # Build full paper list + timeline + keyword aggregation
        from collections import Counter

        year_counts: dict[int, int] = defaultdict(int)
        all_papers = []
        total_citations = 0
        keyword_years: dict[str, list[int]] = defaultdict(list)

        for paper, position, is_corr in rows:
            yr = paper.published_at.year if paper.published_at else None
            if yr:
                year_counts[yr] += 1
            total_citations += paper.citation_count or 0

            # Aggregate keywords
            for kw in paper.keywords or []:
                if yr:
                    keyword_years[str(kw)].append(yr)

            all_papers.append(
                {
                    "id": str(paper.id),
                    "title": paper.title,
                    "doi": paper.doi,
                    "arxiv_id": paper.arxiv_id,
                    "abstract": paper.abstract,
                    "keywords": paper.keywords or [],
                    "published_at": (
                        str(paper.published_at) if paper.published_at else None
                    ),
                    "year": yr,
                    "citation_count": paper.citation_count or 0,
                    "author_position": position,
                    "is_corresponding": is_corr,
                }
            )

        # Build lookup maps for cross-referencing with S2
        # key: normalised arxiv_id or "doi:XXX" → library paper dict
        library_lookup: dict[str, dict] = {}
        for lp in all_papers:
            if lp["arxiv_id"]:
                # normalise: strip version suffix (e.g. "2501.00001v2" → "2501.00001")
                arxiv_clean = lp["arxiv_id"].split("v")[0].lower()
                library_lookup[f"arxiv:{arxiv_clean}"] = lp
            if lp["doi"]:
                library_lookup[f"doi:{lp['doi'].lower()}"] = lp

        # ── Fetch full paper list from Semantic Scholar (if enriched) ──────
        s2_id = author.semantic_scholar_id
        if s2_id:
            from app.clients.semantic_scholar import SemanticScholarClient

            s2_client = SemanticScholarClient()
            try:
                s2_papers_raw = await s2_client.get_author_papers(s2_id, limit=500)
            except Exception as exc:
                logger.warning(
                    "s2_author_papers_failed", s2_id=s2_id, error=str(exc)[:120]
                )
                s2_papers_raw = []
            finally:
                await s2_client.close()

            # Track which library papers were matched to S2 entries
            matched_library_ids: set[str] = set()

            # Merge S2 papers with library lookup
            merged: list[dict] = []
            for sp in s2_papers_raw:
                ext = sp.get("externalIds") or {}
                arxiv_raw = ext.get("ArXiv") or ext.get("arxiv") or ""
                doi_raw = ext.get("DOI") or ""
                arxiv_key = (
                    f"arxiv:{arxiv_raw.split('v')[0].lower()}" if arxiv_raw else None
                )
                doi_key = f"doi:{doi_raw.lower()}" if doi_raw else None

                lib = (arxiv_key and library_lookup.get(arxiv_key)) or (
                    doi_key and library_lookup.get(doi_key)
                )

                # Derive keywords from fieldsOfStudy (can be strings or dicts)
                raw_fields = sp.get("fieldsOfStudy") or []
                fields = [
                    f if isinstance(f, str) else f.get("category", "")
                    for f in raw_fields
                    if f
                ]

                if lib:
                    matched_library_ids.add(lib["id"])

                merged.append(
                    {
                        # identity
                        "id": lib["id"] if lib else sp.get("paperId", ""),
                        "s2_paper_id": sp.get("paperId"),
                        # core metadata
                        "title": sp.get("title") or (lib["title"] if lib else ""),
                        "doi": doi_raw or (lib["doi"] if lib else None),
                        "arxiv_id": arxiv_raw or (lib["arxiv_id"] if lib else None),
                        "abstract": sp.get("abstract")
                        or (lib["abstract"] if lib else None),
                        "keywords": fields or (lib["keywords"] if lib else []),
                        "year": sp.get("year"),
                        "published_at": lib["published_at"] if lib else None,
                        "citation_count": sp.get("citationCount")
                        or (lib["citation_count"] if lib else 0),
                        "venue": (sp.get("publicationVenue") or {}).get("name")
                        or sp.get("venue")
                        or "",
                        # library flags
                        "in_library": bool(lib),
                        "library_paper_id": lib["id"] if lib else None,
                        "has_full_text": lib
                        is not None,  # all library papers went through MinerU
                        # author role (only known for library papers)
                        "author_position": lib["author_position"] if lib else None,
                        "is_corresponding": lib["is_corresponding"] if lib else False,
                    }
                )

            # Append library-only papers not yet indexed by S2
            for lp in all_papers:
                if lp["id"] not in matched_library_ids:
                    merged.append(
                        {
                            **lp,
                            "s2_paper_id": None,
                            "venue": "",
                            "in_library": True,
                            "library_paper_id": lp["id"],
                            "has_full_text": True,
                        }
                    )

            # Rebuild timeline and topics from merged list (S2 has richer coverage)
            year_counts_merged: dict[int, int] = defaultdict(int)
            keyword_years_merged: dict[str, list[int]] = defaultdict(list)
            for mp in merged:
                yr = mp.get("year")
                if yr:
                    year_counts_merged[yr] += 1
                    for kw in mp["keywords"] or []:
                        keyword_years_merged[str(kw)].append(yr)

            all_papers = merged
            year_counts = year_counts_merged
            keyword_years = keyword_years_merged

        # top_papers: top 10 by citation count (library papers first when tied, for navigation)
        top_papers = sorted(
            all_papers,
            key=lambda x: (x["citation_count"], x.get("in_library", False)),
            reverse=True,
        )[:10]

        timeline = [
            {"year": yr, "count": cnt} for yr, cnt in sorted(year_counts.items())
        ]

        # Derive topics from keyword frequency
        keyword_count = Counter(
            kw for kws in [p["keywords"] for p in all_papers] for kw in kws
        )
        topics = []
        for kw, count in keyword_count.most_common(10):
            yrs = sorted(keyword_years[kw])
            year_range = (
                f"{yrs[0]}–{yrs[-1]}"
                if yrs and yrs[0] != yrs[-1]
                else str(yrs[0]) if yrs else ""
            )
            topics.append(
                {
                    "id": kw,
                    "label": kw,
                    "years": year_range,
                    "paperCount": count,
                    "active": True,
                }
            )

        # Co-authors: all other authors on shared papers
        paper_ids = [str(r[0].id) for r in rows]
        co_authors: list[dict] = []
        if paper_ids:
            from uuid import UUID as UUIDType

            co_result = await self.db.execute(
                select(
                    Author.id,
                    Author.display_name,
                    PaperAuthor.paper_id,
                    Paper.published_at,
                )
                .join(PaperAuthor, Author.id == PaperAuthor.author_id)
                .join(Paper, PaperAuthor.paper_id == Paper.id)
                .where(
                    PaperAuthor.paper_id.in_([UUIDType(p) for p in paper_ids]),
                    PaperAuthor.author_id != UUIDType(author_id),
                    Paper.deleted_at.is_(None),
                )
            )
            co_rows = co_result.all()
            # Aggregate by co-author id
            co_map: dict[str, dict] = {}
            for co_id, co_name, _, pub_at in co_rows:
                key = str(co_id)
                if key not in co_map:
                    co_map[key] = {
                        "id": key,
                        "display_name": co_name,
                        "affiliation": "",
                        "paper_count": 0,
                        "last_collab_year": None,
                    }
                co_map[key]["paper_count"] += 1
                if pub_at:
                    yr = pub_at.year
                    if (
                        co_map[key]["last_collab_year"] is None
                        or yr > co_map[key]["last_collab_year"]
                    ):
                        co_map[key]["last_collab_year"] = yr
            co_authors = sorted(co_map.values(), key=lambda x: -x["paper_count"])[:20]

        s2_meta = (author.raw_metadata or {}).get("semantic_scholar", {})
        s2_id = author.semantic_scholar_id
        return {
            "id": str(author.id),
            "display_name": author.display_name,
            "openalex_id": author.openalex_id,
            "semantic_scholar_id": s2_id,
            "scholar_url": (
                f"https://www.semanticscholar.org/author/{s2_id}" if s2_id else None
            ),
            "orcid": author.orcid,
            "h_index": author.h_index,
            "citation_count": author.citation_count,
            "paper_count": author.paper_count,
            "aliases": author.aliases or [],
            "homepage": s2_meta.get("homepage"),
            "affiliations": s2_meta.get("affiliations", []),
            "enriched_at": s2_meta.get("enriched_at"),
            "paper_count_in_library": len(rows),
            "total_citations_in_library": total_citations,
            "timeline": timeline,
            "top_papers": top_papers,
            "papers": all_papers,
            "topics": topics,
            "co_authors": co_authors,
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
            (a, b, w) for (a, b), w in edge_weight.items() if w >= min_collaborations
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
                select(Author.id, Author.display_name).where(Author.id.in_(uuid_ids))
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
