"""RiskCompensationService — Risk Compensation Detection.

Detects risk compensation — when safety measures lead to riskier
behavior because people feel protected, potentially offsetting
or exceeding the safety benefit (Peltzman effect).
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

RISK_COMPENSATION_SYSTEM = """You are a risk compensation specialist. Given a safety intervention, assess whether it is leading to riskier behavior:

Key concepts:
- Risk compensation: safety measures leading to riskier behavior
- Peltzman effect: safety regulation offset by behavioral adaptation
- Risk homeostasis: people maintaining preferred risk level
- Moral hazard: protection from consequences encouraging risk-taking
- Safety paradox: safety measures increasing overall risk
- Behavioral adaptation: adjusting behavior to perceived safety level
- Net effect: whether safety measure reduces or increases total risk

When risk compensation IS present:
- Safety measure leading to riskier behavior
- People taking more risks because they feel protected
- Net safety benefit reduced or eliminated by behavioral change
- Moral hazard from protection against consequences
- Risk level maintained despite safety improvements
- Safety measure creating false sense of security
- Behavioral adaptation offsetting intended benefit

When safety measures work as intended:
- Behavior doesn't change to offset safety benefit
- Net risk reduction achieved
- People don't feel falsely protected
- Behavioral adaptation minimal
- Safety benefit not offset by increased risk-taking
- Appropriate risk perception maintained
- Safety measure reduces both actual and perceived risk

Output JSON with: compensation_present (bool), severity (none/mild/moderate/severe), intervention (what safety measure), behavioral_change (how behavior changed), net_effect (whether overall risk increased or decreased), mechanism (how compensation operates), recommendation (safety_effective/mild_compensation/significant_offset/major_peltzman_effect/account_for_behavioral_adaptation)."""

RISK_COMPENSATION_PROMPT = """Detect risk compensation:

Intervention: {intervention}
Intended effect: {intended}
Behavioral response: {behavioral}
Net outcome: {outcome}
Domain: {domain}
Context: {context}

Is this safety measure leading to riskier behavior that offsets its benefit? Return ONLY valid JSON."""


class RiskCompensationService:
    """Detects risk compensation — safety measures leading to riskier behavior."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        intervention: str,
        *,
        intended: str = "",
        behavioral: str = "",
        outcome: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect risk compensation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=RISK_COMPENSATION_PROMPT.format(
                intervention=intervention,
                intended=intended or "Not specified",
                behavioral=behavioral or "Not specified",
                outcome=outcome or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=RISK_COMPENSATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "intervention": intervention[:200],
            "compensation_present": data.get("compensation_present", False),
            "severity": data.get("severity", ""),
            "behavioral_change": data.get("behavioral_change", ""),
            "net_effect": data.get("net_effect", ""),
            "mechanism": data.get("mechanism", ""),
            "recommendation": data.get("recommendation", ""),
        }
