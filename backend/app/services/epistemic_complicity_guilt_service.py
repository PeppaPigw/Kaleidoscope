"""EpistemicComplicityGuiltService — Epistemic Complicity Guilt Detection.

Detects epistemic complicity guilt — guilt over participating in
harmful knowledge systems or institutions.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_COMPLICITY_GUILT_SYSTEM = """You are an epistemic complicity guilt specialist. Given guilt over participating in harmful systems, assess complicity guilt:

Key concepts:
- Epistemic complicity guilt: guilt over participating in harmful systems
- Institutional guilt: guilt about being part of harmful institutions
- System perpetuation: guilt about maintaining harmful structures
- Benefit from harm: guilt about profiting from unjust systems
- Silent complicity: guilt about not speaking up
- Structural participation: guilt about role in harmful patterns
- Reform failure: guilt about not changing systems from within

When epistemic complicity guilt IS present:
- Guilt over participating in harmful systems
- Guilt about harmful institutions
- Guilt about maintaining structures
- Guilt about profiting from injustice
- Guilt about not speaking up
- Guilt about role in patterns
- Guilt about not changing systems

When no complicity guilt:
- Clear conscience about participation
- Comfortable with institutional role
- Working toward change
- Ethical engagement
- Speaking up appropriately
- Conscious participation
- Active reform efforts

Output JSON with: complicity_guilt_detected (bool), severity (none/mild/moderate/severe), institutional_guilt (what institution causing guilt), system_perpetuation (what maintaining), benefit_from_harm (what profiting from), silent_complicity (what not speaking about), recommendation (no_complicity_guilt/mild_ethical_reflection/significant_action_planning/major_intensive_complicity_processing/emergency_paralyzing_systemic_guilt)."""

EPISTEMIC_COMPLICITY_GUILT_PROMPT = """Detect epistemic complicity guilt:

Institutional guilt: {institutional_guilt}
System perpetuation: {system_perpetuation}
Benefit from harm: {benefit_from_harm}
Silent complicity: {silent_complicity}
Domain: {domain}
Context: {context}

Is there guilt over participating in harmful knowledge systems? Return ONLY valid JSON."""


class EpistemicComplicityGuiltService:
    """Detects epistemic complicity guilt — guilt over participating in harmful systems."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        institutional_guilt: str,
        *,
        system_perpetuation: str = "",
        benefit_from_harm: str = "",
        silent_complicity: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic complicity guilt."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_COMPLICITY_GUILT_PROMPT.format(
                institutional_guilt=institutional_guilt,
                system_perpetuation=system_perpetuation or "Not specified",
                benefit_from_harm=benefit_from_harm or "Not specified",
                silent_complicity=silent_complicity or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_COMPLICITY_GUILT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "institutional_guilt": institutional_guilt[:200],
            "complicity_guilt_detected": data.get("complicity_guilt_detected", False),
            "severity": data.get("severity", ""),
            "system_perpetuation": data.get("system_perpetuation", ""),
            "benefit_from_harm": data.get("benefit_from_harm", ""),
            "silent_complicity": data.get("silent_complicity", ""),
            "recommendation": data.get("recommendation", ""),
        }
