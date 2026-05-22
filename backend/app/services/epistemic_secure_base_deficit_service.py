"""EpistemicSecureBaseDeficitService — Epistemic Secure Base Deficit Detection.

Detects epistemic secure base deficit — lacking a secure base from which
to explore intellectually, resulting in constrained or fearful exploration.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SECURE_BASE_DEFICIT_SYSTEM = """You are an epistemic secure base deficit specialist. Given lack of secure intellectual base, assess deficit:

Key concepts:
- Epistemic secure base deficit: no safe base for exploration
- Exploration inhibition: can't venture intellectually without safety
- Return anxiety: fear of not being able to return to safety
- Support absence: no one to turn to when intellectually lost
- Risk aversion: avoiding intellectual risk due to no safety net
- Containment failure: no one to hold intellectual distress
- Confidence deficit: lacking confidence to explore alone

When epistemic secure base deficit IS present:
- No safe base for exploration
- Can't venture without safety
- Fear of not returning
- No one to turn to
- Avoiding risk without net
- No one to hold distress
- Lacking confidence to explore

When no secure base deficit:
- Safe base available
- Free to venture
- Confident in return
- Support available
- Comfortable with risk
- Distress contained
- Confident explorer

Output JSON with: secure_base_deficit_detected (bool), severity (none/mild/moderate/severe), exploration_inhibition (what can't venture), support_absence (what no one for), risk_aversion (what avoiding), containment_failure (what not held), recommendation (no_secure_base_deficit/mild_base_building/significant_secure_base_therapy/major_intensive_attachment_work/emergency_severe_deficit)."""

EPISTEMIC_SECURE_BASE_DEFICIT_PROMPT = """Detect epistemic secure base deficit:

Exploration inhibition: {exploration_inhibition}
Support absence: {support_absence}
Risk aversion: {risk_aversion}
Containment failure: {containment_failure}
Domain: {domain}
Context: {context}

Is there lack of secure base for intellectual exploration? Return ONLY valid JSON."""


class EpistemicSecureBaseDeficitService:
    """Detects epistemic secure base deficit — no safe base for exploration."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        exploration_inhibition: str,
        *,
        support_absence: str = "",
        risk_aversion: str = "",
        containment_failure: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic secure base deficit."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SECURE_BASE_DEFICIT_PROMPT.format(
                exploration_inhibition=exploration_inhibition,
                support_absence=support_absence or "Not specified",
                risk_aversion=risk_aversion or "Not specified",
                containment_failure=containment_failure or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SECURE_BASE_DEFICIT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "exploration_inhibition": exploration_inhibition[:200],
            "secure_base_deficit_detected": data.get("secure_base_deficit_detected", False),
            "severity": data.get("severity", ""),
            "support_absence": data.get("support_absence", ""),
            "risk_aversion": data.get("risk_aversion", ""),
            "containment_failure": data.get("containment_failure", ""),
            "recommendation": data.get("recommendation", ""),
        }
