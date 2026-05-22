"""EpistemicCheckingCompulsionService — Epistemic Checking Compulsion Detection.

Detects epistemic checking compulsion — compulsive need to verify and recheck
intellectual work beyond what is reasonable or productive.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_CHECKING_COMPULSION_SYSTEM = """You are an epistemic checking compulsion specialist. Given compulsive verification, assess checking:

Key concepts:
- Epistemic checking compulsion: compulsive need to verify
- Doubt persistence: checking doesn't resolve doubt
- Reassurance seeking: needing others to confirm correctness
- Infinite regress: checking the checking
- Time consumption: excessive time spent verifying
- Certainty impossibility: never feeling sure enough
- Functional impairment: checking prevents progress

When epistemic checking compulsion IS present:
- Compulsive need to verify
- Checking doesn't resolve doubt
- Needing others to confirm
- Checking the checking
- Excessive time verifying
- Never sure enough
- Checking prevents progress

When no checking compulsion:
- Appropriate verification
- Doubt resolved by checking
- Self-confident assessment
- Single verification sufficient
- Reasonable time spent
- Comfortable with certainty level
- Verification enables progress

Output JSON with: checking_compulsion_detected (bool), severity (none/mild/moderate/severe), doubt_persistence (what not resolving), reassurance_seeking (what needing confirmed), infinite_regress (what rechecking), functional_impairment (what preventing), recommendation (no_checking_compulsion/mild_tolerance_building/significant_exposure_response/major_intensive_ocd_treatment/emergency_severe_compulsion)."""

EPISTEMIC_CHECKING_COMPULSION_PROMPT = """Detect epistemic checking compulsion:

Doubt persistence: {doubt_persistence}
Reassurance seeking: {reassurance_seeking}
Infinite regress: {infinite_regress}
Functional impairment: {functional_impairment}
Domain: {domain}
Context: {context}

Is there compulsive need to verify intellectual work beyond what is productive? Return ONLY valid JSON."""


class EpistemicCheckingCompulsionService:
    """Detects epistemic checking compulsion — compulsive verification need."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        doubt_persistence: str,
        *,
        reassurance_seeking: str = "",
        infinite_regress: str = "",
        functional_impairment: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic checking compulsion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_CHECKING_COMPULSION_PROMPT.format(
                doubt_persistence=doubt_persistence,
                reassurance_seeking=reassurance_seeking or "Not specified",
                infinite_regress=infinite_regress or "Not specified",
                functional_impairment=functional_impairment or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_CHECKING_COMPULSION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "doubt_persistence": doubt_persistence[:200],
            "checking_compulsion_detected": data.get("checking_compulsion_detected", False),
            "severity": data.get("severity", ""),
            "reassurance_seeking": data.get("reassurance_seeking", ""),
            "infinite_regress": data.get("infinite_regress", ""),
            "functional_impairment": data.get("functional_impairment", ""),
            "recommendation": data.get("recommendation", ""),
        }
