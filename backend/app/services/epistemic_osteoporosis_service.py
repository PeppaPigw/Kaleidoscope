"""EpistemicOsteoporosisService — Epistemic Osteoporosis Detection.

Detects epistemic osteoporosis — progressive weakening of intellectual
bone density making the framework fragile and prone to fracture.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_OSTEOPOROSIS_SYSTEM = """You are an epistemic osteoporosis specialist. Given intellectual framework density, assess whether progressive weakening is occurring:

Key concepts:
- Epistemic osteoporosis: progressive weakening of intellectual density
- Bone mineral density: measure of structural strength
- Resorption exceeding formation: losing more than building
- Trabecular thinning: internal support struts weakening
- Fragility: increased susceptibility to fracture
- Silent progression: weakening without symptoms until fracture
- Weight-bearing exercise: activities that strengthen structure

When epistemic osteoporosis IS present:
- Progressive weakening of intellectual framework density
- Measurably reduced structural strength
- Losing more intellectual structure than building
- Internal support struts weakening
- Increased susceptibility to structural failure
- Silent progression until catastrophic break
- Insufficient strengthening activities

When healthy density is present:
- Strong intellectual framework
- High structural strength
- Building exceeding loss
- Strong internal supports
- Resilient to stress
- No silent weakening
- Regular strengthening activities

Output JSON with: osteoporosis_present (bool), severity (none/mild/moderate/severe), bone_density (what structural strength), resorption (what loss exceeding gain), trabecular_thinning (what internal weakening), fragility (what fracture susceptibility), recommendation (healthy_density/mild_osteoporosis/significant_osteoporosis/major_framework_weakening/strengthen_intellectual_density)."""

EPISTEMIC_OSTEOPOROSIS_PROMPT = """Detect epistemic osteoporosis:

Bone density: {bone_density}
Resorption: {resorption}
Trabecular thinning: {trabecular_thinning}
Fragility: {fragility}
Domain: {domain}
Context: {context}

Is intellectual framework density progressively weakening, becoming fragile? Return ONLY valid JSON."""


class EpistemicOsteoporosisService:
    """Detects epistemic osteoporosis — progressive weakening of intellectual density."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        bone_density: str,
        *,
        resorption: str = "",
        trabecular_thinning: str = "",
        fragility: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic osteoporosis."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_OSTEOPOROSIS_PROMPT.format(
                bone_density=bone_density,
                resorption=resorption or "Not specified",
                trabecular_thinning=trabecular_thinning or "Not specified",
                fragility=fragility or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_OSTEOPOROSIS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "bone_density": bone_density[:200],
            "osteoporosis_present": data.get("osteoporosis_present", False),
            "severity": data.get("severity", ""),
            "resorption": data.get("resorption", ""),
            "trabecular_thinning": data.get("trabecular_thinning", ""),
            "fragility": data.get("fragility", ""),
            "recommendation": data.get("recommendation", ""),
        }
