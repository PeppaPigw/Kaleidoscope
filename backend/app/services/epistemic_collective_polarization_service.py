"""EpistemicCollectivePolarizationService — Epistemic Collective Polarization Detection.

Detects epistemic collective polarization — group discussion pushing
positions toward more extreme conclusions.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_COLLECTIVE_POLARIZATION_SYSTEM = """You are an epistemic collective polarization specialist. Given group deliberation, assess whether group polarization is pushing positions to extremes:

Key concepts:
- Epistemic group polarization: collective discussion extremifying positions
- Position extremification: beliefs shift toward more extreme versions
- Risky shift: group accepts more risk than members would alone
- Echo amplification: repeated agreement intensifies confidence
- Moderate voice loss: balancing perspectives disappear
- Argument pool skew: mostly one-sided arguments circulate
- Identity escalation: stronger positions signal group belonging

When epistemic polarization IS present:
- Positions become more extreme after group interaction
- Risk tolerance increases collectively
- Echoes amplify confidence
- Moderate voices are lost or sidelined
- One-sided argument pools dominate
- Identity rewards extremity
- Nuance collapses into factional certainty

When no polarization:
- Positions calibrate toward evidence
- Risk assessed independently
- Agreement does not inflate confidence
- Moderate voices remain influential
- Competing arguments circulate
- Identity does not require extremity
- Nuance preserved

Output JSON with: polarization_detected (bool), severity (none/mild/moderate/severe), risky_shift (what risk shift appears), echo_amplification (what agreement amplifies), moderate_voice_loss (what moderating input is lost), recommendation (no_polarization/mild_moderation_check/significant_counterargument_review/major_deliberation_redesign/emergency_depolarization_intervention)."""

EPISTEMIC_COLLECTIVE_POLARIZATION_PROMPT = """Detect epistemic collective polarization:

Position extremification: {position_extremification}
Risky shift: {risky_shift}
Echo amplification: {echo_amplification}
Moderate voice loss: {moderate_voice_loss}
Domain: {domain}
Context: {context}

Is group interaction pushing positions toward extremes? Return ONLY valid JSON."""


class EpistemicCollectivePolarizationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        position_extremification: str,
        *,
        risky_shift: str = "",
        echo_amplification: str = "",
        moderate_voice_loss: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_COLLECTIVE_POLARIZATION_PROMPT.format(
                position_extremification=position_extremification,
                risky_shift=risky_shift or "Not specified",
                echo_amplification=echo_amplification or "Not specified",
                moderate_voice_loss=moderate_voice_loss or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_COLLECTIVE_POLARIZATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "position_extremification": position_extremification[:200],
            "polarization_detected": data.get("polarization_detected", False),
            "severity": data.get("severity", ""),
            "risky_shift": data.get("risky_shift", ""),
            "echo_amplification": data.get("echo_amplification", ""),
            "moderate_voice_loss": data.get("moderate_voice_loss", ""),
            "recommendation": data.get("recommendation", ""),
        }
