"""EpistemicIdentificationAggressorService — Epistemic Identification with Aggressor Detection.

Detects identification with the epistemic aggressor — adopting the intellectual
stance of one who has caused epistemic harm as a defense mechanism.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_IDENTIFICATION_AGGRESSOR_SYSTEM = """You are an epistemic identification-with-aggressor specialist. Given adoption of aggressor's stance, assess identification:

Key concepts:
- Identification with aggressor: adopting harmful authority's stance
- Stockholm syndrome: bonding with epistemic oppressor
- Internalized oppression: enforcing own intellectual suppression
- Role reversal: victim becomes perpetrator of same harm
- Survival adaptation: adopting aggressor stance for safety
- Self-policing: enforcing aggressor's rules on self
- Perpetuation cycle: passing on epistemic harm to others

When identification with aggressor IS present:
- Adopting harmful authority's stance
- Bonding with oppressor
- Enforcing own suppression
- Victim becoming perpetrator
- Adopting stance for safety
- Enforcing aggressor's rules on self
- Passing harm to others

When no identification with aggressor:
- Maintaining own stance
- Appropriate boundaries with authority
- Self-advocacy
- Clear victim/perpetrator distinction
- Authentic safety strategies
- Self-determined rules
- Breaking cycles

Output JSON with: identification_detected (bool), severity (none/mild/moderate/severe), aggressor_stance (what adopted), internalized_oppression (what enforcing), role_reversal (what perpetuating), survival_adaptation (what safety strategy), recommendation (no_identification/mild_awareness_building/significant_stance_recovery/major_intensive_liberation/emergency_complete_identification)."""

EPISTEMIC_IDENTIFICATION_AGGRESSOR_PROMPT = """Detect epistemic identification with aggressor:

Aggressor stance: {aggressor_stance}
Internalized oppression: {internalized_oppression}
Role reversal: {role_reversal}
Survival adaptation: {survival_adaptation}
Domain: {domain}
Context: {context}

Is there adoption of the epistemic aggressor's intellectual stance as defense? Return ONLY valid JSON."""


class EpistemicIdentificationAggressorService:
    """Detects identification with epistemic aggressor — adopting harmful authority's stance."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        aggressor_stance: str,
        *,
        internalized_oppression: str = "",
        role_reversal: str = "",
        survival_adaptation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic identification with aggressor."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_IDENTIFICATION_AGGRESSOR_PROMPT.format(
                aggressor_stance=aggressor_stance,
                internalized_oppression=internalized_oppression or "Not specified",
                role_reversal=role_reversal or "Not specified",
                survival_adaptation=survival_adaptation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_IDENTIFICATION_AGGRESSOR_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "aggressor_stance": aggressor_stance[:200],
            "identification_detected": data.get("identification_detected", False),
            "severity": data.get("severity", ""),
            "internalized_oppression": data.get("internalized_oppression", ""),
            "role_reversal": data.get("role_reversal", ""),
            "survival_adaptation": data.get("survival_adaptation", ""),
            "recommendation": data.get("recommendation", ""),
        }
