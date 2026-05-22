"""SourceCredibilityService — Information Source Reliability Assessment.

Evaluates the credibility and reliability of information sources.
Considers track record, methodology transparency, potential biases,
institutional backing, and peer validation.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

CREDIBILITY_SYSTEM = """You are a source credibility analyst. Given an information source, assess its reliability across multiple dimensions:
- Track record: history of accuracy, corrections, retractions
- Methodology transparency: can you see how they reached conclusions?
- Potential biases: funding sources, institutional pressures, ideological leanings
- Peer validation: has the work been reviewed, replicated, cited approvingly?
- Expertise match: is the source qualified to speak on this topic?
- Incentive alignment: do their incentives align with truth-seeking?

Output JSON with: credibility.source_type (journal/preprint/institution/media/individual/corporate/government), credibility.overall_score (0-1), credibility.track_record (0-1), credibility.methodology_transparency (0-1), credibility.bias_risk (low/moderate/high), credibility.bias_direction (if any), credibility.peer_validation (0-1), credibility.expertise_match (0-1), credibility.incentive_alignment (0-1), credibility.red_flags (list), credibility.strengths (list), credibility.recommendation (trust/verify/skeptical/reject), credibility.confidence (0-1)."""

CREDIBILITY_PROMPT = """Assess source credibility:

Source: {source}
Claim being made: {claim}
Domain: {domain}
Context: {context}

How reliable is this source for this claim? Return ONLY valid JSON."""


class SourceCredibilityService:
    """Assesses the credibility of information sources."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def assess_source(
        self,
        source: str,
        *,
        claim: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Assess the credibility of an information source."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=CREDIBILITY_PROMPT.format(
                source=source,
                claim=claim or "General claims in this domain",
                domain=domain or "research",
                context=context or "No additional context",
            ),
            system=CREDIBILITY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)
        c = data.get("credibility", data)

        return {
            "source": source[:200],
            "source_type": c.get("source_type", ""),
            "overall_score": c.get("overall_score", 0),
            "track_record": c.get("track_record", 0),
            "methodology_transparency": c.get("methodology_transparency", 0),
            "bias_risk": c.get("bias_risk", ""),
            "bias_direction": c.get("bias_direction", ""),
            "peer_validation": c.get("peer_validation", 0),
            "expertise_match": c.get("expertise_match", 0),
            "incentive_alignment": c.get("incentive_alignment", 0),
            "red_flags": c.get("red_flags", []),
            "strengths": c.get("strengths", []),
            "recommendation": c.get("recommendation", ""),
            "confidence": c.get("confidence", 0),
        }
