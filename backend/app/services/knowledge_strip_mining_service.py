"""KnowledgeStripMiningService — Knowledge Strip Mining Detection.

Detects knowledge strip mining — extracting knowledge from a source
without sustaining or replenishing it.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

KNOWLEDGE_STRIP_MINING_SYSTEM = """You are a knowledge strip mining specialist. Given a knowledge extraction pattern, assess whether knowledge is being extracted without sustaining the source:

Key concepts:
- Knowledge strip mining: extracting without sustaining source
- Unsustainable extraction: taking knowledge faster than it regenerates
- Source depletion: depleting knowledge sources without replenishment
- Extractive relationship: purely extractive knowledge relationship
- Knowledge exhaustion: exhausting a knowledge source
- Non-renewable extraction: treating renewable knowledge as non-renewable
- Source degradation: degrading knowledge sources through extraction

When knowledge strip mining IS present:
- Knowledge extracted without sustaining the source
- Source depleted faster than it can regenerate
- Extractive relationship without investment
- Knowledge source exhausted through overuse
- No effort to replenish or sustain
- Source degraded through extraction pattern
- Unsustainable extraction rate

When sustainable knowledge use is present:
- Knowledge extracted at sustainable rate
- Source maintained and replenished
- Investment in knowledge generation
- Sustainable relationship with sources
- Effort to sustain and grow sources
- Source enhanced through engagement

Output JSON with: strip_mining_present (bool), severity (none/mild/moderate/severe), source (what knowledge source is affected), extraction_rate (how fast extraction occurs), sustainability (whether extraction is sustainable), depletion (what depletion occurs), recommendation (sustainable_use/mild_overextraction/significant_strip_mining/major_source_depletion/sustain_knowledge_sources)."""

KNOWLEDGE_STRIP_MINING_PROMPT = """Detect knowledge strip mining:

Source: {source}
Extraction pattern: {extraction}
Sustainability: {sustainability}
Investment: {investment}
Domain: {domain}
Context: {context}

Is knowledge being extracted without sustaining the source? Return ONLY valid JSON."""


class KnowledgeStripMiningService:
    """Detects knowledge strip mining — extracting without sustaining source."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        source: str,
        *,
        extraction: str = "",
        sustainability: str = "",
        investment: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect knowledge strip mining."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=KNOWLEDGE_STRIP_MINING_PROMPT.format(
                source=source,
                extraction=extraction or "Not specified",
                sustainability=sustainability or "Not specified",
                investment=investment or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=KNOWLEDGE_STRIP_MINING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "source": source[:200],
            "strip_mining_present": data.get("strip_mining_present", False),
            "severity": data.get("severity", ""),
            "extraction_rate": data.get("extraction_rate", ""),
            "sustainability": data.get("sustainability", ""),
            "depletion": data.get("depletion", ""),
            "recommendation": data.get("recommendation", ""),
        }
