"""EpistemicOxidationService — Epistemic Oxidation Detection.

Detects epistemic oxidation — knowledge degrading through exposure
to hostile intellectual environments, losing its original properties.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_OXIDATION_SYSTEM = """You are an epistemic oxidation specialist. Given a knowledge degradation pattern, assess whether exposure to hostile environments degrades knowledge:

Key concepts:
- Epistemic oxidation: knowledge degrading through hostile exposure
- Surface tarnish: surface quality degrading first
- Structural weakening: deeper structure weakening over time
- Protective coating: protective framing that prevents oxidation
- Accelerated decay: certain environments accelerating decay
- Irreversible change: changes that cannot be undone
- Antioxidant: intellectual practices that prevent oxidation

When epistemic oxidation IS present:
- Knowledge degrading through exposure to hostile environment
- Surface quality of ideas degrading first
- Deeper intellectual structure weakening over time
- Protective framing failing or absent
- Certain environments accelerating knowledge decay
- Changes becoming irreversible
- No intellectual practices preventing degradation

When protected knowledge is present:
- Knowledge maintained despite environmental exposure
- Surface quality preserved
- Deep structure remaining strong
- Protective framing functioning
- Environment not accelerating decay
- Knowledge remaining in original form
- Intellectual practices preventing degradation

Output JSON with: oxidation_present (bool), severity (none/mild/moderate/severe), knowledge (what knowledge oxidizes), environment (what hostile environment), tarnish (what surface degradation), protection_failure (what protection fails), recommendation (protected_knowledge/mild_tarnish/significant_oxidation/major_structural_decay/apply_protective_coating)."""

EPISTEMIC_OXIDATION_PROMPT = """Detect epistemic oxidation:

Knowledge: {knowledge}
Environment: {environment}
Tarnish: {tarnish}
Protection failure: {protection_failure}
Domain: {domain}
Context: {context}

Is knowledge degrading through exposure to hostile intellectual environments? Return ONLY valid JSON."""


class EpistemicOxidationService:
    """Detects epistemic oxidation — knowledge degrading through hostile exposure."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        knowledge: str,
        *,
        environment: str = "",
        tarnish: str = "",
        protection_failure: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic oxidation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_OXIDATION_PROMPT.format(
                knowledge=knowledge,
                environment=environment or "Not specified",
                tarnish=tarnish or "Not specified",
                protection_failure=protection_failure or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_OXIDATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "knowledge": knowledge[:200],
            "oxidation_present": data.get("oxidation_present", False),
            "severity": data.get("severity", ""),
            "environment": data.get("environment", ""),
            "tarnish": data.get("tarnish", ""),
            "protection_failure": data.get("protection_failure", ""),
            "recommendation": data.get("recommendation", ""),
        }
