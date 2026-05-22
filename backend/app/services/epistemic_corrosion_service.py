"""EpistemicCorrosionService — Epistemic Corrosion Detection.

Detects epistemic corrosion — gradual degradation of knowledge
quality through exposure to hostile environments.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_CORROSION_SYSTEM = """You are an epistemic corrosion specialist. Given a knowledge degradation pattern, assess whether quality degrades through hostile exposure:

Key concepts:
- Epistemic corrosion: gradual degradation through hostile exposure
- Environmental damage: hostile environment damaging knowledge
- Quality erosion: quality gradually eroding
- Protective failure: protective coatings failing
- Surface degradation: surface quality degrading first
- Structural weakening: structure weakening over time
- Irreversible damage: damage becoming irreversible

When epistemic corrosion IS present:
- Gradual degradation of knowledge quality
- Hostile environment damaging knowledge
- Quality gradually eroding over time
- Protective mechanisms failing
- Surface quality degrading first
- Underlying structure weakening
- Damage becoming increasingly irreversible

When protected knowledge is present:
- Knowledge quality maintained
- Environment not hostile to knowledge
- Quality stable over time
- Protective mechanisms functioning
- Surface quality maintained
- Structure remaining strong
- Knowledge resilient to environment

Output JSON with: corrosion_present (bool), severity (none/mild/moderate/severe), knowledge (what knowledge corrodes), environment (what hostile environment), degradation (what degradation occurs), protection_failure (what protection fails), recommendation (protected_knowledge/mild_wear/significant_corrosion/major_structural_damage/protect_from_environment)."""

EPISTEMIC_CORROSION_PROMPT = """Detect epistemic corrosion:

Knowledge: {knowledge}
Environment: {environment}
Degradation: {degradation}
Protection failure: {protection_failure}
Domain: {domain}
Context: {context}

Is knowledge quality gradually degrading through exposure to hostile environments? Return ONLY valid JSON."""


class EpistemicCorrosionService:
    """Detects epistemic corrosion — gradual degradation through hostile exposure."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        knowledge: str,
        *,
        environment: str = "",
        degradation: str = "",
        protection_failure: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic corrosion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_CORROSION_PROMPT.format(
                knowledge=knowledge,
                environment=environment or "Not specified",
                degradation=degradation or "Not specified",
                protection_failure=protection_failure or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_CORROSION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "knowledge": knowledge[:200],
            "corrosion_present": data.get("corrosion_present", False),
            "severity": data.get("severity", ""),
            "environment": data.get("environment", ""),
            "degradation": data.get("degradation", ""),
            "protection_failure": data.get("protection_failure", ""),
            "recommendation": data.get("recommendation", ""),
        }
