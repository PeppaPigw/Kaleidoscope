"""SelfServingInterpretationService — Self-Serving Interpretation Detection.

Detects self-serving interpretation — interpreting ambiguous evidence
in ways that consistently serve one's interests, where interpretation
tracks advantage rather than truth.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

SELF_SERVING_INTERPRETATION_SYSTEM = """You are a self-serving interpretation specialist. Given an interpretation, assess whether ambiguity is being resolved in self-serving ways:

Key concepts:
- Self-serving interpretation: ambiguity resolved for advantage
- Convenient reading: choosing interpretation that serves interests
- Asymmetric interpretation: favorable for self, unfavorable for others
- Interest-tracking hermeneutics: interpretation follows interest
- Selective ambiguity resolution: ambiguity resolved when convenient
- Benefit of doubt asymmetry: generous to self, strict to others
- Motivated interpretation: desire shaping how evidence is read

When self-serving interpretation IS present:
- Ambiguous evidence consistently interpreted favorably
- Interpretation tracks interests rather than truth
- Same ambiguity resolved differently depending on who benefits
- Favorable readings chosen without justification
- Benefit of doubt given asymmetrically
- Interpretation changes when interests change
- Pattern of convenient readings across situations

When interpretation is fair:
- Ambiguity acknowledged rather than resolved conveniently
- Same interpretive standards applied regardless of who benefits
- Multiple readings considered before choosing
- Interpretation justified by evidence not interest
- Benefit of doubt applied consistently
- Interpretation stable regardless of who it favors
- Uncomfortable interpretations given fair consideration

Output JSON with: self_serving_present (bool), severity (none/mild/moderate/severe), interpretation (what interpretation is made), ambiguity (what is ambiguous), interest_served (what interest is served), alternative (what alternative interpretation exists), recommendation (fair_interpretation/mild_favorable_reading/significant_self_serving/major_interest_driven_interpretation/apply_consistent_standards)."""

SELF_SERVING_INTERPRETATION_PROMPT = """Detect self-serving interpretation:

Interpretation: {interpretation}
Evidence: {evidence}
Interest at stake: {interest}
Alternative reading: {alternative}
Domain: {domain}
Context: {context}

Is ambiguous evidence being interpreted in self-serving ways? Return ONLY valid JSON."""


class SelfServingInterpretationService:
    """Detects self-serving interpretation — ambiguity resolved for advantage."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        interpretation: str,
        *,
        evidence: str = "",
        interest: str = "",
        alternative: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect self-serving interpretation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=SELF_SERVING_INTERPRETATION_PROMPT.format(
                interpretation=interpretation,
                evidence=evidence or "Not specified",
                interest=interest or "Not specified",
                alternative=alternative or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=SELF_SERVING_INTERPRETATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "interpretation": interpretation[:200],
            "self_serving_present": data.get("self_serving_present", False),
            "severity": data.get("severity", ""),
            "ambiguity": data.get("ambiguity", ""),
            "interest_served": data.get("interest_served", ""),
            "alternative": data.get("alternative", ""),
            "recommendation": data.get("recommendation", ""),
        }
