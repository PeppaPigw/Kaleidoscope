"""EpistemicShameShieldService — Epistemic Shame Shield Detection.

Detects epistemic shame shields — defensive strategies deployed to avoid
exposure of intellectual shame or inadequacy.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SHAME_SHIELD_SYSTEM = """You are an epistemic shame shield specialist. Given defensive strategies against shame exposure, assess shielding:

Key concepts:
- Epistemic shame shield: defense against shame exposure
- Perfectionism shield: if perfect, shame can't touch
- Withdrawal shield: if not seen, shame can't be triggered
- Aggression shield: attacking before being shamed
- Humor shield: deflecting with jokes before shame lands
- Intellectualization shield: analyzing shame away
- Grandiosity shield: superiority covering shame

When epistemic shame shield IS present:
- Defense against exposure
- Perfectionism protecting
- Withdrawal hiding
- Attacking preemptively
- Deflecting with humor
- Analyzing away
- Superiority covering

When no shame shield:
- Comfortable with vulnerability
- Good enough accepted
- Visible and present
- Non-defensive engagement
- Direct expression
- Feeling through
- Authentic self-presentation

Output JSON with: shame_shield_detected (bool), severity (none/mild/moderate/severe), shield_type (what defense using), underlying_shame (what protecting from), rigidity_level (what can't drop), cost_pattern (what losing by shielding), recommendation (no_shame_shield/mild_vulnerability_practice/significant_shield_softening/major_intensive_shame_work/emergency_rigid_armoring)."""

EPISTEMIC_SHAME_SHIELD_PROMPT = """Detect epistemic shame shield:

Shield type: {shield_type}
Underlying shame: {underlying_shame}
Rigidity level: {rigidity_level}
Cost pattern: {cost_pattern}
Domain: {domain}
Context: {context}

Are there defensive strategies to avoid intellectual shame exposure? Return ONLY valid JSON."""


class EpistemicShameShieldService:
    """Detects epistemic shame shields — defenses against shame exposure."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        shield_type: str,
        *,
        underlying_shame: str = "",
        rigidity_level: str = "",
        cost_pattern: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic shame shield."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SHAME_SHIELD_PROMPT.format(
                shield_type=shield_type,
                underlying_shame=underlying_shame or "Not specified",
                rigidity_level=rigidity_level or "Not specified",
                cost_pattern=cost_pattern or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SHAME_SHIELD_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "shield_type": shield_type[:200],
            "shame_shield_detected": data.get("shame_shield_detected", False),
            "severity": data.get("severity", ""),
            "underlying_shame": data.get("underlying_shame", ""),
            "rigidity_level": data.get("rigidity_level", ""),
            "cost_pattern": data.get("cost_pattern", ""),
            "recommendation": data.get("recommendation", ""),
        }
