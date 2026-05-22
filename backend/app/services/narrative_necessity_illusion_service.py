"""NarrativeNecessityIllusionService — Narrative Necessity Illusion Detection.

Detects narrative necessity illusion — treating contingent outcomes
as if they were inevitable, constructing after-the-fact narratives
that make random or path-dependent events seem predetermined.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

NARRATIVE_NECESSITY_ILLUSION_SYSTEM = """You are a narrative necessity illusion specialist. Given a historical or causal narrative, assess whether contingent outcomes are being presented as inevitable:

Key concepts:
- Narrative necessity: treating what happened as what had to happen
- Contingency: outcomes that could easily have been different
- Deterministic narrative: story implying inevitability
- Path dependence: small early events having large later effects
- Counterfactual fragility: how easily history could have diverged
- Whig history: reading present back into past as inevitable progress
- Survivorship narrative: only telling stories of what succeeded

When narrative necessity illusion IS present:
- Outcomes presented as inevitable when they were contingent
- Alternative paths not acknowledged
- Hindsight creating false sense of inevitability
- Narrative smoothing over decision points where things could have gone differently
- Success stories told as if failure was never possible
- Historical contingency erased by narrative structure
- "It was bound to happen" framing of unlikely events

When contingency is acknowledged:
- Multiple possible outcomes recognized
- Decision points identified where paths diverged
- Luck and timing acknowledged
- Alternative histories considered
- Inevitability claims qualified
- Contingent factors identified
- Narrative acknowledges uncertainty at each step

Output JSON with: illusion_present (bool), severity (none/mild/moderate/severe), narrative (what story is told), contingent_points (where outcomes could have differed), inevitability_claim (what is presented as inevitable), alternative_paths (what other outcomes were possible), recommendation (contingency_acknowledged/mild_inevitability/significant_necessity_illusion/major_deterministic_narrative/acknowledge_contingency)."""

NARRATIVE_NECESSITY_ILLUSION_PROMPT = """Detect narrative necessity illusion:

Narrative: {narrative}
Outcome: {outcome}
Decision points: {decision_points}
Alternatives: {alternatives}
Domain: {domain}
Context: {context}

Are contingent outcomes being presented as inevitable? Return ONLY valid JSON."""


class NarrativeNecessityIllusionService:
    """Detects narrative necessity illusion — contingent outcomes presented as inevitable."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        narrative: str,
        *,
        outcome: str = "",
        decision_points: str = "",
        alternatives: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect narrative necessity illusion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=NARRATIVE_NECESSITY_ILLUSION_PROMPT.format(
                narrative=narrative,
                outcome=outcome or "Not specified",
                decision_points=decision_points or "Not specified",
                alternatives=alternatives or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=NARRATIVE_NECESSITY_ILLUSION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "narrative": narrative[:200],
            "illusion_present": data.get("illusion_present", False),
            "severity": data.get("severity", ""),
            "contingent_points": data.get("contingent_points", ""),
            "inevitability_claim": data.get("inevitability_claim", ""),
            "alternative_paths": data.get("alternative_paths", ""),
            "recommendation": data.get("recommendation", ""),
        }
