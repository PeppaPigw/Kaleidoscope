"""EpistemicMotivationCorruptionService — Epistemic Motivation Corruption Detection.

Detects epistemic motivation corruption — external incentives corrupting
epistemic motivation and undermining genuine inquiry.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_MOTIVATION_CORRUPTION_SYSTEM = """You are an epistemic motivation corruption specialist. Given external incentives corrupting epistemic motivation, assess motivation corruption:

Key concepts:
- Epistemic motivation corruption: external incentives corrupting epistemic motivation
- Incentive contamination: incentives contaminating inquiry
- Funding bias: funding sources biasing conclusions
- Career pressure: career pressures distorting inquiry
- Publication bias: publication incentives distorting research
- Reward distortion: rewards distorting what gets investigated
- Market corruption: market forces corrupting epistemic values

When epistemic motivation corruption IS present:
- External incentives corrupting motivation
- Incentives contaminating inquiry
- Funding biasing conclusions
- Career pressures distorting
- Publication incentives distorting
- Rewards distorting investigation
- Market forces corrupting values

When no motivation corruption:
- Motivation internally driven
- Incentives separate from inquiry
- Funding not biasing
- Career not distorting
- Publication not distorting
- Rewards aligned with truth
- Market forces not corrupting

Output JSON with: motivation_corruption_detected (bool), severity (none/mild/moderate/severe), incentive_contamination (what incentives contaminating), funding_bias (what funding biasing), career_pressure (what career pressures distorting), publication_bias (what publication incentives distorting), recommendation (no_motivation_corruption/mild_incentive_awareness/significant_independence_recovery/major_intensive_motivation_purification/emergency_complete_motivation_corruption)."""

EPISTEMIC_MOTIVATION_CORRUPTION_PROMPT = """Detect epistemic motivation corruption:

Incentive contamination: {incentive_contamination}
Funding bias: {funding_bias}
Career pressure: {career_pressure}
Publication bias: {publication_bias}
Domain: {domain}
Context: {context}

Are external incentives corrupting epistemic motivation? Return ONLY valid JSON."""


class EpistemicMotivationCorruptionService:
    """Detects epistemic motivation corruption — external incentives corrupting motivation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        incentive_contamination: str,
        *,
        funding_bias: str = "",
        career_pressure: str = "",
        publication_bias: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic motivation corruption."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_MOTIVATION_CORRUPTION_PROMPT.format(
                incentive_contamination=incentive_contamination,
                funding_bias=funding_bias or "Not specified",
                career_pressure=career_pressure or "Not specified",
                publication_bias=publication_bias or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_MOTIVATION_CORRUPTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "incentive_contamination": incentive_contamination[:200],
            "motivation_corruption_detected": data.get("motivation_corruption_detected", False),
            "severity": data.get("severity", ""),
            "funding_bias": data.get("funding_bias", ""),
            "career_pressure": data.get("career_pressure", ""),
            "publication_bias": data.get("publication_bias", ""),
            "recommendation": data.get("recommendation", ""),
        }
