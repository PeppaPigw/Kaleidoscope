"""EpistemicIdentityForeclosureService — Epistemic Identity Foreclosure Detection.

Detects epistemic identity foreclosure — prematurely closing intellectual
identity without genuine exploration.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_IDENTITY_FORECLOSURE_SYSTEM = """You are an epistemic identity foreclosure specialist. Given prematurely closing intellectual identity, assess identity foreclosure:

Key concepts:
- Epistemic identity foreclosure: prematurely closing without exploration
- Premature commitment: committing to positions without exploring alternatives
- Exploration avoidance: avoiding intellectual exploration that might change identity
- Inherited identity: adopting intellectual identity from others without questioning
- Comfort closure: closing identity to avoid discomfort of uncertainty
- Growth refusal: refusing to grow because it would change identity
- Fixed self-concept: rigid intellectual self-concept resistant to change

When epistemic identity foreclosure IS present:
- Prematurely closing without exploration
- Committing without exploring alternatives
- Avoiding exploration that might change
- Adopting from others without questioning
- Closing to avoid discomfort
- Refusing growth that changes identity
- Rigid self-concept resistant to change

When no identity foreclosure:
- Open exploration
- Exploring before committing
- Welcoming identity-changing exploration
- Questioning inherited positions
- Comfortable with uncertainty
- Embracing growth
- Flexible self-concept

Output JSON with: identity_foreclosure_detected (bool), severity (none/mild/moderate/severe), premature_commitment (what committing without exploring), exploration_avoidance (what avoiding exploring), inherited_identity (what adopting without questioning), growth_refusal (what refusing to grow about), recommendation (no_identity_foreclosure/mild_exploration_practice/significant_openness_building/major_intensive_identity_reopening/emergency_complete_foreclosure)."""

EPISTEMIC_IDENTITY_FORECLOSURE_PROMPT = """Detect epistemic identity foreclosure:

Premature commitment: {premature_commitment}
Exploration avoidance: {exploration_avoidance}
Inherited identity: {inherited_identity}
Growth refusal: {growth_refusal}
Domain: {domain}
Context: {context}

Is there prematurely closing intellectual identity without genuine exploration? Return ONLY valid JSON."""


class EpistemicIdentityForeclosureService:
    """Detects epistemic identity foreclosure — prematurely closing without exploration."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        premature_commitment: str,
        *,
        exploration_avoidance: str = "",
        inherited_identity: str = "",
        growth_refusal: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic identity foreclosure."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_IDENTITY_FORECLOSURE_PROMPT.format(
                premature_commitment=premature_commitment,
                exploration_avoidance=exploration_avoidance or "Not specified",
                inherited_identity=inherited_identity or "Not specified",
                growth_refusal=growth_refusal or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_IDENTITY_FORECLOSURE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "premature_commitment": premature_commitment[:200],
            "identity_foreclosure_detected": data.get("identity_foreclosure_detected", False),
            "severity": data.get("severity", ""),
            "exploration_avoidance": data.get("exploration_avoidance", ""),
            "inherited_identity": data.get("inherited_identity", ""),
            "growth_refusal": data.get("growth_refusal", ""),
            "recommendation": data.get("recommendation", ""),
        }
