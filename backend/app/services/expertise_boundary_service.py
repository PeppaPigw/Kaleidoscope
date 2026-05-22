"""ExpertiseBoundaryService — Expertise Boundary Blindness Detection.

Detects expertise boundary blindness — failing to recognize where
expertise ends and speculation begins, presenting speculation with
the same confidence as expert knowledge.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EXPERTISE_BOUNDARY_SYSTEM = """You are an expertise boundary specialist. Given a claim or analysis, assess whether the boundary between expertise and speculation is being respected:

Key concepts:
- Expertise boundary: where knowledge ends and speculation begins
- Confidence-competence mismatch: same confidence across domains
- Unmarked speculation: speculation presented as knowledge
- Domain boundary blindness: not seeing where expertise stops
- Hedging failure: not qualifying claims outside expertise
- Overconfident extrapolation: extending expertise beyond its range
- Known-unknown boundary: failing to mark what is not known

When expertise boundary blindness IS present:
- Speculation presented with same confidence as expertise
- No marking of where knowledge ends
- Claims outside expertise not hedged
- Boundary between known and speculated invisible
- Confidence uniform across domains of varying competence
- Extrapolation beyond data presented as knowledge
- Uncertainty not acknowledged at boundary

When boundary management is appropriate:
- Clear marking of where expertise ends
- Speculation labeled as speculation
- Confidence calibrated to actual knowledge
- Hedging increases as claims move beyond expertise
- Known-unknown boundary explicitly stated
- Extrapolation acknowledged as extrapolation
- Different confidence levels for different claims

Output JSON with: blindness_present (bool), severity (none/mild/moderate/severe), claim (what is claimed), expertise_zone (where expertise is valid), speculation_zone (where speculation begins), boundary_unmarked (what boundary is not marked), recommendation (appropriate_boundary_management/mild_overextension/significant_boundary_blindness/major_speculation_as_expertise/mark_expertise_boundaries)."""

EXPERTISE_BOUNDARY_PROMPT = """Detect expertise boundary blindness:

Claim: {claim}
Expertise area: {expertise}
Claim domain: {claim_domain}
Confidence level: {confidence}
Domain: {domain}
Context: {context}

Is the boundary between expertise and speculation being respected? Return ONLY valid JSON."""


class ExpertiseBoundaryService:
    """Detects expertise boundary blindness — failing to mark where expertise ends."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        claim: str,
        *,
        expertise: str = "",
        claim_domain: str = "",
        confidence: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect expertise boundary blindness."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EXPERTISE_BOUNDARY_PROMPT.format(
                claim=claim,
                expertise=expertise or "Not specified",
                claim_domain=claim_domain or "Not specified",
                confidence=confidence or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EXPERTISE_BOUNDARY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "claim": claim[:200],
            "blindness_present": data.get("blindness_present", False),
            "severity": data.get("severity", ""),
            "expertise_zone": data.get("expertise_zone", ""),
            "speculation_zone": data.get("speculation_zone", ""),
            "boundary_unmarked": data.get("boundary_unmarked", ""),
            "recommendation": data.get("recommendation", ""),
        }
