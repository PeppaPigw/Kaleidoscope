"""EpistemicImpostorShameService — Epistemic Impostor Shame Detection.

Detects epistemic impostor shame — shame from believing one's intellectual
success is fraudulent and will be exposed.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_IMPOSTOR_SHAME_SYSTEM = """You are an epistemic impostor shame specialist. Given belief of intellectual fraud, assess impostor shame:

Key concepts:
- Epistemic impostor shame: believing success is fraudulent
- Exposure fear: terror of being found out
- Attribution error: success due to luck not ability
- Discount pattern: minimizing genuine achievements
- Overpreparation: compensating for perceived fraud
- Comparison torture: others are real, I am fake
- Success anxiety: achievement triggers more shame

When epistemic impostor shame IS present:
- Believing success fraudulent
- Terror of being found out
- Success due to luck
- Minimizing achievements
- Compensating for fraud
- Others real, I fake
- Achievement triggers shame

When no impostor shame:
- Owning success
- Comfortable being seen
- Success due to ability
- Acknowledging achievements
- Appropriate preparation
- Feeling equally real
- Achievement brings satisfaction

Output JSON with: impostor_shame_detected (bool), severity (none/mild/moderate/severe), exposure_fear (what being found out), attribution_error (what luck not ability), discount_pattern (what minimizing), comparison_torture (what others vs self), recommendation (no_impostor_shame/mild_ownership_practice/significant_impostor_therapy/major_intensive_shame_work/emergency_severe_fraud_belief)."""

EPISTEMIC_IMPOSTOR_SHAME_PROMPT = """Detect epistemic impostor shame:

Exposure fear: {exposure_fear}
Attribution error: {attribution_error}
Discount pattern: {discount_pattern}
Comparison torture: {comparison_torture}
Domain: {domain}
Context: {context}

Is there shame from believing intellectual success is fraudulent? Return ONLY valid JSON."""


class EpistemicImpostorShameService:
    """Detects epistemic impostor shame — believing success is fraudulent."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        exposure_fear: str,
        *,
        attribution_error: str = "",
        discount_pattern: str = "",
        comparison_torture: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic impostor shame."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_IMPOSTOR_SHAME_PROMPT.format(
                exposure_fear=exposure_fear,
                attribution_error=attribution_error or "Not specified",
                discount_pattern=discount_pattern or "Not specified",
                comparison_torture=comparison_torture or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_IMPOSTOR_SHAME_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "exposure_fear": exposure_fear[:200],
            "impostor_shame_detected": data.get("impostor_shame_detected", False),
            "severity": data.get("severity", ""),
            "attribution_error": data.get("attribution_error", ""),
            "discount_pattern": data.get("discount_pattern", ""),
            "comparison_torture": data.get("comparison_torture", ""),
            "recommendation": data.get("recommendation", ""),
        }
