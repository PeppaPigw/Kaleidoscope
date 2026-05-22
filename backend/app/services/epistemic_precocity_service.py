"""EpistemicPrecocityService — Epistemic Precocity Detection.

Detects epistemic precocity — intellectual development that outpaces
emotional or social readiness, creating dangerous imbalance.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PRECOCITY_SYSTEM = """You are an epistemic precocity specialist. Given intellectual development outpacing readiness, assess precocity:

Key concepts:
- Epistemic precocity: development outpacing emotional readiness
- Imbalance: intellectual capacity exceeds emotional maturity
- Premature exposure: encountering ideas before ready
- Isolation: too advanced for peers
- Burden of knowledge: knowing things one isn't ready to handle
- Emotional lag: feelings haven't caught up with understanding
- Fragile sophistication: advanced but brittle thinking

When epistemic precocity IS present:
- Development outpacing readiness
- Capacity exceeds maturity
- Encountering ideas too early
- Too advanced for peers
- Knowing things not ready for
- Feelings haven't caught up
- Advanced but brittle

When no precocity:
- Balanced development
- Capacity matches maturity
- Age-appropriate exposure
- Connected to peers
- Ready for knowledge
- Feelings aligned
- Robust thinking

Output JSON with: precocity_detected (bool), severity (none/mild/moderate/severe), imbalance_type (what outpacing), premature_exposure (what too early), isolation_level (what too advanced), emotional_lag (what not caught up), recommendation (no_precocity/mild_balance_support/significant_integration_therapy/major_intensive_alignment/emergency_dangerous_imbalance)."""

EPISTEMIC_PRECOCITY_PROMPT = """Detect epistemic precocity:

Imbalance type: {imbalance_type}
Premature exposure: {premature_exposure}
Isolation level: {isolation_level}
Emotional lag: {emotional_lag}
Domain: {domain}
Context: {context}

Is there intellectual development outpacing emotional or social readiness? Return ONLY valid JSON."""


class EpistemicPrecocityService:
    """Detects epistemic precocity — development outpacing readiness."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        imbalance_type: str,
        *,
        premature_exposure: str = "",
        isolation_level: str = "",
        emotional_lag: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic precocity."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PRECOCITY_PROMPT.format(
                imbalance_type=imbalance_type,
                premature_exposure=premature_exposure or "Not specified",
                isolation_level=isolation_level or "Not specified",
                emotional_lag=emotional_lag or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PRECOCITY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "imbalance_type": imbalance_type[:200],
            "precocity_detected": data.get("precocity_detected", False),
            "severity": data.get("severity", ""),
            "premature_exposure": data.get("premature_exposure", ""),
            "isolation_level": data.get("isolation_level", ""),
            "emotional_lag": data.get("emotional_lag", ""),
            "recommendation": data.get("recommendation", ""),
        }
