"""Admin service — reprocessing, cost metering, and digest generation."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import structlog
from sqlalchemy import func, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.paper import Paper

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# LLM cost metering — simple in-process counter written to a JSONB table row.
# Production: replace with Prometheus counter or a dedicated cost_events table.
# ---------------------------------------------------------------------------

_LLM_COST_BY_MODEL: dict[str, float] = {}   # model_name -> cumulative USD cost
_LLM_CALLS_BY_MODEL: dict[str, int] = {}    # model_name -> call count
_LLM_TOKENS_BY_MODEL: dict[str, int] = {}   # model_name -> prompt+completion tokens


def record_llm_usage(
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    cost_usd: float,
) -> None:
    """Record one LLM call. Thread-safe enough for single-process deployments."""
    _LLM_CALLS_BY_MODEL[model] = _LLM_CALLS_BY_MODEL.get(model, 0) + 1
    _LLM_TOKENS_BY_MODEL[model] = (
        _LLM_TOKENS_BY_MODEL.get(model, 0) + prompt_tokens + completion_tokens
    )
    _LLM_COST_BY_MODEL[model] = _LLM_COST_BY_MODEL.get(model, 0.0) + cost_usd


class AdminService:
    """System administration: reprocessing pipelines, cost metering, digests."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Feature 9: Admin Reprocess ──────────────────────────────────────────

    async def reprocess_stale_papers(
        self,
        parser_version_lt: str | None = None,
        limit: int = 50,
    ) -> dict:
        """Queue re-parse for papers whose parser_version is outdated.

        If *parser_version_lt* is given, only papers with a lower version string
        are targeted.  Returns the list of queued paper IDs.
        """
        stmt = select(Paper).where(Paper.deleted_at.is_(None))
        if parser_version_lt:
            stmt = stmt.where(
                (Paper.parser_version.is_(None))
                | (Paper.parser_version < parser_version_lt)
            )
        else:
            stmt = stmt.where(Paper.parser_version.is_(None))

        stmt = stmt.limit(limit)
        result = await self.db.execute(stmt)
        papers = result.scalars().all()

        queued_ids: list[str] = []
        for paper in papers:
            try:
                from app.tasks.ingest_tasks import ingest_paper  # local to avoid circ. import
                ingest_paper.delay(str(paper.id), "doi" if paper.doi else "arxiv")
                queued_ids.append(str(paper.id))
            except Exception as exc:  # noqa: BLE001
                logger.warning("reprocess_queue_failed", paper_id=str(paper.id), error=str(exc))

        logger.info(
            "admin_reprocess_queued",
            count=len(queued_ids),
            parser_version_lt=parser_version_lt,
        )
        return {
            "queued_count": len(queued_ids),
            "queued_paper_ids": queued_ids,
            "parser_version_lt": parser_version_lt,
        }

    # ── Feature 35: LLM Cost Metering ───────────────────────────────────────

    async def get_llm_costs(self) -> dict:
        """Return accumulated LLM usage and cost statistics."""
        total_cost = sum(_LLM_COST_BY_MODEL.values())
        total_calls = sum(_LLM_CALLS_BY_MODEL.values())
        total_tokens = sum(_LLM_TOKENS_BY_MODEL.values())

        breakdown = [
            {
                "model": model,
                "calls": _LLM_CALLS_BY_MODEL.get(model, 0),
                "tokens": _LLM_TOKENS_BY_MODEL.get(model, 0),
                "cost_usd": round(_LLM_COST_BY_MODEL.get(model, 0.0), 6),
            }
            for model in sorted(_LLM_COST_BY_MODEL)
        ]

        paper_count_result = await self.db.execute(
            select(func.count()).select_from(Paper).where(Paper.deleted_at.is_(None))
        )
        paper_count: int = paper_count_result.scalar() or 0

        return {
            "total_llm_calls": total_calls,
            "total_tokens": total_tokens,
            "total_cost_usd": round(total_cost, 6),
            "cost_per_paper_usd": round(total_cost / paper_count, 6) if paper_count else None,
            "paper_count": paper_count,
            "breakdown_by_model": breakdown,
            "note": "In-process counters reset on worker restart. "
                    "Integrate Prometheus for persistence.",
        }

    # ── Feature 26: Weekly Digest ────────────────────────────────────────────

    async def get_weekly_digest(self, weeks_back: int = 1) -> dict:
        """Build a digest of papers ingested in the last *weeks_back* weeks.

        Returns counts, top keywords, and a list of highlights (papers with
        the highest citation count or summary content).
        """
        since = datetime.now(tz=timezone.utc) - timedelta(weeks=weeks_back)

        stmt = (
            select(Paper)
            .where(Paper.deleted_at.is_(None), Paper.created_at >= since)
            .order_by(Paper.citation_count.desc().nullslast(), Paper.created_at.desc())
        )
        result = await self.db.execute(stmt)
        papers = result.scalars().all()

        if not papers:
            return {
                "period_start": since.isoformat(),
                "paper_count": 0,
                "highlights": [],
                "keyword_frequency": {},
                "open_access_count": 0,
                "sources": {},
            }

        keyword_freq: dict[str, int] = {}
        sources: dict[str, int] = {}
        oa_count = 0

        for p in papers:
            kws = p.keywords or []
            if isinstance(kws, list):
                for kw in kws[:10]:
                    keyword_freq[kw] = keyword_freq.get(kw, 0) + 1
            elif isinstance(kws, dict):
                for kw in list(kws.keys())[:10]:
                    keyword_freq[kw] = keyword_freq.get(kw, 0) + 1

            src = p.source_type or "unknown"
            sources[src] = sources.get(src, 0) + 1

            raw = p.raw_metadata or {}
            if raw.get("oa_status") in ("gold", "green", "diamond", "hybrid"):
                oa_count += 1

        top_keywords = sorted(keyword_freq, key=keyword_freq.get, reverse=True)[:15]  # type: ignore[arg-type]

        highlights = [
            {
                "paper_id": str(p.id),
                "title": p.title,
                "authors": p.authors[:3] if isinstance(p.authors, list) else [],
                "published_at": str(p.published_at) if p.published_at else None,
                "citation_count": p.citation_count,
                "doi": p.doi,
                "arxiv_id": p.arxiv_id,
                "summary_snippet": (p.summary or "")[:200] or None,
            }
            for p in papers[:20]
        ]

        return {
            "period_start": since.isoformat(),
            "period_end": datetime.now(tz=timezone.utc).isoformat(),
            "paper_count": len(papers),
            "open_access_count": oa_count,
            "highlights": highlights,
            "top_keywords": top_keywords,
            "keyword_frequency": {k: keyword_freq[k] for k in top_keywords},
            "sources": sources,
        }
