"""EpistemicPlateauDenialService — Epistemic Plateau Denial Detection.

Detects epistemic plateau denial — denying one has plateaued intellectually
and refusing to acknowledge stagnation.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PLATEAU_DENIAL_SYSTEM = """You are an epistemic plateau denial specialist. Given denying intellectual plateau, assess plateau denial:

Key concepts:
- Epistemic plateau denial: denying one has plateaued intellectually
- Stagnation blindness: unable to see own stagnation
- Progress illusion: maintaining illusion of progress without real growth
- Repetition as novelty: treating repetition of old ideas as new insight
- Depth avoidance: staying at same depth while claiming to go deeper
- Mastery inflation: inflating sense of mastery beyond actual level
- Growth theater: performing growth without actually growing

When epistemic plateau denial IS present:
- Denying plateau
- Unable to see stagnation
- Maintaining progress illusion
- Treating repetition as novelty
- Staying at same depth
- Inflating mastery sense
- Performing growth without growing

When no plateau denial:
- Acknowledging plateaus
- Seeing stagnation clearly
- Honest about progress
- Distinguishing repetition from novelty
- Aware of actual depth
- Accurate mastery assessment
- Genuine growth

Output JSON with: plateau_denial_detected (bool), severity (none/mild/moderate/severe), stagnation_blindness (what stagnation blind to), progress_illusion (what illusion of progress about), repetition_as_novelty (what repetition treated as novel), mastery_inflation (what mastery inflated about), recommendation (no_plateau_denial/mild_honest_assessment/significant_plateau_acknowledgment/major_intensive_growth_restart/emergency_complete_plateau_denial)."""

EPISTEMIC_PLATEAU_DENIAL_PROMPT = """Detect epistemic plateau denial:

Stagnation blindness: {stagnation_blindness}
Progress illusion: {progress_illusion}
Repetition as novelty: {repetition_as_novelty}
Mastery inflation: {mastery_inflation}
Domain: {domain}
Context: {context}

Is there denying one has plateaued intellectually? Return ONLY valid JSON."""


class EpistemicPlateauDenialService:
    """Detects epistemic plateau denial — denying intellectual plateau."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        stagnation_blindness: str,
        *,
        progress_illusion: str = "",
        repetition_as_novelty: str = "",
        mastery_inflation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic plateau denial."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PLATEAU_DENIAL_PROMPT.format(
                stagnation_blindness=stagnation_blindness,
                progress_illusion=progress_illusion or "Not specified",
                repetition_as_novelty=repetition_as_novelty or "Not specified",
                mastery_inflation=mastery_inflation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PLATEAU_DENIAL_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "stagnation_blindness": stagnation_blindness[:200],
            "plateau_denial_detected": data.get("plateau_denial_detected", False),
            "severity": data.get("severity", ""),
            "progress_illusion": data.get("progress_illusion", ""),
            "repetition_as_novelty": data.get("repetition_as_novelty", ""),
            "mastery_inflation": data.get("mastery_inflation", ""),
            "recommendation": data.get("recommendation", ""),
        }
