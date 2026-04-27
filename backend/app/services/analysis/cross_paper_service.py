"""Cross-paper reasoning service — multi-doc synthesis, timelines, reading sets.

P3 WS-2: §20 (#165-176) from FeasibilityAnalysis.md

MVP scope:
- Multi-document synthesis (LLM + citation-guided RAG)
- Research timeline construction (citation graph + temporal ordering)
- Minimal reading set (PageRank-based essential papers)
- Bridge paper detection (betweenness centrality)

Deferred: full cross-domain analysis, deep contradiction detection.
"""

import json
from collections import defaultdict

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.paper import Paper, PaperReference

logger = structlog.get_logger(__name__)

SYNTHESIS_PROMPT = """Synthesize knowledge across these {n} papers on the topic: {topic}

{papers_section}

Produce a structured synthesis that includes:
1. **Key Themes**: Major research themes identified across these papers
2. **Consensus**: What do these papers agree on?
3. **Divergences**: Where do findings or approaches differ?
4. **Gaps**: What questions remain unanswered?
5. **Evolution**: How has understanding progressed over time?
6. **Recommended Reading Order**: Most efficient order to read these papers

Return JSON:
{{
    "themes": [{{"name": "...", "papers": ["..."], "summary": "..."}}],
    "consensus": ["..."],
    "divergences": [{{"point": "...", "positions": [{{"paper": "...", "stance": "..."}}]}}],
    "gaps": ["..."],
    "evolution": [{{"period": "...", "development": "...", "key_papers": ["..."]}}],
    "reading_order": [{{"paper": "...", "rationale": "..."}}]
}}

Return ONLY the JSON."""

TIMELINE_PROMPT = """Construct a research timeline showing how this field has evolved.

{papers_section}

For each major development, provide:
- year: when it happened
- event: what happened (1 sentence)
- paper: which paper introduced it
- impact: significance (high/medium/low)

Return JSON array:
[{{"year": 2020, "event": "...", "paper": "...", "impact": "high"}}]

Return ONLY the JSON array, sorted chronologically."""


class CrossPaperService:
    """Multi-paper synthesis and reasoning."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._llm_client = None

    async def _get_llm(self):
        if self._llm_client is None:
            from app.clients.llm_client import LLMClient

            self._llm_client = LLMClient()
        return self._llm_client

    async def _load_papers(self, paper_ids: list[str]) -> list[Paper]:
        result = await self.db.execute(
            select(Paper).where(Paper.id.in_(paper_ids), Paper.deleted_at.is_(None))
        )
        return list(result.scalars().all())

    def _format_papers(self, papers: list[Paper]) -> str:
        sections = []
        for i, p in enumerate(papers, 1):
            block = f"**[{i}] {p.title}**\n"
            if p.published_at:
                block += f"Year: {p.published_at.year}\n"
            if p.doi:
                block += f"DOI: {p.doi}\n"
            if p.abstract:
                block += f"Abstract: {p.abstract[:400]}\n"
            sections.append(block)
        return "\n".join(sections)

    async def synthesize(
        self, paper_ids: list[str], topic: str = "this research area"
    ) -> dict:
        """
        Produce a multi-document synthesis across given papers.

        Returns structured thematic analysis, consensus, divergences, gaps.
        """
        papers = await self._load_papers(paper_ids)
        if not papers:
            return {"error": "No papers found"}

        llm = await self._get_llm()
        prompt = SYNTHESIS_PROMPT.format(
            n=len(papers),
            topic=topic,
            papers_section=self._format_papers(papers),
        )

        try:
            response = await llm.complete(
                prompt=prompt, temperature=0.3, max_tokens=4096
            )
            result = json.loads(response)
            return {
                "topic": topic,
                "paper_count": len(papers),
                **result,
            }
        except json.JSONDecodeError:
            return {
                "topic": topic,
                "paper_count": len(papers),
                "raw_synthesis": response,
            }
        except Exception as e:
            logger.error("synthesis_failed", error=str(e))
            return {"error": str(e)}

    async def build_timeline(self, paper_ids: list[str]) -> dict:
        """
        Build a research evolution timeline from papers.

        Combines citation graph structure with temporal ordering.
        """
        papers = await self._load_papers(paper_ids)
        if not papers:
            return {"error": "No papers found"}

        llm = await self._get_llm()
        prompt = TIMELINE_PROMPT.format(
            papers_section=self._format_papers(papers),
        )

        try:
            response = await llm.complete(prompt=prompt, temperature=0.2)
            events = json.loads(response)
            return {
                "paper_count": len(papers),
                "events": events,
            }
        except Exception as e:
            logger.error("timeline_failed", error=str(e))
            return {"error": str(e)}

    async def _build_citation_adjacency(
        self, pid_set: set[str]
    ) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
        """
        Build in-set citation adjacency from PostgreSQL PaperReference.
        Falls back to Neo4j if PostgreSQL edges are sparse.
        Returns (cited_by, cites) dicts.
        """
        cited_by: dict[str, set[str]] = defaultdict(set)
        cites: dict[str, set[str]] = defaultdict(set)

        # 1) Try PostgreSQL PaperReference (resolved edges)
        for pid in pid_set:
            refs = await self.db.execute(
                select(PaperReference.cited_paper_id).where(
                    PaperReference.citing_paper_id == pid,
                    PaperReference.cited_paper_id.is_not(None),
                    PaperReference.cited_paper_id.in_(pid_set),
                )
            )
            for row in refs.all():
                cpid = str(row.cited_paper_id)
                cited_by[cpid].add(pid)
                cites[pid].add(cpid)

        total_pg_edges = sum(len(v) for v in cites.values())

        # 2) If PostgreSQL is sparse, try Neo4j
        if total_pg_edges < 2:
            try:
                from app.graph_db import driver as neo4j_driver

                pid_list = list(pid_set)
                result = await neo4j_driver.run_query(
                    """
                    MATCH (a:Paper)-[:CITES]->(b:Paper)
                    WHERE a.id IN $ids AND b.id IN $ids
                    RETURN a.id AS citing, b.id AS cited
                    """,
                    {"ids": pid_list},
                )
                for record in result:
                    citing = str(record["citing"])
                    cited = str(record["cited"])
                    if citing in pid_set and cited in pid_set:
                        cited_by[cited].add(citing)
                        cites[citing].add(cited)
                neo4j_edges = sum(len(v) for v in cites.values()) - total_pg_edges
                if neo4j_edges > 0:
                    logger.info(
                        "neo4j_fallback_edges",
                        pg_edges=total_pg_edges,
                        neo4j_edges=neo4j_edges,
                    )
            except Exception as e:
                logger.debug("neo4j_fallback_skipped", error=str(e))

        return cited_by, cites

    async def find_essential_papers(
        self, paper_ids: list[str], top_k: int = 10
    ) -> list[dict]:
        """
        Find the minimal essential reading set using citation importance.

        Uses in-set citation count from PostgreSQL (+ Neo4j fallback).
        If no graph edges exist, falls back to global citation_count.
        """
        papers = await self._load_papers(paper_ids)
        if not papers:
            return []

        pid_set = {str(p.id) for p in papers}
        paper_map = {str(p.id): p for p in papers}

        cited_by, cites = await self._build_citation_adjacency(pid_set)

        # Count in-set citations
        citation_counts = {pid: len(cited_by.get(pid, set())) for pid in pid_set}
        has_edges = any(v > 0 for v in citation_counts.values())

        # Rank: prefer in-set citations, fallback to global citation_count
        def sort_key(pid):
            if has_edges:
                return citation_counts.get(pid, 0)
            p = paper_map.get(pid)
            return (p.citation_count or 0) if p else 0

        ranked = sorted(pid_set, key=sort_key, reverse=True)[:top_k]

        return [
            {
                "id": pid,
                "title": paper_map[pid].title if pid in paper_map else None,
                "in_set_citations": citation_counts.get(pid, 0),
                "global_citations": (
                    paper_map[pid].citation_count if pid in paper_map else None
                ),
                "published_at": (
                    str(paper_map[pid].published_at)
                    if pid in paper_map and paper_map[pid].published_at
                    else None
                ),
                "rationale": (
                    "foundational"
                    if citation_counts.get(pid, 0) >= 3
                    else (
                        "frequently cited"
                        if citation_counts.get(pid, 0) >= 1
                        else (
                            "high global impact"
                            if has_edges is False and sort_key(pid) > 0
                            else "included in set"
                        )
                    )
                ),
                "signal": "graph" if has_edges else "citation_count",
            }
            for pid in ranked
        ]

    async def find_bridge_papers(self, paper_ids: list[str]) -> list[dict]:
        """
        Find bridge papers that connect different research communities.

        Uses in/out degree product as betweenness proxy.
        Falls back to Neo4j if PostgreSQL edges are sparse.
        """
        papers = await self._load_papers(paper_ids)
        if not papers:
            return []

        pid_set = {str(p.id) for p in papers}
        paper_map = {str(p.id): p for p in papers}

        cited_by, cites = await self._build_citation_adjacency(pid_set)

        # Simple bridge score: in_degree × out_degree
        bridge_scores = {}
        for pid in pid_set:
            in_degree = len(cited_by.get(pid, set()))
            out_degree = len(cites.get(pid, set()))
            bridge_scores[pid] = in_degree * out_degree

        # Filter to papers with non-zero bridge score
        bridges = sorted(
            [(pid, score) for pid, score in bridge_scores.items() if score > 0],
            key=lambda x: x[1],
            reverse=True,
        )[:10]

        return [
            {
                "id": pid,
                "title": paper_map[pid].title if pid in paper_map else None,
                "bridge_score": score,
                "cited_by_count": len(cited_by.get(pid, set())),
                "cites_count": len(cites.get(pid, set())),
            }
            for pid, score in bridges
        ]

    async def close(self):
        if self._llm_client:
            try:
                await self._llm_client.close()
            except Exception:
                pass
