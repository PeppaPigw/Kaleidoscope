"""EpistemicFrailtyService — Epistemic Frailty Detection.

Detects epistemic frailty — intellectual systems becoming vulnerable to
stressors due to accumulated decline across multiple domains.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_FRAILTY_SYSTEM = """You are an epistemic frailty specialist. Given intellectual vulnerability to stressors, assess frailty:

Key concepts:
- Epistemic frailty: vulnerability from accumulated decline
- Sarcopenia: loss of intellectual muscle/strength
- Falls risk: likelihood of intellectual collapse
- Polypharmacy: too many interventions causing interactions
- Deconditioning: loss of fitness from disuse
- Functional decline: progressive loss of independence
- Frailty index: cumulative deficit measurement

When epistemic frailty IS present:
- Vulnerable to minor stressors
- Loss of intellectual strength
- High risk of collapse
- Too many interventions interacting
- Loss of fitness from disuse
- Progressive independence loss
- High cumulative deficit score

When no frailty:
- Resilient to stressors
- Adequate intellectual strength
- Low collapse risk
- Appropriate intervention level
- Maintained fitness
- Independent function
- Low deficit score

Output JSON with: frailty_detected (bool), severity (none/mild/moderate/severe), strength_status (what muscle/power), falls_risk (what collapse likelihood), polypharmacy (what intervention overload), functional_status (what independence), recommendation (no_frailty/mild_pre_frailty/significant_frailty/major_severe_frailty/advanced_end_stage_frailty)."""

EPISTEMIC_FRAILTY_PROMPT = """Detect epistemic frailty:

Strength status: {strength_status}
Falls risk: {falls_risk}
Polypharmacy: {polypharmacy}
Functional status: {functional_status}
Domain: {domain}
Context: {context}

Is the intellectual system vulnerable to stressors from accumulated decline? Return ONLY valid JSON."""


class EpistemicFrailtyService:
    """Detects epistemic frailty — vulnerability from accumulated decline."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        strength_status: str,
        *,
        falls_risk: str = "",
        polypharmacy: str = "",
        functional_status: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic frailty."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_FRAILTY_PROMPT.format(
                strength_status=strength_status,
                falls_risk=falls_risk or "Not specified",
                polypharmacy=polypharmacy or "Not specified",
                functional_status=functional_status or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_FRAILTY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "strength_status": strength_status[:200],
            "frailty_detected": data.get("frailty_detected", False),
            "severity": data.get("severity", ""),
            "falls_risk": data.get("falls_risk", ""),
            "polypharmacy": data.get("polypharmacy", ""),
            "functional_status": data.get("functional_status", ""),
            "recommendation": data.get("recommendation", ""),
        }
