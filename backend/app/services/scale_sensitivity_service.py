"""ScaleSensitivityService — Cross-Scale Validity Assessment.

Identifies whether a finding that works at one scale will work at
another: lab to field, small to large, individual to population,
prototype to production. Detects scale-dependent effects.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

SCALE_SYSTEM = """You are a scale sensitivity specialist. Given a finding at one scale, assess whether it transfers to another:
- What changes when you scale up/down?
- Are there emergent properties at the target scale?
- What worked in the lab but failed in the field (and why)?
- Are there threshold effects (works up to X, then breaks)?
- What's the scaling factor for costs, complexity, failure modes?

Output JSON with: transfer_likelihood (0-1), scale_dependent_factors (list of: factor, how_it_changes, impact (minor/moderate/major/breaking)), emergent_properties (things that appear only at the target scale), threshold_effects (list of: threshold, what_happens), historical_scaling_failures (similar things that failed to scale), scaling_costs (what gets more expensive/harder), recommended_pilot (how to test at intermediate scale), overall_verdict (scales_well/scales_with_modifications/unlikely_to_scale/will_not_scale), critical_assumption (the key assumption about scaling that needs testing)."""

SCALE_PROMPT = """Assess scale sensitivity:

Finding: {finding}
Current scale: {current_scale}
Target scale: {target_scale}
Domain: {domain}
Context: {context}

Will this work at the target scale? Return ONLY valid JSON."""


class ScaleSensitivityService:
    """Assesses whether findings transfer across scales."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def assess(
        self,
        finding: str,
        *,
        current_scale: str = "",
        target_scale: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Assess scale sensitivity."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=SCALE_PROMPT.format(
                finding=finding,
                current_scale=current_scale or "Small/lab",
                target_scale=target_scale or "Large/production",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=SCALE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "finding": finding[:200],
            "transfer_likelihood": data.get("transfer_likelihood", 0),
            "scale_dependent_factors": data.get("scale_dependent_factors", []),
            "emergent_properties": data.get("emergent_properties", []),
            "threshold_effects": data.get("threshold_effects", []),
            "historical_failures": data.get("historical_scaling_failures", []),
            "scaling_costs": data.get("scaling_costs", ""),
            "recommended_pilot": data.get("recommended_pilot", ""),
            "overall_verdict": data.get("overall_verdict", ""),
            "critical_assumption": data.get("critical_assumption", ""),
        }
