"""Summarization service — multi-level paper summaries using LLM."""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.llm_client import LLMClient
from app.models.paper import Paper
from app.services.extraction.chunker import TextChunker
from app.services.extraction.prompts import (
    SUMMARIZE_SYSTEM,
    SUMMARIZE_TWEET,
    SUMMARIZE_ABSTRACT,
    SUMMARIZE_EXECUTIVE,
    SUMMARIZE_DETAILED,
)

logger = structlog.get_logger(__name__)


LEVEL_CONFIG = {
    "tweet": {"template": SUMMARIZE_TWEET, "max_tokens": 200, "model": "gpt-4o-mini"},
    "abstract": {
        "template": SUMMARIZE_ABSTRACT,
        "max_tokens": 600,
        "model": "gpt-4o-mini",
    },
    "executive": {
        "template": SUMMARIZE_EXECUTIVE,
        "max_tokens": 1500,
        "model": "gpt-4o-mini",
    },
    "detailed": {"template": SUMMARIZE_DETAILED, "max_tokens": 4000, "model": "gpt-4o"},
}


class SummarizationService:
    """Generate multi-level paper summaries using LLM."""

    def __init__(self, db: AsyncSession, llm: LLMClient | None = None):
        self.db = db
        self.llm = llm or LLMClient()
        self.chunker = TextChunker()

    async def summarize(self, paper: Paper, level: str = "abstract") -> dict:
        """
        Generate a summary at the specified level.

        Levels:
        - tweet: 1-2 sentences (~50 words)
        - abstract: Structured 4-part summary (~300 words)
        - executive: For research leads (~800 words)
        - detailed: Comprehensive (~2000 words)

        Returns dict with summary text, level, and model used.
        """
        if level not in LEVEL_CONFIG:
            raise ValueError(
                f"Invalid level: {level}. Must be one of {list(LEVEL_CONFIG.keys())}"
            )

        config = LEVEL_CONFIG[level]
        log = logger.bind(paper_id=str(paper.id), level=level)

        # Assemble full text
        fulltext = TextChunker.prepare_paper_text(paper)

        # Truncate fulltext to fit context window
        # GPT-4o-mini: 128K context, but we limit to ~30K words for cost
        max_text_words = 10000 if level in ("tweet", "abstract") else 25000
        fulltext_words = fulltext.split()
        if len(fulltext_words) > max_text_words:
            fulltext = " ".join(fulltext_words[:max_text_words]) + "\n[... truncated]"

        prompt = config["template"].format(
            title=paper.title,
            abstract=paper.abstract or "(not available)",
            fulltext=fulltext if fulltext else "(not available — using abstract only)",
        )

        summary = await self.llm.complete(
            prompt=prompt,
            system=SUMMARIZE_SYSTEM,
            model=config["model"],
            max_tokens=config["max_tokens"],
            temperature=0.3,
        )

        log.info("summary_generated", level=level, length=len(summary))

        return {
            "paper_id": str(paper.id),
            "level": level,
            "summary": summary,
            "model": config["model"],
            "fulltext_available": bool(fulltext and fulltext != paper.abstract),
        }

    async def close(self) -> None:
        await self.llm.close()
