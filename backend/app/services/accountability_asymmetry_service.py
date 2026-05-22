"""AccountabilityAsymmetryService — Accountability Asymmetry Detection.

Detects accountability asymmetry — asymmetric accountability for
epistemic failures based on status, where high-status actors face
less consequence for being wrong.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

ACCOUNTABILITY_ASYMMETRY_SYSTEM = """You are an accountability asymmetry specialist. Given an epistemic accountability situation, assess whether accountability is asymmetrically distributed:

Key concepts:
- Accountability asymmetry: unequal consequences for being wrong
- Status-based immunity: high-status actors facing less consequence
- Failure consequence asymmetry: same failure different consequences
- Epistemic privilege: some can be wrong without cost
- Accountability gradient: accountability inversely proportional to status
- Consequence asymmetry: different penalties for same epistemic failure
- Power-accountability inversion: more power less accountability

When accountability asymmetry IS present:
- Same epistemic failure different consequences based on status
- High-status actors facing less accountability for being wrong
- Power inversely related to epistemic accountability
- Consequences for epistemic failure status-dependent
- Some actors can be wrong without cost
- Accountability gradient favoring the powerful
- Epistemic failures excused based on who made them

When differential accountability is appropriate:
- Accountability proportionate to authority and role
- Consequences proportionate to impact of failure
- Status carrying more not less accountability
- Power increasing rather than decreasing accountability
- Consequences based on failure severity not actor status
- Accountability serving learning not punishment
- Standards applied based on role not identity

Output JSON with: asymmetry_present (bool), severity (none/mild/moderate/severe), situation (what situation exists), high_status_treatment (how high-status actors are treated), low_status_treatment (how low-status actors are treated), basis (what drives the asymmetry), recommendation (proportionate_accountability/mild_status_preference/significant_accountability_asymmetry/major_power_immunity/accountability_proportionate_to_authority)."""

ACCOUNTABILITY_ASYMMETRY_PROMPT = """Detect accountability asymmetry:

Situation: {situation}
High-status treatment: {high_status}
Low-status treatment: {low_status}
Failure type: {failure}
Domain: {domain}
Context: {context}

Is accountability for epistemic failures asymmetrically distributed based on status? Return ONLY valid JSON."""


class AccountabilityAsymmetryService:
    """Detects accountability asymmetry — unequal consequences for epistemic failures."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        high_status: str = "",
        low_status: str = "",
        failure: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect accountability asymmetry."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=ACCOUNTABILITY_ASYMMETRY_PROMPT.format(
                situation=situation,
                high_status=high_status or "Not specified",
                low_status=low_status or "Not specified",
                failure=failure or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=ACCOUNTABILITY_ASYMMETRY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "asymmetry_present": data.get("asymmetry_present", False),
            "severity": data.get("severity", ""),
            "high_status_treatment": data.get("high_status_treatment", ""),
            "low_status_treatment": data.get("low_status_treatment", ""),
            "basis": data.get("basis", ""),
            "recommendation": data.get("recommendation", ""),
        }
