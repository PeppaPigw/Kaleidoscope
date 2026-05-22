"""OstrichEffectService — Ostrich Effect Detection.

Detects ostrich effect — deliberately avoiding negative
information or feedback. Galai & Sade (2006). Named after
the myth that ostriches bury their heads in sand. People
avoid checking portfolio values during downturns, skip
medical tests, ignore warning signs. Avoidance feels
protective but prevents timely corrective action.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

OSTRICH_SYSTEM = """You are an ostrich effect specialist. Given a situation where information is being avoided, assess whether the avoidance is harmful:

Key concepts (Galai & Sade, 2006):
- Ostrich effect: deliberately avoiding negative information
- Information avoidance: choosing not to know
- Monitoring avoidance: not checking on things that might be bad
- Anticipatory dread: avoiding information to avoid anxiety
- Strategic ignorance: maintaining plausible deniability
- Head-in-sand: refusing to look at problems
- Feedback avoidance: not seeking performance information

When ostrich effect IS present:
- Not checking account balances during financial stress
- Avoiding medical tests for feared conditions
- Not reading performance reviews
- Ignoring warning indicators in projects
- "I don't want to know" about potential problems
- Avoiding conversations that might reveal bad news

When avoidance IS rational:
- The information genuinely cannot be acted upon
- Knowing would cause harm without enabling any response
- The emotional cost of knowing exceeds the decision value
- The information is unreliable and would cause unnecessary anxiety
- Timing: information will be more actionable later

Output JSON with: ostrich_effect_present (bool), severity (none/mild/moderate/severe), information_avoided (what information is being avoided), reason_for_avoidance (why is it being avoided), actionability (could the information be acted upon?), cost_of_not_knowing (what is lost by avoiding the information?), cost_of_knowing (what emotional/practical cost of knowing?), time_sensitivity (is delay making things worse?), pattern (bool — is this a pattern of avoidance?), recommendation (avoidance_rational/mild_ostrich/significant_avoidance/major_information_avoidance/face_the_information)."""

OSTRICH_PROMPT = """Detect ostrich effect:

Situation: {situation}
Information avoided: {avoided}
Reason: {reason}
Consequences: {consequences}
Domain: {domain}
Context: {context}

Is the person harmfully avoiding negative information? Return ONLY valid JSON."""


class OstrichEffectService:
    """Detects ostrich effect — deliberately avoiding negative information."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        avoided: str = "",
        reason: str = "",
        consequences: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect ostrich effect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=OSTRICH_PROMPT.format(
                situation=situation,
                avoided=avoided or "Not specified",
                reason=reason or "Not specified",
                consequences=consequences or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=OSTRICH_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "ostrich_effect_present": data.get("ostrich_effect_present", False),
            "severity": data.get("severity", ""),
            "information_avoided": data.get("information_avoided", ""),
            "reason_for_avoidance": data.get("reason_for_avoidance", ""),
            "actionability": data.get("actionability", ""),
            "cost_of_not_knowing": data.get("cost_of_not_knowing", ""),
            "cost_of_knowing": data.get("cost_of_knowing", ""),
            "time_sensitivity": data.get("time_sensitivity", ""),
            "pattern": data.get("pattern", False),
            "recommendation": data.get("recommendation", ""),
        }
