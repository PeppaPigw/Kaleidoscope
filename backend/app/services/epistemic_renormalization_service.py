"""EpistemicRenormalizationService — Epistemic Renormalization Detection.

Detects epistemic renormalization — removing infinities from intellectual
calculations by redefining parameters at different scales.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_RENORMALIZATION_SYSTEM = """You are an epistemic renormalization specialist. Given an intellectual calculation, assess whether infinities are being removed by redefining parameters:

Key concepts:
- Epistemic renormalization: removing infinities by redefining parameters
- Bare parameter: original undefined quantity
- Dressed parameter: physically meaningful redefined quantity
- Running coupling: parameter changing with scale
- Ultraviolet divergence: infinity at small scales
- Infrared divergence: infinity at large scales
- Counterterm: added term to cancel infinity

When epistemic renormalization IS present:
- Infinities appearing in intellectual calculations
- Original parameters being undefined or infinite
- Physically meaningful redefinitions replacing bare values
- Parameters changing meaning at different scales
- Divergences at very detailed examination
- Divergences at very broad examination
- Added corrections canceling problematic infinities

When finite calculation is present:
- No infinities in calculations
- Parameters well-defined at all scales
- No need for redefinition
- Parameters constant across scales
- No divergences at any level
- Consistent results at all scales
- No corrections needed

Output JSON with: renormalization_present (bool), severity (none/mild/moderate/severe), bare_parameter (what undefined quantity), running_coupling (what scale dependence), ultraviolet (what small-scale infinity), counterterm (what correction), recommendation (finite_calculation/mild_renormalization/significant_renormalization/major_divergence/apply_renormalization_group)."""

EPISTEMIC_RENORMALIZATION_PROMPT = """Detect epistemic renormalization:

Bare parameter: {bare_parameter}
Running coupling: {running_coupling}
Ultraviolet: {ultraviolet}
Counterterm: {counterterm}
Domain: {domain}
Context: {context}

Are infinities being removed from intellectual calculations by redefining parameters at different scales? Return ONLY valid JSON."""


class EpistemicRenormalizationService:
    """Detects epistemic renormalization — removing infinities by redefining parameters."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        bare_parameter: str,
        *,
        running_coupling: str = "",
        ultraviolet: str = "",
        counterterm: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic renormalization."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_RENORMALIZATION_PROMPT.format(
                bare_parameter=bare_parameter,
                running_coupling=running_coupling or "Not specified",
                ultraviolet=ultraviolet or "Not specified",
                counterterm=counterterm or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_RENORMALIZATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "bare_parameter": bare_parameter[:200],
            "renormalization_present": data.get("renormalization_present", False),
            "severity": data.get("severity", ""),
            "running_coupling": data.get("running_coupling", ""),
            "ultraviolet": data.get("ultraviolet", ""),
            "counterterm": data.get("counterterm", ""),
            "recommendation": data.get("recommendation", ""),
        }
