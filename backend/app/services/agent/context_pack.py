"""Deterministic context-pack builder for downstream agents."""

from __future__ import annotations

import math
import re
from typing import Any

import structlog
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.collection import DEFAULT_USER_ID
from app.models.paper import Paper
from app.models.paper_qa import PaperChunk
from app.services.collection_service import CollectionService

logger = structlog.get_logger(__name__)

_MIN_PAPER_BUDGET = 160
_MAX_PAPER_BUDGET = 900
_MAX_EVIDENCE_BUDGET = 280


class AgentContextPackService:
    """Build compact cited JSON context without adding an LLM dependency."""

    def __init__(self, db: AsyncSession, user_id: str = DEFAULT_USER_ID):
        self.db = db
        self.user_id = user_id
        self.collection_service = CollectionService(db, user_id=user_id)

    async def build_context_pack(
        self,
        paper_ids: list[str] | None = None,
        collection_id: str | None = None,
        question: str | None = None,
        token_budget: int = 4000,
        include_evidence: bool = True,
        evidence_top_k: int = 8,
    ) -> dict[str, Any]:
        """Return compressed paper metadata and evidence for an agent token budget."""
        resolved_ids, warnings = await self._resolve_paper_ids(
            paper_ids or [],
            collection_id,
        )
        if not resolved_ids:
            return self._empty_pack(
                paper_ids=paper_ids or [],
                collection_id=collection_id,
                question=question,
                token_budget=token_budget,
                warnings=warnings or ["No papers resolved for context pack."],
            )

        papers = await self._load_papers(resolved_ids)
        if not papers:
            return self._empty_pack(
                paper_ids=resolved_ids,
                collection_id=collection_id,
                question=question,
                token_budget=token_budget,
                warnings=warnings or ["No matching local papers found."],
            )

        ordered_papers = self._order_papers(papers, resolved_ids)
        citations = self._build_citations(ordered_papers)
        paper_budget = self._paper_budget(token_budget, len(ordered_papers))
        paper_items = [
            self._format_paper(paper, citations[str(paper.id)], paper_budget)
            for paper in ordered_papers
        ]
        evidence_items = []
        if include_evidence:
            evidence_items = await self._build_evidence(
                [str(paper.id) for paper in ordered_papers],
                question,
                evidence_top_k,
            )

        estimated_tokens = self._estimate_tokens(
            {"papers": paper_items, "evidence": evidence_items}
        )
        truncated = estimated_tokens > token_budget
        if truncated:
            evidence_items = self._fit_evidence_to_budget(
                evidence_items,
                max(token_budget - self._estimate_tokens({"papers": paper_items}), 0),
            )
            estimated_tokens = self._estimate_tokens(
                {"papers": paper_items, "evidence": evidence_items}
            )

        return {
            "scope": {
                "paper_ids": [str(paper.id) for paper in ordered_papers],
                "collection_id": collection_id,
                "question": question,
            },
            "budget": {
                "requested_tokens": token_budget,
                "estimated_tokens": estimated_tokens,
                "truncated": truncated,
            },
            "citations": [
                {"key": key, "paper_id": paper_id}
                for paper_id, key in citations.items()
            ],
            "papers": paper_items,
            "evidence": evidence_items,
            "warnings": warnings,
        }

    async def _resolve_paper_ids(
        self,
        paper_ids: list[str],
        collection_id: str | None,
    ) -> tuple[list[str], list[str]]:
        warnings: list[str] = []
        resolved = list(dict.fromkeys(pid.strip() for pid in paper_ids if pid.strip()))
        if collection_id:
            try:
                collection_papers = await self.collection_service.get_collection_papers(
                    collection_id,
                    limit=100,
                )
                collection_ids = [str(item["paper_id"]) for item in collection_papers]
                resolved.extend(pid for pid in collection_ids if pid not in resolved)
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "context_pack_collection_lookup_failed",
                    collection_id=collection_id,
                    error=str(exc),
                )
                warnings.append(f"Collection lookup failed: {type(exc).__name__}")
        return resolved[:100], warnings

    async def _load_papers(self, paper_ids: list[str]) -> list[Any]:
        result = await self.db.execute(
            select(Paper).where(
                Paper.deleted_at.is_(None),
                Paper.id.in_(paper_ids),
            )
        )
        return list(result.scalars().all())

    @staticmethod
    def _order_papers(papers: list[Any], paper_ids: list[str]) -> list[Any]:
        order = {paper_id: index for index, paper_id in enumerate(paper_ids)}
        return sorted(papers, key=lambda paper: order.get(str(paper.id), len(order)))

    @staticmethod
    def _build_citations(papers: list[Any]) -> dict[str, str]:
        return {str(paper.id): f"P{index}" for index, paper in enumerate(papers, 1)}

    @staticmethod
    def _paper_budget(token_budget: int, paper_count: int) -> int:
        if paper_count <= 0:
            return _MIN_PAPER_BUDGET
        return min(
            _MAX_PAPER_BUDGET,
            max(_MIN_PAPER_BUDGET, token_budget // max(paper_count * 2, 1)),
        )

    def _format_paper(self, paper: Any, citation_key: str, token_budget: int) -> dict[str, Any]:
        raw = getattr(paper, "raw_metadata", None) or {}
        abstract = getattr(paper, "abstract", None) or ""
        summary = getattr(paper, "summary", None) or ""
        deep_analysis = (getattr(paper, "deep_analysis", None) or {}).get("analysis", "")
        text_budget = max(token_budget - 120, 80)
        return {
            "citation_key": citation_key,
            "paper_id": str(paper.id),
            "title": getattr(paper, "title", None),
            "identifiers": {
                "doi": getattr(paper, "doi", None),
                "arxiv_id": getattr(paper, "arxiv_id", None),
                "pmid": getattr(paper, "pmid", None),
                "openalex_id": getattr(paper, "openalex_id", None),
                "semantic_scholar_id": getattr(paper, "semantic_scholar_id", None),
            },
            "year": paper.published_at.year if getattr(paper, "published_at", None) else None,
            "venue": raw.get("venue") or raw.get("container-title"),
            "keywords": getattr(paper, "keywords", None) or [],
            "status": {
                "ingestion_status": getattr(paper, "ingestion_status", None),
                "has_full_text": getattr(paper, "has_full_text", None),
            },
            "abstract": self._truncate(abstract, text_budget),
            "summary": self._truncate(summary, text_budget),
            "contributions": self._truncate_list(getattr(paper, "contributions", None) or [], 5),
            "limitations": self._truncate_list(getattr(paper, "limitations", None) or [], 5),
            "analysis_snippet": self._truncate(deep_analysis, text_budget),
            "links": {
                "doi": f"https://doi.org/{paper.doi}" if getattr(paper, "doi", None) else None,
                "arxiv": f"https://arxiv.org/abs/{paper.arxiv_id}"
                if getattr(paper, "arxiv_id", None)
                else None,
                "pdf": raw.get("pdf_url") or raw.get("best_oa_url"),
            },
        }

    async def _build_evidence(
        self,
        paper_ids: list[str],
        question: str | None,
        top_k: int,
    ) -> list[dict[str, Any]]:
        query = (
            select(
                PaperChunk.id.label("chunk_id"),
                PaperChunk.paper_id,
                PaperChunk.section_title,
                PaperChunk.content,
                Paper.title.label("paper_title"),
            )
            .join(Paper, Paper.id == PaperChunk.paper_id)
            .where(
                PaperChunk.paper_id.in_(paper_ids),
                PaperChunk.is_references.is_(False),
                PaperChunk.is_appendix.is_(False),
            )
            .order_by(PaperChunk.order_index)
            .limit(top_k)
        )
        terms = self._query_terms(question or "")
        if terms:
            query = query.where(
                or_(
                    *[
                        PaperChunk.content.ilike(f"%{term}%")
                        for term in terms[:6]
                    ],
                    *[
                        PaperChunk.section_title.ilike(f"%{term}%")
                        for term in terms[:6]
                    ],
                )
            )

        try:
            result = await self.db.execute(query)
            rows = result.fetchall()
        except Exception as exc:  # noqa: BLE001
            logger.warning("context_pack_evidence_lookup_failed", error=str(exc))
            return []

        return [self._format_evidence_row(row, index) for index, row in enumerate(rows, 1)]

    def _format_evidence_row(self, row: Any, index: int) -> dict[str, Any]:
        return {
            "id": str(row.chunk_id),
            "citation_key": f"E{index}",
            "paper_id": str(row.paper_id),
            "paper_title": row.paper_title,
            "section_title": row.section_title,
            "content": self._truncate(row.content or "", _MAX_EVIDENCE_BUDGET),
            "source": "local_chunk",
        }

    @staticmethod
    def _query_terms(question: str) -> list[str]:
        terms = re.findall(r"[A-Za-z][A-Za-z0-9_-]{3,}", question.lower())
        return list(dict.fromkeys(terms))

    def _fit_evidence_to_budget(
        self,
        evidence_items: list[dict[str, Any]],
        token_budget: int,
    ) -> list[dict[str, Any]]:
        kept: list[dict[str, Any]] = []
        used = 0
        for item in evidence_items:
            item_tokens = self._estimate_tokens(item)
            if used + item_tokens > token_budget:
                break
            kept.append(item)
            used += item_tokens
        return kept

    @staticmethod
    def _empty_pack(
        paper_ids: list[str],
        collection_id: str | None,
        question: str | None,
        token_budget: int,
        warnings: list[str],
    ) -> dict[str, Any]:
        return {
            "scope": {
                "paper_ids": paper_ids,
                "collection_id": collection_id,
                "question": question,
            },
            "budget": {
                "requested_tokens": token_budget,
                "estimated_tokens": 0,
                "truncated": False,
            },
            "citations": [],
            "papers": [],
            "evidence": [],
            "warnings": warnings,
        }

    @staticmethod
    def _truncate(text: str, token_budget: int) -> str:
        if not text:
            return ""
        char_budget = max(token_budget * 4, 0)
        if len(text) <= char_budget:
            return text
        return text[: max(char_budget - 1, 0)].rstrip() + "…"

    def _truncate_list(self, values: list[Any], limit: int) -> list[str]:
        return [self._truncate(str(value), 80) for value in values[:limit]]

    def _estimate_tokens(self, value: Any) -> int:
        if value is None:
            return 0
        if isinstance(value, str):
            return math.ceil(len(value) / 4)
        if isinstance(value, bool | int | float):
            return 1
        if isinstance(value, list | tuple):
            return sum(self._estimate_tokens(item) for item in value)
        if isinstance(value, dict):
            return sum(
                self._estimate_tokens(str(key)) + self._estimate_tokens(item)
                for key, item in value.items()
            )
        return self._estimate_tokens(str(value))
