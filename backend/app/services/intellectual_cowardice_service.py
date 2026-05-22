"""IntellectualCowardiceService — Intellectual Cowardice Detection.

Detects intellectual cowardice — avoiding difficult truths,
uncomfortable conclusions, or challenging questions out of fear
of social consequences, professional risk, or personal discomfort.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

INTELLECTUAL_COWARDICE_SYSTEM = """You are an intellectual cowardice specialist. Given a reasoning situation, assess whether fear is preventing honest inquiry:

Key concepts:
- Intellectual cowardice: avoiding truth out of fear
- Epistemic timidity: not following evidence where it leads
- Social fear: avoiding conclusions that might be unpopular
- Professional risk aversion: not saying what evidence shows
- Comfortable ignorance: preferring not to know
- Self-censorship: suppressing own conclusions
- Courage deficit: lacking bravery to state uncomfortable truths

When intellectual cowardice IS present:
- Evidence points somewhere but fear prevents following
- Conclusions avoided because socially uncomfortable
- Professional risk prevents honest assessment
- Comfortable ignorance preferred over difficult truth
- Self-censorship suppresses genuine conclusions
- Fear of consequences overrides epistemic duty
- Difficult questions avoided rather than faced

When prudence is appropriate:
- Timing and context considered for communication
- Sensitivity to audience without sacrificing truth
- Professional judgment about when to speak
- Strategic silence that doesn't distort
- Courage exercised proportionally to stakes
- Truth told in appropriate manner
- Prudence serves truth not avoids it

Output JSON with: cowardice_present (bool), severity (none/mild/moderate/severe), situation (what situation exists), avoided (what truth is avoided), fear (what fear prevents honesty), cost (what epistemic cost results), recommendation (appropriate_prudence/mild_timidity/significant_intellectual_cowardice/major_truth_avoidance/practice_intellectual_courage)."""

INTELLECTUAL_COWARDICE_PROMPT = """Detect intellectual cowardice:

Situation: {situation}
Evidence direction: {evidence}
Conclusion avoided: {avoided}
Fear source: {fear}
Domain: {domain}
Context: {context}

Is fear preventing honest engagement with where evidence leads? Return ONLY valid JSON."""


class IntellectualCowardiceService:
    """Detects intellectual cowardice — fear preventing honest inquiry."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        evidence: str = "",
        avoided: str = "",
        fear: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect intellectual cowardice."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=INTELLECTUAL_COWARDICE_PROMPT.format(
                situation=situation,
                evidence=evidence or "Not specified",
                avoided=avoided or "Not specified",
                fear=fear or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=INTELLECTUAL_COWARDICE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "cowardice_present": data.get("cowardice_present", False),
            "severity": data.get("severity", ""),
            "avoided": data.get("avoided", ""),
            "fear": data.get("fear", ""),
            "cost": data.get("cost", ""),
            "recommendation": data.get("recommendation", ""),
        }
