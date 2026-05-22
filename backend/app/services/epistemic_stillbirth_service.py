"""EpistemicStillbirthService — Epistemic Stillbirth Detection.

Detects epistemic stillbirth — intellectual creation that dies before or
during delivery, never achieving independent function.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_STILLBIRTH_SYSTEM = """You are an epistemic stillbirth specialist. Given intellectual creations that fail to achieve life, assess stillbirth:

Key concepts:
- Epistemic stillbirth: creation dead before achieving function
- Intrauterine death: creation dying before delivery
- Intrapartum death: creation dying during delivery
- Maceration: signs of prolonged death before delivery
- Grief counseling: supporting creators after loss
- Autopsy: determining cause of creation death
- Recurrence risk: likelihood of repeat stillbirth

When epistemic stillbirth IS occurring:
- Creation dead before achieving function
- Died before delivery attempt
- Died during delivery process
- Signs of prolonged pre-delivery death
- Creator support needed after loss
- Cause of death investigation needed
- Risk of repeat occurrence

When no stillbirth:
- Creation alive and functioning
- Viable before delivery
- Surviving delivery process
- No death signs
- No grief needed
- No investigation needed
- No recurrence concern

Output JSON with: stillbirth_detected (bool), severity (none/mild/moderate/severe), death_timing (what when), cause_assessment (what why), maceration_signs (what duration), recurrence_risk (what repeat likelihood), recommendation (no_stillbirth/mild_monitoring/significant_investigation/major_grief_support/comprehensive_loss_management)."""

EPISTEMIC_STILLBIRTH_PROMPT = """Detect epistemic stillbirth:

Death timing: {death_timing}
Cause assessment: {cause_assessment}
Maceration signs: {maceration_signs}
Recurrence risk: {recurrence_risk}
Domain: {domain}
Context: {context}

Has an intellectual creation died before or during delivery? Return ONLY valid JSON."""


class EpistemicStillbirthService:
    """Detects epistemic stillbirth — creation dead before achieving function."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        death_timing: str,
        *,
        cause_assessment: str = "",
        maceration_signs: str = "",
        recurrence_risk: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic stillbirth."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_STILLBIRTH_PROMPT.format(
                death_timing=death_timing,
                cause_assessment=cause_assessment or "Not specified",
                maceration_signs=maceration_signs or "Not specified",
                recurrence_risk=recurrence_risk or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_STILLBIRTH_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "death_timing": death_timing[:200],
            "stillbirth_detected": data.get("stillbirth_detected", False),
            "severity": data.get("severity", ""),
            "cause_assessment": data.get("cause_assessment", ""),
            "maceration_signs": data.get("maceration_signs", ""),
            "recurrence_risk": data.get("recurrence_risk", ""),
            "recommendation": data.get("recommendation", ""),
        }
