"""ScopeNeglectAsymmetryService — Scope Neglect Asymmetry Detection.

Detects scope neglect asymmetry — caring about problems differently
based on scale in inconsistent ways, where emotional response does
not scale proportionally with the magnitude of the problem.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

SCOPE_NEGLECT_ASYMMETRY_SYSTEM = """You are a scope neglect asymmetry specialist. Given a response or decision, assess whether emotional or practical response scales inconsistently with problem magnitude:

Key concepts:
- Scope neglect asymmetry: response doesn't scale with magnitude
- Psychic numbing: caring less as numbers increase
- Compassion fade: empathy decreasing with scale
- Identifiable victim effect: one death is tragedy, million is statistic
- Proportion neglect: ignoring relative scale
- Flat affect for large numbers: emotional response plateaus
- Inconsistent valuation: same life valued differently at different scales

When scope neglect asymmetry IS present:
- Response doesn't scale with magnitude of problem
- Small-scale problems get disproportionate attention
- Large-scale problems get insufficient response
- Emotional engagement inversely related to scale
- Same unit (life, dollar, etc.) valued differently at different scales
- Identifiable cases prioritized over statistical ones
- Proportion ignored in favor of absolute numbers or narratives

When non-proportional response is appropriate:
- Diminishing marginal utility genuinely applies
- Practical constraints limit response regardless of scale
- Qualitative differences between scales acknowledged
- Non-linearity justified by specific reasoning
- Triage decisions made explicitly
- Scale acknowledged even if response is limited
- Asymmetry is a conscious choice, not unconscious bias

Output JSON with: asymmetry_present (bool), severity (none/mild/moderate/severe), response (what response is given), scale_small (small-scale response), scale_large (large-scale response), inconsistency (how response is inconsistent), recommendation (appropriate_non_linear_response/mild_scope_neglect/significant_asymmetry/major_proportion_blindness/scale_response_proportionally)."""

SCOPE_NEGLECT_ASYMMETRY_PROMPT = """Detect scope neglect asymmetry:

Response: {response}
Small scale: {small}
Large scale: {large}
Proportionality: {proportionality}
Domain: {domain}
Context: {context}

Does the response fail to scale proportionally with the magnitude of the problem? Return ONLY valid JSON."""


class ScopeNeglectAsymmetryService:
    """Detects scope neglect asymmetry — response not scaling with magnitude."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        response: str,
        *,
        small: str = "",
        large: str = "",
        proportionality: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect scope neglect asymmetry."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=SCOPE_NEGLECT_ASYMMETRY_PROMPT.format(
                response=response,
                small=small or "Not specified",
                large=large or "Not specified",
                proportionality=proportionality or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=SCOPE_NEGLECT_ASYMMETRY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "response": response[:200],
            "asymmetry_present": data.get("asymmetry_present", False),
            "severity": data.get("severity", ""),
            "scale_small": data.get("scale_small", ""),
            "scale_large": data.get("scale_large", ""),
            "inconsistency": data.get("inconsistency", ""),
            "recommendation": data.get("recommendation", ""),
        }
