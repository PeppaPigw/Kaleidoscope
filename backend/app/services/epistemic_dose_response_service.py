"""EpistemicDoseResponseService — Epistemic Dose-Response Detection.

Detects epistemic dose-response patterns — relationship between exposure
amount and intellectual damage, where more exposure causes more harm.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_DOSE_RESPONSE_SYSTEM = """You are an epistemic dose-response specialist. Given intellectual exposure patterns, assess the relationship between amount and damage:

Key concepts:
- Epistemic dose-response: relationship between exposure and damage
- Threshold dose: minimum amount causing detectable effect
- LD50: dose causing 50% intellectual function loss
- Hormesis: low dose beneficial, high dose harmful
- Potency: how little is needed to cause effect
- Synergy: combined exposures worse than sum
- Tolerance: reduced response after repeated exposure

When epistemic dose-response IS present:
- Clear relationship between exposure amount and damage
- Identifiable threshold for detectable effect
- Known dose causing significant function loss
- Possible low-dose benefit with high-dose harm
- High potency requiring little for effect
- Combined exposures amplifying damage
- Tolerance developing from repeated exposure

When no dose-response is present:
- No relationship between amount and effect
- No identifiable threshold
- No predictable function loss
- Consistent effect regardless of dose
- Low potency
- No synergistic effects
- No tolerance development

Output JSON with: dose_response_present (bool), severity (none/mild/moderate/severe), threshold_dose (what minimum for effect), potency (what little needed), synergy (what combined amplification), tolerance (what reduced response), recommendation (no_dose_response/mild_dose_response/significant_dose_response/major_dose_dependent_damage/reduce_intellectual_exposure_dose)."""

EPISTEMIC_DOSE_RESPONSE_PROMPT = """Detect epistemic dose-response:

Threshold dose: {threshold_dose}
Potency: {potency}
Synergy: {synergy}
Tolerance: {tolerance}
Domain: {domain}
Context: {context}

Is there a clear relationship between intellectual exposure amount and damage? Return ONLY valid JSON."""


class EpistemicDoseResponseService:
    """Detects epistemic dose-response — exposure-damage relationship."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        threshold_dose: str,
        *,
        potency: str = "",
        synergy: str = "",
        tolerance: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic dose-response."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_DOSE_RESPONSE_PROMPT.format(
                threshold_dose=threshold_dose,
                potency=potency or "Not specified",
                synergy=synergy or "Not specified",
                tolerance=tolerance or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_DOSE_RESPONSE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "threshold_dose": threshold_dose[:200],
            "dose_response_present": data.get("dose_response_present", False),
            "severity": data.get("severity", ""),
            "potency": data.get("potency", ""),
            "synergy": data.get("synergy", ""),
            "tolerance": data.get("tolerance", ""),
            "recommendation": data.get("recommendation", ""),
        }
