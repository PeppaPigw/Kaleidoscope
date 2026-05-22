"""EpistemicPrematureOptimismService — Epistemic Premature Optimism Detection.

Detects epistemic premature optimism — optimism that arrives before
evidence warrants it, distorting assessment.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PREMATURE_OPTIMISM_SYSTEM = """You are an epistemic premature optimism specialist. Given optimism before evidence warrants, assess premature optimism:

Key concepts:
- Epistemic premature optimism: optimism before evidence warrants
- Early celebration: declaring success before confirmation
- Insufficient evidence optimism: positive conclusions from thin data
- Confirmation rush: rushing to confirm desired hypothesis
- Victory declaration: claiming victory before battle won
- Premature closure: closing inquiry because early signs positive
- Enthusiasm bias: enthusiasm overriding careful assessment

When epistemic premature optimism IS present:
- Optimism before evidence warrants
- Declaring success early
- Positive from thin data
- Rushing to confirm
- Claiming victory early
- Closing inquiry prematurely
- Enthusiasm overriding assessment

When no premature optimism:
- Optimism calibrated to evidence
- Waiting for confirmation
- Conclusions from sufficient data
- Patient hypothesis testing
- Victory after confirmation
- Inquiry until complete
- Enthusiasm alongside rigor

Output JSON with: premature_optimism_detected (bool), severity (none/mild/moderate/severe), early_celebration (what declaring success about), insufficient_evidence_optimism (what concluding from thin data), confirmation_rush (what rushing to confirm), premature_closure (what closing inquiry about), recommendation (no_premature_optimism/mild_patience_practice/significant_evidence_discipline/major_intensive_optimism_calibration/emergency_severe_reality_disconnect)."""

EPISTEMIC_PREMATURE_OPTIMISM_PROMPT = """Detect epistemic premature optimism:

Early celebration: {early_celebration}
Insufficient evidence optimism: {insufficient_evidence_optimism}
Confirmation rush: {confirmation_rush}
Premature closure: {premature_closure}
Domain: {domain}
Context: {context}

Is there optimism before evidence warrants it? Return ONLY valid JSON."""


class EpistemicPrematureOptimismService:
    """Detects epistemic premature optimism — optimism before evidence warrants."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        early_celebration: str,
        *,
        insufficient_evidence_optimism: str = "",
        confirmation_rush: str = "",
        premature_closure: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic premature optimism."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PREMATURE_OPTIMISM_PROMPT.format(
                early_celebration=early_celebration,
                insufficient_evidence_optimism=insufficient_evidence_optimism or "Not specified",
                confirmation_rush=confirmation_rush or "Not specified",
                premature_closure=premature_closure or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PREMATURE_OPTIMISM_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "early_celebration": early_celebration[:200],
            "premature_optimism_detected": data.get("premature_optimism_detected", False),
            "severity": data.get("severity", ""),
            "insufficient_evidence_optimism": data.get("insufficient_evidence_optimism", ""),
            "confirmation_rush": data.get("confirmation_rush", ""),
            "premature_closure": data.get("premature_closure", ""),
            "recommendation": data.get("recommendation", ""),
        }
