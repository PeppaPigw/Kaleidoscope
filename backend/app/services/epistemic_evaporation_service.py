"""EpistemicEvaporationService — Epistemic Evaporation Detection.

Detects epistemic evaporation — knowledge gradually disappearing
from a community without being noticed.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_EVAPORATION_SYSTEM = """You are an epistemic evaporation specialist. Given a knowledge loss pattern, assess whether knowledge is gradually disappearing unnoticed:

Key concepts:
- Epistemic evaporation: knowledge gradually disappearing unnoticed
- Gradual loss: slow loss not triggering alarm
- Invisible departure: knowledge leaving without being noticed
- Expertise drain: expertise gradually draining away
- Institutional memory loss: institutional memory evaporating
- Skill atrophy: skills atrophying from disuse
- Knowledge half-life: knowledge decaying over time

When epistemic evaporation IS present:
- Knowledge gradually disappearing without being noticed
- Slow loss not triggering any alarm
- Knowledge leaving the community invisibly
- Expertise gradually draining away
- Institutional memory evaporating
- Skills atrophying from disuse
- Knowledge decaying over time unnoticed

When knowledge retention is present:
- Knowledge actively maintained and preserved
- Loss detected and addressed promptly
- Knowledge departure noticed and managed
- Expertise actively maintained
- Institutional memory preserved
- Skills maintained through practice
- Knowledge refreshed and updated

Output JSON with: evaporation_present (bool), severity (none/mild/moderate/severe), knowledge (what knowledge evaporates), rate (how fast it disappears), invisibility (how invisible the loss is), impact (what impact results), recommendation (knowledge_retention/mild_loss/significant_evaporation/major_invisible_drain/implement_retention_strategy)."""

EPISTEMIC_EVAPORATION_PROMPT = """Detect epistemic evaporation:

Knowledge: {knowledge}
Rate: {rate}
Invisibility: {invisibility}
Impact: {impact}
Domain: {domain}
Context: {context}

Is knowledge gradually disappearing from the community without being noticed? Return ONLY valid JSON."""


class EpistemicEvaporationService:
    """Detects epistemic evaporation — knowledge gradually disappearing unnoticed."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        knowledge: str,
        *,
        rate: str = "",
        invisibility: str = "",
        impact: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic evaporation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_EVAPORATION_PROMPT.format(
                knowledge=knowledge,
                rate=rate or "Not specified",
                invisibility=invisibility or "Not specified",
                impact=impact or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_EVAPORATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "knowledge": knowledge[:200],
            "evaporation_present": data.get("evaporation_present", False),
            "severity": data.get("severity", ""),
            "rate": data.get("rate", ""),
            "invisibility": data.get("invisibility", ""),
            "impact": data.get("impact", ""),
            "recommendation": data.get("recommendation", ""),
        }
