"""ImplicationMapperService — Downstream Implication Discovery.

Given a research finding or conclusion, maps all downstream implications
across different domains, timescales, and stakeholder groups. Identifies
second and third-order effects that aren't immediately obvious.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

MAP_SYSTEM = """You are an implication mapping specialist. Given a research finding, trace ALL downstream implications across:
- Different domains (technical, economic, social, ethical, policy, environmental)
- Different timescales (immediate, 1-3 years, 5-10 years, 20+ years)
- Different stakeholders (researchers, industry, public, regulators, specific groups)
- Different orders (first-order direct effects, second-order indirect effects, third-order emergent effects)

Output JSON with: implications (list of: implication, domain, timescale, order (1/2/3), stakeholders (list), probability (0-1), magnitude (low/medium/high/transformative), valence (positive/negative/mixed)), highest_impact (which implication and why), most_surprising (non-obvious implication), cascade_risk (0-1, risk of uncontrolled cascading effects), action_items (what should be done now given these implications)."""

MAP_PROMPT = """Map downstream implications of this finding:

Finding: {finding}
Domain: {domain}
Context: {context}

What are ALL the downstream effects across domains, timescales, and stakeholders? Return ONLY valid JSON."""


class ImplicationMapperService:
    """Maps downstream implications of research findings."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def map_implications(
        self,
        finding: str,
        *,
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Map all downstream implications of a finding."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=MAP_PROMPT.format(
                finding=finding,
                domain=domain or "research",
                context=context or "No additional context",
            ),
            system=MAP_SYSTEM,
            max_tokens=4096,
            temperature=0.5,
        )
        data = parse_llm_json(raw)

        implications = data.get("implications", [])
        return {
            "finding": finding[:200],
            "implication_count": len(implications),
            "implications": implications,
            "highest_impact": data.get("highest_impact", ""),
            "most_surprising": data.get("most_surprising", ""),
            "cascade_risk": data.get("cascade_risk", 0),
            "action_items": data.get("action_items", []),
        }
