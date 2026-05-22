"""EpistemicCountertransferenceService — Epistemic Countertransference Detection.

Detects epistemic countertransference — authority figure's unconscious
emotional reactions to another's intellectual transference.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_COUNTERTRANSFERENCE_SYSTEM = """You are an epistemic countertransference specialist. Given authority's unconscious reactions, assess countertransference:

Key concepts:
- Epistemic countertransference: authority's reactions to transference
- Reactive feelings: emotions triggered by other's projection
- Role enactment: unconsciously playing assigned role
- Boundary blur: losing professional intellectual distance
- Over-identification: merging with other's experience
- Rescue fantasy: wanting to save intellectually
- Avoidance: pulling away from difficult material

When epistemic countertransference IS present:
- Authority reacting to transference
- Emotions triggered by projection
- Playing assigned role
- Losing intellectual distance
- Merging with experience
- Wanting to save
- Pulling away

When no countertransference:
- Neutral engagement
- Own emotions managed
- Maintaining own role
- Appropriate distance
- Separate experience
- Appropriate support
- Staying present

Output JSON with: countertransference_detected (bool), severity (none/mild/moderate/severe), reactive_feelings (what triggered), role_enactment (what playing), boundary_blur (what losing distance), rescue_fantasy (what wanting save), recommendation (no_countertransference/mild_self_monitoring/significant_supervision/major_intensive_analysis/emergency_boundary_collapse)."""

EPISTEMIC_COUNTERTRANSFERENCE_PROMPT = """Detect epistemic countertransference:

Reactive feelings: {reactive_feelings}
Role enactment: {role_enactment}
Boundary blur: {boundary_blur}
Rescue fantasy: {rescue_fantasy}
Domain: {domain}
Context: {context}

Is there authority figure's unconscious emotional reaction to another's transference? Return ONLY valid JSON."""


class EpistemicCountertransferenceService:
    """Detects epistemic countertransference — authority's reactions to transference."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        reactive_feelings: str,
        *,
        role_enactment: str = "",
        boundary_blur: str = "",
        rescue_fantasy: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic countertransference."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_COUNTERTRANSFERENCE_PROMPT.format(
                reactive_feelings=reactive_feelings,
                role_enactment=role_enactment or "Not specified",
                boundary_blur=boundary_blur or "Not specified",
                rescue_fantasy=rescue_fantasy or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_COUNTERTRANSFERENCE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "reactive_feelings": reactive_feelings[:200],
            "countertransference_detected": data.get("countertransference_detected", False),
            "severity": data.get("severity", ""),
            "role_enactment": data.get("role_enactment", ""),
            "boundary_blur": data.get("boundary_blur", ""),
            "rescue_fantasy": data.get("rescue_fantasy", ""),
            "recommendation": data.get("recommendation", ""),
        }
