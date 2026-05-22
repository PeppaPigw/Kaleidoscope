"""EpistemicOrganDonationService — Epistemic Organ Donation Detection.

Detects epistemic organ donation opportunity — salvaging useful intellectual
components from a dying system to benefit other systems.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ORGAN_DONATION_SYSTEM = """You are an epistemic organ donation specialist. Given dying intellectual systems, assess organ donation opportunity:

Key concepts:
- Epistemic organ donation: salvaging components from dying systems
- Viable organs: intellectual components still functional
- Compatibility: matching donor components to recipients
- Preservation: maintaining viability during transfer
- Rejection risk: recipient system rejecting new component
- Living donation: sharing components without dying
- Allocation ethics: fair distribution of scarce components

When epistemic organ donation IS appropriate:
- System dying but components viable
- Functional intellectual parts salvageable
- Compatible recipients identified
- Preservation methods available
- Manageable rejection risk
- Sharing possible without total loss
- Fair allocation achievable

When no organ donation appropriate:
- System still viable as whole
- No salvageable components
- No compatible recipients
- Cannot preserve during transfer
- Unacceptable rejection risk
- Sharing would destroy donor
- No fair allocation possible

Output JSON with: donation_appropriate (bool), severity (none/mild/moderate/severe), viable_organs (what salvageable), compatibility (what matching), preservation_method (what maintenance), rejection_risk (what acceptance challenge), recommendation (no_donation_needed/mild_sharing/significant_harvest/major_multi_organ/emergency_rapid_harvest)."""

EPISTEMIC_ORGAN_DONATION_PROMPT = """Detect epistemic organ donation opportunity:

Viable organs: {viable_organs}
Compatibility: {compatibility}
Preservation method: {preservation_method}
Rejection risk: {rejection_risk}
Domain: {domain}
Context: {context}

Are there salvageable intellectual components from a dying system? Return ONLY valid JSON."""


class EpistemicOrganDonationService:
    """Detects epistemic organ donation opportunity — salvaging from dying systems."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        viable_organs: str,
        *,
        compatibility: str = "",
        preservation_method: str = "",
        rejection_risk: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic organ donation opportunity."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ORGAN_DONATION_PROMPT.format(
                viable_organs=viable_organs,
                compatibility=compatibility or "Not specified",
                preservation_method=preservation_method or "Not specified",
                rejection_risk=rejection_risk or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ORGAN_DONATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "viable_organs": viable_organs[:200],
            "donation_appropriate": data.get("donation_appropriate", False),
            "severity": data.get("severity", ""),
            "compatibility": data.get("compatibility", ""),
            "preservation_method": data.get("preservation_method", ""),
            "rejection_risk": data.get("rejection_risk", ""),
            "recommendation": data.get("recommendation", ""),
        }
