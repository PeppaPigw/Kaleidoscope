"""EpistemicSocialSignalingService — Epistemic Social Signaling Detection.

Detects epistemic social signaling — beliefs held for social signaling
rather than truth, using beliefs as identity markers.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SOCIAL_SIGNALING_SYSTEM = """You are an epistemic social signaling specialist. Given beliefs held for signaling rather than truth, assess social signaling:

Key concepts:
- Epistemic social signaling: beliefs held for social signaling rather than truth
- Virtue signaling: beliefs held to signal virtue
- Intelligence signaling: beliefs held to signal intelligence
- Group membership signaling: beliefs held to signal group membership
- Status signaling: beliefs held to signal status
- Contrarian signaling: beliefs held to signal independence
- Sophistication signaling: beliefs held to signal sophistication

When epistemic social signaling IS present:
- Beliefs held for signaling
- Virtue being signaled
- Intelligence being signaled
- Group membership signaled
- Status signaled
- Contrarianism signaled
- Sophistication signaled

When no social signaling:
- Beliefs held for truth
- Virtue not signaled
- Intelligence not performed
- Group membership not signaled
- Status not signaled
- Positions held genuinely
- Sophistication not performed

Output JSON with: social_signaling_detected (bool), severity (none/mild/moderate/severe), virtue_signaling (what beliefs signal virtue), intelligence_signaling (what beliefs signal intelligence), group_membership_signaling (what beliefs signal membership), status_signaling (what beliefs signal status), recommendation (no_social_signaling/mild_authenticity_practice/significant_truth_commitment/major_intensive_sincerity_recovery/emergency_complete_social_signaling)."""

EPISTEMIC_SOCIAL_SIGNALING_PROMPT = """Detect epistemic social signaling:

Virtue signaling: {virtue_signaling}
Intelligence signaling: {intelligence_signaling}
Group membership signaling: {group_membership_signaling}
Status signaling: {status_signaling}
Domain: {domain}
Context: {context}

Are beliefs held for social signaling rather than truth? Return ONLY valid JSON."""


class EpistemicSocialSignalingService:
    """Detects epistemic social signaling — beliefs held for signaling not truth."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        virtue_signaling: str,
        *,
        intelligence_signaling: str = "",
        group_membership_signaling: str = "",
        status_signaling: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic social signaling."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SOCIAL_SIGNALING_PROMPT.format(
                virtue_signaling=virtue_signaling,
                intelligence_signaling=intelligence_signaling or "Not specified",
                group_membership_signaling=group_membership_signaling or "Not specified",
                status_signaling=status_signaling or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SOCIAL_SIGNALING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "virtue_signaling": virtue_signaling[:200],
            "social_signaling_detected": data.get("social_signaling_detected", False),
            "severity": data.get("severity", ""),
            "intelligence_signaling": data.get("intelligence_signaling", ""),
            "group_membership_signaling": data.get("group_membership_signaling", ""),
            "status_signaling": data.get("status_signaling", ""),
            "recommendation": data.get("recommendation", ""),
        }
