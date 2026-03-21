"""Structured extraction service — highlights, methods, limitations using LLM."""

import json

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.llm_client import LLMClient
from app.models.paper import Paper
from app.services.extraction.chunker import TextChunker
from app.services.extraction.prompts import (
    EXTRACT_SYSTEM,
    EXTRACT_HIGHLIGHTS,
    EXTRACT_METHODS,
)

logger = structlog.get_logger(__name__)


class ExtractionService:
    """Extract structured information from papers using LLM."""

    def __init__(self, db: AsyncSession, llm: LLMClient | None = None):
        self.db = db
        self.llm = llm or LLMClient()

    async def extract_highlights(self, paper: Paper) -> dict:
        """
        Extract highlights, contributions, limitations, and future work.

        Returns parsed JSON with these keys:
        - highlights: list[str]
        - contributions: list[str]
        - limitations: list[str]
        - future_work: list[str]
        - novelty_claim: str
        """
        fulltext = TextChunker.prepare_paper_text(paper)
        # Truncate for context window
        if len(fulltext.split()) > 15000:
            fulltext = " ".join(fulltext.split()[:15000]) + "\n[... truncated]"

        prompt = EXTRACT_HIGHLIGHTS.format(
            title=paper.title,
            abstract=paper.abstract or "(not available)",
            fulltext=fulltext or "(not available)",
        )

        result = await self.llm.complete_json(
            prompt=prompt, system=EXTRACT_SYSTEM, max_tokens=2000,
        )

        # Store extracted data on paper
        paper.highlights = result.get("highlights")
        paper.contributions = result.get("contributions")
        paper.limitations = result.get("limitations")

        logger.info("highlights_extracted", paper_id=str(paper.id),
                     highlights=len(result.get("highlights", [])))
        return result

    async def extract_methods(self, paper: Paper) -> dict:
        """
        Extract methods, datasets, metrics, and baselines.

        Returns parsed JSON with:
        - methods: list of {name, description, is_novel}
        - datasets: list of {name, size, domain}
        - metrics: list of {name, value, is_main_result}
        - baselines: list[str]
        - implementation_details: dict
        """
        fulltext = TextChunker.prepare_paper_text(paper)
        if len(fulltext.split()) > 15000:
            fulltext = " ".join(fulltext.split()[:15000]) + "\n[... truncated]"

        prompt = EXTRACT_METHODS.format(
            title=paper.title,
            abstract=paper.abstract or "(not available)",
            fulltext=fulltext or "(not available)",
        )

        result = await self.llm.complete_json(
            prompt=prompt, system=EXTRACT_SYSTEM, max_tokens=3000,
        )

        logger.info("methods_extracted", paper_id=str(paper.id),
                     methods=len(result.get("methods", [])),
                     datasets=len(result.get("datasets", [])))
        return result

    async def close(self) -> None:
        await self.llm.close()
