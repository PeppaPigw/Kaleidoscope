"""Paper analyst — full-spectrum LLM analysis of topic, method, and novelty.

Called after MinerU conversion in seed_arxiv (and available as a standalone service).
Stores the complete analysis in Paper.deep_analysis (JSONB).
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.extraction.prompts import (
    PAPER_ANALYST_PROMPT,
    PAPER_ANALYST_SYSTEM,
)

logger = structlog.get_logger(__name__)

# Chars of full-text to send to the LLM.
# Qwen3-235B-A22B supports 32K output; keep input under ~60K chars (~15K tokens).
MAX_FULLTEXT_CHARS = 60_000


def _format_authors(authors: list[str] | None) -> str:
    if not authors:
        return "Unknown"
    if len(authors) <= 3:
        return ", ".join(authors)
    return f"{authors[0]} et al."


def _extract_year(paper: Any) -> str:
    """Best-effort year from published_at or raw_metadata."""
    if paper.published_at:
        return str(paper.published_at.year)
    if paper.raw_metadata:
        for key in ("year", "published", "date"):
            val = paper.raw_metadata.get(key, "")
            m = re.search(r"\b(19|20)\d{2}\b", str(val))
            if m:
                return m.group()
    return str(datetime.now(timezone.utc).year)


class PaperAnalystService:
    """Generate a full-spectrum paper analysis using the project LLM."""

    def __init__(self, db: AsyncSession | None = None) -> None:
        self.db = db
        self._llm: Any = None

    async def _get_llm(self):
        if self._llm is None:
            from app.clients.llm_client import LLMClient
            self._llm = LLMClient()
        return self._llm

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    async def analyse(self, paper: Any) -> dict[str, Any]:
        """
        Run the full 5-part analysis against `paper`.

        Works directly with a Paper ORM object (no DB lookup needed).
        Returns a dict that can be stored in Paper.deep_analysis.
        """
        log = logger.bind(paper_id=str(paper.id), title=paper.title[:80])

        # Build inputs
        authors_str = _format_authors(
            [a.display_name for a in paper.authors] if hasattr(paper, "authors") and paper.authors
            else paper.raw_metadata.get("authors", []) if paper.raw_metadata else []
        )
        year = _extract_year(paper)
        fulltext = (paper.full_text_markdown or paper.abstract or "").strip()
        if len(fulltext) > MAX_FULLTEXT_CHARS:
            fulltext = fulltext[:MAX_FULLTEXT_CHARS] + "\n\n[... truncated for context limit ...]"

        prompt = PAPER_ANALYST_PROMPT.format(
            title=paper.title,
            authors=authors_str,
            year=year,
            abstract=paper.abstract or "(not available)",
            fulltext=fulltext if fulltext else "(not available)",
        )

        log.info("paper_analysis_start", fulltext_chars=len(fulltext))

        try:
            llm = await self._get_llm()
            raw_text = await llm.complete(
                prompt=prompt,
                system=PAPER_ANALYST_SYSTEM,
                temperature=0.25,       # low temp → dense, consistent output
                max_tokens=8192,        # enough for all 5 parts
            )
        except Exception as exc:
            log.error("paper_analysis_llm_failed", error=str(exc)[:300])
            return {
                "status": "error",
                "error": str(exc)[:300],
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }

        result = {
            "status": "ok",
            "analysis": raw_text,
            "model": "Qwen3-235B-A22B",
            "authors": authors_str,
            "year": year,
            "fulltext_chars": len(fulltext),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        log.info("paper_analysis_done", chars=len(raw_text))
        return result

    async def analyse_and_persist(self, paper: Any, session: AsyncSession) -> dict[str, Any]:
        """
        Run analysis and write the result back to paper.deep_analysis.
        Caller is responsible for committing the session.
        """
        result = await self.analyse(paper)
        paper.deep_analysis = result
        paper.deep_analysis_at = datetime.now(timezone.utc)
        return result

    async def close(self) -> None:
        if self._llm:
            try:
                await self._llm.close()
            except Exception:
                pass
