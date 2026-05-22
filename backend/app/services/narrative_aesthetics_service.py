"""NarrativeAestheticsService — Narrative Aesthetics Bias Detection.

Detects narrative aesthetics bias — preferring narratively satisfying
explanations over true but less satisfying ones.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

NARRATIVE_AESTHETICS_SYSTEM = """You are a narrative aesthetics bias specialist. Given an explanation preference, assess whether narrative satisfaction is being preferred over truth:

Key concepts:
- Narrative aesthetics bias: preferring narratively satisfying explanations
- Story over truth: choosing good stories over accurate accounts
- Dramatic preference: preferring dramatic explanations
- Arc satisfaction: preferring explanations with satisfying narrative arcs
- Character-driven explanation: preferring explanations with clear protagonists
- Resolution preference: preferring neat resolutions over messy reality
- Plot coherence over truth: preferring coherent plots over accurate accounts

When narrative aesthetics bias IS present:
- Narratively satisfying explanation preferred over true one
- Good story chosen over accurate account
- Dramatic explanation preferred without evidence
- Satisfying arc preferred over messy reality
- Character-driven explanation imposed on complex causation
- Neat resolution preferred over honest incompleteness
- Plot coherence prioritized over accuracy

When appropriate narrative use is present:
- Narrative used to communicate truth effectively
- Story structure serving understanding
- Drama proportionate to actual events
- Arc reflecting genuine development
- Characters representing real agents
- Resolution reflecting actual outcomes
- Coherence reflecting genuine patterns

Output JSON with: aesthetics_bias_present (bool), severity (none/mild/moderate/severe), explanation (what explanation is preferred), narrative_appeal (what makes it narratively appealing), truth_cost (what truth is sacrificed), accurate_alternative (what accurate but less satisfying alternative exists), recommendation (appropriate_narrative/mild_dramatization/significant_narrative_aesthetics/major_story_over_truth/prioritize_accuracy_over_narrative)."""

NARRATIVE_AESTHETICS_PROMPT = """Detect narrative aesthetics bias:

Explanation: {explanation}
Narrative appeal: {appeal}
Truth cost: {truth_cost}
Accurate alternative: {alternative}
Domain: {domain}
Context: {context}

Is narrative satisfaction being preferred over truth? Return ONLY valid JSON."""


class NarrativeAestheticsService:
    """Detects narrative aesthetics bias — preferring satisfying narratives over truth."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        explanation: str,
        *,
        appeal: str = "",
        truth_cost: str = "",
        alternative: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect narrative aesthetics bias."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=NARRATIVE_AESTHETICS_PROMPT.format(
                explanation=explanation,
                appeal=appeal or "Not specified",
                truth_cost=truth_cost or "Not specified",
                alternative=alternative or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=NARRATIVE_AESTHETICS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "explanation": explanation[:200],
            "aesthetics_bias_present": data.get("aesthetics_bias_present", False),
            "severity": data.get("severity", ""),
            "narrative_appeal": data.get("narrative_appeal", ""),
            "truth_cost": data.get("truth_cost", ""),
            "accurate_alternative": data.get("accurate_alternative", ""),
            "recommendation": data.get("recommendation", ""),
        }
