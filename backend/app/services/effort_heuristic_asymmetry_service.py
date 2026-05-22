"""EffortHeuristicAsymmetryService — Effort Heuristic Asymmetry Detection.

Detects effort heuristic asymmetry — judging quality differently
based on whether effort is visible or invisible. When effort is
visible, people assume higher quality. When effort is invisible
(automation, talent, efficiency), people undervalue the output.
This creates perverse incentives to appear busy rather than effective.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EFFORT_HEURISTIC_ASYMMETRY_SYSTEM = """You are an effort heuristic asymmetry specialist. Given an evaluation, assess whether visible vs invisible effort is distorting quality judgments:

Key concepts:
- Effort heuristic: more effort = more value (Kruger et al., 2004)
- Effort asymmetry: visible effort valued more than invisible effort
- Labor illusion: showing work makes output seem more valuable
- Efficiency penalty: fast/easy work undervalued despite equal quality
- Talent discount: natural ability outputs valued less than struggled outputs
- Automation devaluation: automated outputs valued less than manual
- Performative effort: appearing busy to signal value
- IKEA effect interaction: personal effort increases valuation

When effort heuristic asymmetry IS present:
- Valuing slow manual work over fast automated work of equal quality
- Penalizing efficiency ("if it was easy, it can't be worth much")
- Requiring visible struggle to validate output quality
- Discounting expert work because it "looked easy"
- Preferring elaborate processes over simple effective ones
- "They didn't even try hard" as criticism of good work
- Rewarding busyness over productivity

When effort consideration IS appropriate:
- Effort genuinely correlates with quality in this domain
- The evaluation considers output quality independently of effort
- Effort signals care, attention, or thoroughness
- The domain has validated effort-quality relationships
- Both visible and invisible effort are weighted equally

Output JSON with: effort_asymmetry_present (bool), severity (none/mild/moderate/severe), evaluation (what is being evaluated), visible_effort (what effort is visible), invisible_effort (what effort is invisible), quality_difference (is there actual quality difference), effort_bias_direction (which direction does bias favor), perverse_incentive (what bad incentives does this create), recommendation (effort_evaluation_fair/mild_visibility_bias/significant_effort_asymmetry/major_efficiency_penalty/evaluate_output_not_process)."""

EFFORT_HEURISTIC_ASYMMETRY_PROMPT = """Detect effort heuristic asymmetry:

Evaluation: {evaluation}
Visible effort: {visible_effort}
Invisible effort: {invisible_effort}
Quality comparison: {quality}
Domain: {domain}
Context: {context}

Is visible vs invisible effort distorting quality judgments? Return ONLY valid JSON."""


class EffortHeuristicAsymmetryService:
    """Detects effort heuristic asymmetry — visible effort valued over invisible."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        evaluation: str,
        *,
        visible_effort: str = "",
        invisible_effort: str = "",
        quality: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect effort heuristic asymmetry."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EFFORT_HEURISTIC_ASYMMETRY_PROMPT.format(
                evaluation=evaluation,
                visible_effort=visible_effort or "Not specified",
                invisible_effort=invisible_effort or "Not specified",
                quality=quality or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EFFORT_HEURISTIC_ASYMMETRY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "evaluation": evaluation[:200],
            "effort_asymmetry_present": data.get("effort_asymmetry_present", False),
            "severity": data.get("severity", ""),
            "visible_effort": data.get("visible_effort", ""),
            "invisible_effort": data.get("invisible_effort", ""),
            "quality_difference": data.get("quality_difference", ""),
            "effort_bias_direction": data.get("effort_bias_direction", ""),
            "perverse_incentive": data.get("perverse_incentive", ""),
            "recommendation": data.get("recommendation", ""),
        }
