"""NarrativeCoherenceService — Internal Consistency & Plot Hole Detection.

Takes an explanation or narrative and checks whether it's internally
consistent. Identifies logical gaps, contradictions, unexplained jumps,
and where narrative is doing work that evidence should be doing.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

COHERENCE_SYSTEM = """You are a narrative coherence analyst. Given an explanation or argument, check for:
- Internal contradictions (does it contradict itself?)
- Logical gaps (jumps in reasoning where a step is missing)
- Unexplained transitions (where does the argument change direction without justification?)
- Narrative doing evidence's work (where is the story compelling but the evidence absent?)
- Selective framing (what's being left out that would change the picture?)
- Temporal inconsistencies (does the timeline make sense?)

Output JSON with: coherence_score (0-1), contradictions (list of: statement_a, statement_b, why_contradictory), logical_gaps (list of: from_point, to_point, missing_step), narrative_over_evidence (list of: claim, why_narrative_not_evidence), selective_framing (list of what's omitted), temporal_issues (list if any), overall_verdict (coherent/mostly_coherent/has_gaps/incoherent), strongest_point (where the narrative is most solid), weakest_point (where it's most vulnerable), repair_suggestions (how to fix the gaps)."""

COHERENCE_PROMPT = """Check narrative coherence:

Narrative/Explanation: {narrative}
Claimed conclusion: {conclusion}
Domain: {domain}

Is this internally consistent? Return ONLY valid JSON."""


class NarrativeCoherenceService:
    """Checks internal consistency of narratives and explanations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def check(
        self,
        narrative: str,
        *,
        conclusion: str = "",
        domain: str = "",
    ) -> dict:
        """Check narrative coherence."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=COHERENCE_PROMPT.format(
                narrative=narrative,
                conclusion=conclusion or "Not explicitly stated",
                domain=domain or "general",
            ),
            system=COHERENCE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "coherence_score": data.get("coherence_score", 0),
            "contradictions": data.get("contradictions", []),
            "logical_gaps": data.get("logical_gaps", []),
            "narrative_over_evidence": data.get("narrative_over_evidence", []),
            "selective_framing": data.get("selective_framing", []),
            "temporal_issues": data.get("temporal_issues", []),
            "overall_verdict": data.get("overall_verdict", ""),
            "strongest_point": data.get("strongest_point", ""),
            "weakest_point": data.get("weakest_point", ""),
            "repair_suggestions": data.get("repair_suggestions", []),
        }
