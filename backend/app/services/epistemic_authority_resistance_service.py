"""EpistemicAuthorityResistanceService — Epistemic Authority Resistance Detection.

Detects epistemic authority resistance — reflexive resistance to
intellectual authority regardless of merit.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_AUTHORITY_RESISTANCE_SYSTEM = """You are an epistemic authority resistance specialist. Given reflexive resistance to authority, assess authority resistance:

Key concepts:
- Epistemic authority resistance: reflexive resistance to intellectual authority
- Contrarian reflex: opposing authority positions automatically
- Anti-establishment bias: rejecting ideas from established sources
- Expertise rejection: dismissing expert opinion on principle
- Rebellion pattern: intellectual rebellion as identity
- Oppositional thinking: defining self against authority
- Autonomy overreach: independence becoming rigidity

When epistemic authority resistance IS present:
- Reflexive resistance to authority
- Opposing automatically
- Rejecting established sources
- Dismissing expert opinion
- Rebellion as identity
- Defining self against authority
- Independence becoming rigidity

When no authority resistance:
- Evaluating authority on merit
- Considering all positions
- Engaging established sources
- Weighing expert opinion
- Independent without rebellion
- Self-defined positively
- Flexible independence

Output JSON with: authority_resistance_detected (bool), severity (none/mild/moderate/severe), contrarian_reflex (what opposing automatically), anti_establishment_bias (what rejecting from establishment), expertise_rejection (what dismissing), rebellion_pattern (what rebelling against), recommendation (no_authority_resistance/mild_openness_practice/significant_flexibility_building/major_intensive_authority_processing/emergency_rigid_opposition)."""

EPISTEMIC_AUTHORITY_RESISTANCE_PROMPT = """Detect epistemic authority resistance:

Contrarian reflex: {contrarian_reflex}
Anti establishment bias: {anti_establishment_bias}
Expertise rejection: {expertise_rejection}
Rebellion pattern: {rebellion_pattern}
Domain: {domain}
Context: {context}

Is there reflexive resistance to intellectual authority? Return ONLY valid JSON."""


class EpistemicAuthorityResistanceService:
    """Detects epistemic authority resistance — reflexive resistance to authority."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        contrarian_reflex: str,
        *,
        anti_establishment_bias: str = "",
        expertise_rejection: str = "",
        rebellion_pattern: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic authority resistance."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_AUTHORITY_RESISTANCE_PROMPT.format(
                contrarian_reflex=contrarian_reflex,
                anti_establishment_bias=anti_establishment_bias or "Not specified",
                expertise_rejection=expertise_rejection or "Not specified",
                rebellion_pattern=rebellion_pattern or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_AUTHORITY_RESISTANCE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "contrarian_reflex": contrarian_reflex[:200],
            "authority_resistance_detected": data.get("authority_resistance_detected", False),
            "severity": data.get("severity", ""),
            "anti_establishment_bias": data.get("anti_establishment_bias", ""),
            "expertise_rejection": data.get("expertise_rejection", ""),
            "rebellion_pattern": data.get("rebellion_pattern", ""),
            "recommendation": data.get("recommendation", ""),
        }
