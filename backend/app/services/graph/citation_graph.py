"""Citation graph service — build and query the Neo4j citation graph."""

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.graph_db import driver as neo4j_driver
from app.graph_db import queries as Q
from app.models.paper import Paper, PaperReference

logger = structlog.get_logger(__name__)


class CitationGraphService:
    """Build and query the citation graph in Neo4j."""

    def __init__(self, db: AsyncSession | None = None):
        self.db = db

    # ─── Sync operations ─────────────────────────────────────────

    async def sync_paper(self, paper: Paper) -> dict:
        """
        Sync a paper and its references to Neo4j.

        1. Upsert the paper node
        2. Upsert each reference as a CITES edge
        """
        log = logger.bind(paper_id=str(paper.id), doi=paper.doi)

        # Upsert paper node
        await neo4j_driver.run_write(
            Q.UPSERT_PAPER,
            {
                "id": str(paper.id),
                "doi": paper.doi,
                "arxiv_id": paper.arxiv_id,
                "title": paper.title,
                "year": paper.published_at.year if paper.published_at else None,
                "citation_count": paper.citation_count or 0,
                "paper_type": paper.paper_type,
            },
        )

        # Sync references from PaperReference rows
        refs_synced = 0
        if self.db:
            result = await self.db.execute(
                select(PaperReference).where(PaperReference.citing_paper_id == paper.id)
            )
            references = result.scalars().all()

            for ref in references:
                # Use the actual PaperReference field names (raw_doi, raw_title, raw_year)
                cited_id = (
                    str(ref.cited_paper_id)
                    if ref.cited_paper_id
                    else f"ext:{ref.raw_doi or ref.raw_title or f'ref_{ref.position}'}"
                )
                await neo4j_driver.run_write(
                    Q.UPSERT_CITATION,
                    {
                        "citing_id": str(paper.id),
                        "cited_id": cited_id,
                        "cited_doi": ref.raw_doi,
                        "cited_title": ref.raw_title,
                        "cited_year": ref.raw_year,
                        "context": None,
                        "position": ref.position,
                    },
                )
                refs_synced += 1

        log.info("paper_synced_to_graph", refs=refs_synced)

        # ── Reconcile stubs: merge any existing stub nodes that match ──
        stubs_reconciled = 0
        try:
            if paper.doi:
                result = await neo4j_driver.run_query(
                    Q.RECONCILE_STUBS_BY_DOI,
                    {"canonical_id": str(paper.id)},
                )
                if result:
                    stubs_reconciled += result[0].get("reconciled", 0)
            if paper.title:
                result = await neo4j_driver.run_query(
                    Q.RECONCILE_STUBS_BY_TITLE,
                    {"canonical_id": str(paper.id)},
                )
                if result:
                    stubs_reconciled += result[0].get("reconciled", 0)
            if stubs_reconciled:
                log.info("stubs_reconciled", count=stubs_reconciled)
        except Exception as e:
            log.warning("stub_reconciliation_failed", error=str(e))

        return {
            "paper_id": str(paper.id),
            "references_synced": refs_synced,
            "stubs_reconciled": stubs_reconciled,
        }

    async def sync_all_papers(self, limit: int = 1000) -> int:
        """Batch-sync papers from PostgreSQL to Neo4j."""
        if not self.db:
            raise ValueError("DB session required for batch sync")

        result = await self.db.execute(
            select(Paper).where(Paper.deleted_at.is_(None)).limit(limit)
        )
        papers = result.scalars().all()

        synced = 0
        for paper in papers:
            try:
                await self.sync_paper(paper)
                synced += 1
            except Exception as e:
                logger.warning(
                    "graph_sync_failed", paper_id=str(paper.id), error=str(e)
                )

        logger.info("batch_graph_sync_complete", synced=synced, total=len(papers))
        return synced

    # ─── Query operations ────────────────────────────────────────

    async def get_citations(
        self, paper_id: str, direction: str = "both", limit: int = 50
    ) -> dict:
        """
        Get citations for a paper.

        Args:
            direction: "forward" (papers citing this), "backward" (references), or "both"
        """
        result = {"paper_id": paper_id}
        neo4j_available = True

        if direction in ("forward", "both"):
            try:
                result["forward_citations"] = await neo4j_driver.run_query(
                    Q.GET_FORWARD_CITATIONS, {"paper_id": paper_id, "limit": limit}
                )
            except Exception as exc:
                neo4j_available = False
                logger.warning("graph_forward_citations_unavailable", error=str(exc))
                result["forward_citations"] = []

        if direction in ("backward", "both"):
            try:
                result["backward_citations"] = await neo4j_driver.run_query(
                    Q.GET_BACKWARD_CITATIONS, {"paper_id": paper_id, "limit": limit}
                )
            except Exception as exc:
                neo4j_available = False
                logger.warning("graph_backward_citations_unavailable", error=str(exc))
                result["backward_citations"] = []

        # PostgreSQL fallback when Neo4j is unavailable
        if not neo4j_available and self.db:
            from sqlalchemy import text as sa_text
            if direction in ("backward", "both"):
                rows = await self.db.execute(sa_text("""
                    SELECT pr.cited_paper_id, pr.raw_title, pr.raw_doi, pr.raw_year,
                           p.title as resolved_title, p.doi as resolved_doi,
                           LEFT(pr.raw_string, 200) as raw_string
                    FROM paper_references pr
                    LEFT JOIN papers p ON p.id = pr.cited_paper_id
                    WHERE pr.citing_paper_id = :pid
                    ORDER BY pr.position
                    LIMIT :lim
                """), {"pid": paper_id, "lim": limit})
                backward = []
                for row in rows.all():
                    title = row[4] or row[1] or (row[6][:150] if row[6] else None)
                    doi = row[5] or row[2]
                    if not title:
                        title = f"DOI: {doi}" if doi else "Unknown reference"
                    entry = {
                        "cited_paper_id": str(row[0]) if row[0] else None,
                        "title": title,
                        "doi": doi,
                        "year": row[3],
                        "resolved": row[0] is not None,
                    }
                    backward.append(entry)
                result["backward_citations"] = backward

            if direction in ("forward", "both"):
                rows = await self.db.execute(sa_text("""
                    SELECT pr.citing_paper_id, p.title, p.doi,
                           EXTRACT(YEAR FROM p.published_at)::int as year
                    FROM paper_references pr
                    JOIN papers p ON p.id = pr.citing_paper_id
                    WHERE pr.cited_paper_id = :pid
                    LIMIT :lim
                """), {"pid": paper_id, "lim": limit})
                forward = []
                for row in rows.all():
                    forward.append({
                        "citing_paper_id": str(row[0]),
                        "title": row[1],
                        "doi": row[2],
                        "year": row[3],
                        "resolved": True,
                    })
                result["forward_citations"] = forward

            result["source"] = "postgresql_fallback"

            # Add summary stats
            try:
                stats_row = await self.db.execute(sa_text("""
                    SELECT COUNT(*) as total,
                           COUNT(cited_paper_id) as resolved
                    FROM paper_references
                    WHERE citing_paper_id = :pid
                """), {"pid": paper_id})
                stats = stats_row.one()
                result["total_references"] = stats[0]
                result["resolved_references"] = stats[1]
            except Exception:
                pass

        return result

    async def co_citation_analysis(self, paper_id: str, limit: int = 20) -> list[dict]:
        """
        Find papers frequently cited alongside this one.

        Co-citation strength = number of papers that cite both.
        """
        try:
            return await neo4j_driver.run_query(
                Q.CO_CITATION_ANALYSIS, {"paper_id": paper_id, "limit": limit}
            )
        except Exception as exc:
            logger.warning("graph_co_citation_unavailable", error=str(exc))

        # PostgreSQL fallback
        if self.db:
            from sqlalchemy import text as sa_text
            try:
                rows = await self.db.execute(sa_text("""
                    SELECT pr2.cited_paper_id, p.title, COUNT(*) as co_citation_count
                    FROM paper_references pr1
                    JOIN paper_references pr2
                        ON pr1.citing_paper_id = pr2.citing_paper_id
                        AND pr2.cited_paper_id != :pid
                        AND pr2.cited_paper_id IS NOT NULL
                    JOIN papers p ON p.id = pr2.cited_paper_id
                    WHERE pr1.cited_paper_id = :pid
                    GROUP BY pr2.cited_paper_id, p.title
                    ORDER BY co_citation_count DESC
                    LIMIT :lim
                """), {"pid": paper_id, "lim": limit})
                return [
                    {"paper_id": str(row[0]), "title": row[1], "co_citation_count": row[2]}
                    for row in rows.all()
                ]
            except Exception:
                pass
        return []

    async def bibliographic_coupling(
        self, paper_id: str, limit: int = 20
    ) -> list[dict]:
        """
        Find papers that cite the same references as this one.

        Coupling strength = number of shared references.
        """
        try:
            return await neo4j_driver.run_query(
                Q.BIBLIOGRAPHIC_COUPLING, {"paper_id": paper_id, "limit": limit}
            )
        except Exception as exc:
            logger.warning("graph_bibliographic_coupling_unavailable", error=str(exc))

        # PostgreSQL fallback
        if self.db:
            from sqlalchemy import text as sa_text
            try:
                rows = await self.db.execute(sa_text("""
                    SELECT pr2.citing_paper_id, p.title, COUNT(*) as shared_refs
                    FROM paper_references pr1
                    JOIN paper_references pr2
                        ON pr1.cited_paper_id = pr2.cited_paper_id
                        AND pr2.citing_paper_id != :pid
                        AND pr1.cited_paper_id IS NOT NULL
                    JOIN papers p ON p.id = pr2.citing_paper_id
                    WHERE pr1.citing_paper_id = :pid
                    GROUP BY pr2.citing_paper_id, p.title
                    ORDER BY shared_refs DESC
                    LIMIT :lim
                """), {"pid": paper_id, "lim": limit})
                return [
                    {"paper_id": str(row[0]), "title": row[1], "shared_references": row[2]}
                    for row in rows.all()
                ]
            except Exception:
                pass
        return []

    async def get_neighborhood(
        self, paper_id: str, depth: int = 1, limit: int = 100
    ) -> dict:
        """Get graph neighborhood for visualization."""
        try:
            if depth == 1:
                results = await neo4j_driver.run_query(
                    Q.GRAPH_NEIGHBORHOOD, {"paper_id": paper_id}
                )
                return results[0] if results else {}
            nodes = await neo4j_driver.run_query(
                Q.GRAPH_NEIGHBORHOOD_2HOP, {"paper_id": paper_id, "limit": limit}
            )
            return {"center_id": paper_id, "neighbors": nodes}
        except Exception as exc:
            logger.warning("graph_neighborhood_unavailable", error=str(exc))
            return {"center_id": paper_id, "nodes": [], "edges": []}

    async def get_stats(self) -> dict:
        """Get graph statistics."""
        try:
            result = await neo4j_driver.run_query(Q.GRAPH_STATS)
        except Exception as exc:
            logger.warning("graph_stats_unavailable", error=str(exc))
            # PostgreSQL fallback
            if self.db:
                from sqlalchemy import text as sa_text
                try:
                    r = await self.db.execute(sa_text("""
                        SELECT
                            (SELECT COUNT(*) FROM papers WHERE deleted_at IS NULL) as paper_count,
                            (SELECT COUNT(*) FROM paper_references) as citation_count,
                            (SELECT COUNT(DISTINCT author_name_normalized) FROM author_papers) as author_count
                    """))
                    row = r.one()
                    return {"paper_count": row[0], "citation_count": row[1], "author_count": row[2], "source": "postgresql"}
                except Exception:
                    pass
            return {"paper_count": 0, "citation_count": 0, "author_count": 0}
        return (
            result[0]
            if result
            else {"paper_count": 0, "citation_count": 0, "author_count": 0}
        )


class RecommendationService:
    """Recommend similar papers using graph + vector signals."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.graph = CitationGraphService(db)

    async def recommend_similar(self, paper_id: str, limit: int = 10) -> list[dict]:
        """
        Recommend papers using multi-signal RRF fusion:
        1. Bibliographic coupling (shared references) — graph signal
        2. Co-citation (cited together) — graph signal
        3. SPECTER2 embedding similarity — vector signal (Qdrant)

        For papers with sparse citation graphs, signal 3 ensures
        meaningful recommendations still surface.
        """
        log = logger.bind(paper_id=paper_id)

        # Signal 1: Bibliographic coupling
        try:
            coupling = await self.graph.bibliographic_coupling(paper_id, limit=20)
        except Exception:
            coupling = []
        coupling_ranked = {
            r.get("id") or r.get("paper_id"): 1.0 / (i + 1)
            for i, r in enumerate(coupling)
            if r.get("id") or r.get("paper_id")
        }

        # Signal 2: Co-citation
        try:
            co_cite = await self.graph.co_citation_analysis(paper_id, limit=20)
        except Exception:
            co_cite = []
        co_cite_ranked = {
            r.get("id") or r.get("paper_id"): 1.0 / (i + 1)
            for i, r in enumerate(co_cite)
            if r.get("id") or r.get("paper_id")
        }

        # Signal 3: SPECTER2 vector similarity via Qdrant
        vector_ranked: dict[str, float] = {}
        vector_raw_scores: dict[str, float] = {}
        try:
            paper_result = await self.db.execute(
                select(Paper.title, Paper.abstract).where(Paper.id == paper_id)
            )
            paper_row = paper_result.one_or_none()
            if paper_row and paper_row.title:
                from app.services.search.instances import vector_service

                query_text = paper_row.title
                if paper_row.abstract:
                    query_text += " " + paper_row.abstract[:500]
                vec_results = vector_service.search(query_text, top_k=20)
                for i, hit in enumerate(vec_results):
                    pid = hit.get("paper_id", "")
                    if pid and pid != paper_id:  # Exclude self
                        vector_ranked[pid] = 1.0 / (i + 1)
                        vector_raw_scores[pid] = hit.get("score", 0.0)
        except Exception as e:
            log.debug("vector_similarity_skipped", error=str(e))

        # Merge with RRF (k=60)
        k = 60
        all_ids = (
            set(coupling_ranked.keys())
            | set(co_cite_ranked.keys())
            | set(vector_ranked.keys())
        )
        fused = []
        for pid in all_ids:
            score = 0.0
            reasons = []
            if pid in coupling_ranked:
                score += 1.0 / (k + (1.0 / coupling_ranked[pid]))
                reasons.append("shared_references")
            if pid in co_cite_ranked:
                score += 1.0 / (k + (1.0 / co_cite_ranked[pid]))
                reasons.append("co_cited")
            if pid in vector_ranked:
                score += 1.0 / (k + (1.0 / vector_ranked[pid]))
                reasons.append("embedding_similarity")
            similarity = vector_raw_scores.get(pid, 0.0)
            fused.append({"id": pid, "score": round(similarity, 4) if similarity else round(score, 6), "reasons": reasons})

        fused.sort(key=lambda x: x["score"], reverse=True)

        # Enrich with paper details from DB
        result_ids = [f["id"] for f in fused[:limit]]
        if result_ids and self.db:
            papers_result = await self.db.execute(
                select(
                    Paper.id,
                    Paper.doi,
                    Paper.title,
                    Paper.published_at,
                    Paper.citation_count,
                ).where(Paper.id.in_(result_ids))
            )
            details = {str(r.id): r for r in papers_result.all()}

            for item in fused[:limit]:
                if item["id"] in details:
                    d = details[item["id"]]
                    item["doi"] = d.doi
                    item["title"] = d.title
                    item["year"] = d.published_at.year if d.published_at else None
                    item["citation_count"] = d.citation_count

        log.info(
            "recommendation_generated",
            count=len(fused[:limit]),
            signals={
                "coupling": len(coupling_ranked),
                "co_cite": len(co_cite_ranked),
                "vector": len(vector_ranked),
            },
        )
        return fused[:limit]
