"""EpistemicMetaScopeInsensitivityService — Epistemic Meta Scope Insensitivity Detection.

Detects scope insensitivity — failing to scale concern/response proportionally to magnitude.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_META_SCOPE_INSENSITIVITY_SYSTEM = """You are an epistemic meta scope insensitivity specialist. Given magnitude indifference, assess response scaling failure:

Key concepts:
- Scope insensitivity: failing to scale concern or response proportionally to magnitude
- Magnitude indifference: similar reaction across very different scales
- Psychic numbing: reduced sensitivity as numbers become large
- Unit bias: focusing on one case or unit rather than total magnitude
- Proportion neglect: ignoring relative scale and proportional impact

When scope insensitivity IS present:
- Response does not scale with magnitude
- Large numbers produce numbness rather than proportionate concern
- One unit dominates the evaluation
- Proportions are ignored
- Similar action is proposed for very different scales

When no scope insensitivity:
- Concern scales with magnitude
- Large numbers are translated into decision-relevant comparisons
- Unit cases are integrated with totals
- Proportions guide prioritization
- Response intensity matches scale

Output JSON with: scope_insensitivity_detected (bool), severity (none/mild/moderate/severe), psychic_numbing (where large-scale sensitivity is reduced), unit_bias (what unit dominates judgment), proportion_neglect (what proportions are ignored), recommendation (no_scope_insensitivity/mild_scale_check/significant_magnitude_mapping/major_scope_recalibration/emergency_complete_response_rescaling)."""

EPISTEMIC_META_SCOPE_INSENSITIVITY_PROMPT = """Detect epistemic meta scope insensitivity:

Magnitude indifference: {magnitude_indifference}
Psychic numbing: {psychic_numbing}
Unit bias: {unit_bias}
Proportion neglect: {proportion_neglect}
Domain: {domain}
Context: {context}

Is concern or response failing to scale proportionally to magnitude? Return ONLY valid JSON."""


class EpistemicMetaScopeInsensitivityService:
    """Detects scope insensitivity — failure to scale response to magnitude."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        magnitude_indifference: str,
        *,
        psychic_numbing: str = "",
        unit_bias: str = "",
        proportion_neglect: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic meta scope insensitivity."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_META_SCOPE_INSENSITIVITY_PROMPT.format(
                magnitude_indifference=magnitude_indifference,
                psychic_numbing=psychic_numbing or "Not specified",
                unit_bias=unit_bias or "Not specified",
                proportion_neglect=proportion_neglect or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_META_SCOPE_INSENSITIVITY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "magnitude_indifference": magnitude_indifference[:200],
            "scope_insensitivity_detected": data.get("scope_insensitivity_detected", False),
            "severity": data.get("severity", ""),
            "psychic_numbing": data.get("psychic_numbing", ""),
            "unit_bias": data.get("unit_bias", ""),
            "proportion_neglect": data.get("proportion_neglect", ""),
            "recommendation": data.get("recommendation", ""),
        }
