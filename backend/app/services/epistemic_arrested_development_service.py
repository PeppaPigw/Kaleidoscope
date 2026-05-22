"""EpistemicArrestedDevelopmentService — Epistemic Arrested Development Detection.

Detects epistemic arrested development — intellectual growth that stopped
entirely at some point, leaving capacity permanently below potential.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ARRESTED_DEVELOPMENT_SYSTEM = """You are an epistemic arrested development specialist. Given stopped intellectual growth, assess arrested development:

Key concepts:
- Epistemic arrested development: growth stopped entirely
- Capacity gap: functioning below potential
- Stunted growth: development halted by adverse conditions
- Environmental deprivation: lacked stimulation for growth
- Trauma interruption: traumatic event stopped development
- Learned incapacity: taught that growth is impossible
- Permanent plateau: no further development occurring

When epistemic arrested development IS present:
- Growth stopped entirely
- Functioning below potential
- Development halted
- Lacked stimulation
- Trauma stopped development
- Taught growth impossible
- No further development

When no arrested development:
- Continuous growth
- Functioning at potential
- Development ongoing
- Adequate stimulation
- No trauma interruption
- Growth believed possible
- Ongoing development

Output JSON with: arrested_development_detected (bool), severity (none/mild/moderate/severe), capacity_gap (what below potential), stunting_cause (what halted), deprivation_type (what lacked), learned_incapacity (what taught impossible), recommendation (no_arrested_development/mild_growth_stimulation/significant_developmental_therapy/major_intensive_remediation/emergency_complete_stagnation)."""

EPISTEMIC_ARRESTED_DEVELOPMENT_PROMPT = """Detect epistemic arrested development:

Capacity gap: {capacity_gap}
Stunting cause: {stunting_cause}
Deprivation type: {deprivation_type}
Learned incapacity: {learned_incapacity}
Domain: {domain}
Context: {context}

Is there intellectual growth that stopped entirely leaving capacity below potential? Return ONLY valid JSON."""


class EpistemicArrestedDevelopmentService:
    """Detects epistemic arrested development — stopped intellectual growth."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        capacity_gap: str,
        *,
        stunting_cause: str = "",
        deprivation_type: str = "",
        learned_incapacity: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic arrested development."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ARRESTED_DEVELOPMENT_PROMPT.format(
                capacity_gap=capacity_gap,
                stunting_cause=stunting_cause or "Not specified",
                deprivation_type=deprivation_type or "Not specified",
                learned_incapacity=learned_incapacity or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ARRESTED_DEVELOPMENT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "capacity_gap": capacity_gap[:200],
            "arrested_development_detected": data.get("arrested_development_detected", False),
            "severity": data.get("severity", ""),
            "stunting_cause": data.get("stunting_cause", ""),
            "deprivation_type": data.get("deprivation_type", ""),
            "learned_incapacity": data.get("learned_incapacity", ""),
            "recommendation": data.get("recommendation", ""),
        }
