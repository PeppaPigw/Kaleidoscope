"""EpistemicTemperingService — Epistemic Tempering Detection.

Detects epistemic tempering failure — knowledge not properly tempered,
remaining brittle and shattering under stress rather than flexing.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_TEMPERING_SYSTEM = """You are an epistemic tempering specialist. Given a knowledge structure, assess whether it lacks proper tempering:

Key concepts:
- Epistemic tempering: process of making knowledge resilient through controlled stress
- Brittleness: knowledge that shatters rather than flexes under pressure
- Stress failure: knowledge failing under real-world stress
- Hardness without toughness: hard conclusions without resilience
- Quenching without tempering: rapid formation without stress relief
- Fracture points: where brittle knowledge breaks
- Controlled stress: necessary testing that builds resilience

When tempering failure IS present:
- Knowledge not subjected to proper stress testing
- Brittle conclusions that shatter under challenge
- Hard positions without resilience or flexibility
- Rapid conclusion formation without stress relief
- Clear fracture points in reasoning
- Knowledge that breaks rather than bends
- Untested hardness masquerading as strength

When properly tempered knowledge is present:
- Knowledge tested through controlled challenges
- Conclusions that flex under pressure without breaking
- Positions that are both strong and resilient
- Conclusions formed through iterative stress testing
- No obvious fracture points
- Knowledge that bends appropriately under stress
- Genuine strength through tested resilience

Output JSON with: tempering_failure (bool), severity (none/mild/moderate/severe), knowledge (what knowledge is brittle), brittleness (how brittle), stress_points (where it breaks), formation (how it was formed too quickly), recommendation (properly_tempered/mild_brittleness/significant_tempering_failure/major_fracture_risk/apply_controlled_stress)."""

EPISTEMIC_TEMPERING_PROMPT = """Detect epistemic tempering failure:

Knowledge: {knowledge}
Brittleness: {brittleness}
Stress points: {stress_points}
Formation: {formation}
Domain: {domain}
Context: {context}

Is knowledge brittle and untested, likely to shatter under real stress? Return ONLY valid JSON."""


class EpistemicTemperingService:
    """Detects epistemic tempering failure — brittle knowledge that shatters under stress."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        knowledge: str,
        *,
        brittleness: str = "",
        stress_points: str = "",
        formation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic tempering failure."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_TEMPERING_PROMPT.format(
                knowledge=knowledge,
                brittleness=brittleness or "Not specified",
                stress_points=stress_points or "Not specified",
                formation=formation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_TEMPERING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "knowledge": knowledge[:200],
            "tempering_failure": data.get("tempering_failure", False),
            "severity": data.get("severity", ""),
            "brittleness": data.get("brittleness", ""),
            "stress_points": data.get("stress_points", ""),
            "formation": data.get("formation", ""),
            "recommendation": data.get("recommendation", ""),
        }
