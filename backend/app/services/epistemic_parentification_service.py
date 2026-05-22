"""EpistemicParentificationService — Epistemic Parentification Detection.

Detects epistemic parentification — being forced into intellectual caretaker
role prematurely, providing epistemic support that should come from authority.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PARENTIFICATION_SYSTEM = """You are an epistemic parentification specialist. Given premature intellectual caretaking, assess parentification:

Key concepts:
- Epistemic parentification: forced into caretaker role prematurely
- Role reversal: providing support that should come from authority
- Premature responsibility: carrying intellectual burden too early
- Lost development: missed own intellectual growth stages
- Hypercompetence: appearing capable while internally depleted
- Resentment: anger at unfair intellectual burden
- Burnout: exhaustion from carrying others' epistemic needs

When epistemic parentification IS present:
- Forced into caretaker role
- Providing support authority should give
- Carrying burden too early
- Missed growth stages
- Appearing capable while depleted
- Anger at unfair burden
- Exhaustion from carrying others

When no parentification:
- Age-appropriate role
- Authority provides support
- Appropriate responsibility
- Normal development
- Genuine competence
- Fair distribution
- Sustainable engagement

Output JSON with: parentification_detected (bool), severity (none/mild/moderate/severe), role_reversal (what providing), premature_burden (what too early), lost_development (what missed), resentment_level (what anger), recommendation (no_parentification/mild_role_correction/significant_boundary_therapy/major_intensive_recovery/emergency_complete_burnout)."""

EPISTEMIC_PARENTIFICATION_PROMPT = """Detect epistemic parentification:

Role reversal: {role_reversal}
Premature burden: {premature_burden}
Lost development: {lost_development}
Resentment level: {resentment_level}
Domain: {domain}
Context: {context}

Is there premature forcing into intellectual caretaker role? Return ONLY valid JSON."""


class EpistemicParentificationService:
    """Detects epistemic parentification — premature intellectual caretaking."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        role_reversal: str,
        *,
        premature_burden: str = "",
        lost_development: str = "",
        resentment_level: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic parentification."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PARENTIFICATION_PROMPT.format(
                role_reversal=role_reversal,
                premature_burden=premature_burden or "Not specified",
                lost_development=lost_development or "Not specified",
                resentment_level=resentment_level or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PARENTIFICATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "role_reversal": role_reversal[:200],
            "parentification_detected": data.get("parentification_detected", False),
            "severity": data.get("severity", ""),
            "premature_burden": data.get("premature_burden", ""),
            "lost_development": data.get("lost_development", ""),
            "resentment_level": data.get("resentment_level", ""),
            "recommendation": data.get("recommendation", ""),
        }
