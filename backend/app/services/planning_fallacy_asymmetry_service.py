"""PlanningFallacyAsymmetryService — Planning Fallacy Asymmetry Detection.

Detects planning fallacy asymmetry — the specific pattern where
people underestimate time/cost for their own tasks while being
more accurate (or even pessimistic) about others' tasks.
Buehler, Griffin & Ross (1994). The inside view dominates for
own projects while the outside view is available for others'.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

PLANNING_FALLACY_ASYMMETRY_SYSTEM = """You are a planning fallacy asymmetry specialist. Given time/cost estimates, assess whether there's an asymmetry between estimates for own tasks vs others' tasks:

Key concepts (Buehler, Griffin & Ross, 1994):
- Planning fallacy: underestimating own task completion time
- Inside view: focusing on specific case details (own projects)
- Outside view: using base rates and reference class (others' projects)
- Self-other asymmetry: accurate for others, optimistic for self
- Optimism bias interaction: motivated reasoning about own capabilities
- Unique case thinking: "my project is different"
- Reference class neglect: ignoring how long similar projects took

When planning fallacy asymmetry IS present:
- Own project estimates significantly shorter than similar past projects
- Accurate predictions for others' timelines but optimistic for own
- "This time will be different" for own work
- Acknowledging others face delays while assuming own won't
- Inside view for self, outside view for others
- Detailed plans creating illusion of control over own timeline
- History of own projects running over while predicting others' will too

When estimates ARE calibrated:
- Using reference class forecasting for own projects
- Track record of accurate self-estimation
- Explicit buffer added based on past overruns
- Same methodology applied to own and others' estimates
- Acknowledging uncertainty equally for self and others

Output JSON with: asymmetry_present (bool), severity (none/mild/moderate/severe), own_estimate (estimate for own task), others_estimate (estimate for others' similar tasks), reference_class (what similar past projects show), inside_view_dominance (how much is inside view dominating), track_record (past estimation accuracy), optimism_source (what drives the optimism for own tasks), recommendation (estimates_calibrated/mild_self_optimism/significant_planning_asymmetry/major_inside_view_dominance/apply_outside_view_to_self)."""

PLANNING_FALLACY_ASYMMETRY_PROMPT = """Detect planning fallacy asymmetry:

Situation: {situation}
Own estimate: {own_estimate}
Others' estimate: {others_estimate}
Past performance: {track_record}
Domain: {domain}
Context: {context}

Is there an asymmetry between optimistic self-estimates and more realistic estimates for others? Return ONLY valid JSON."""


class PlanningFallacyAsymmetryService:
    """Detects planning fallacy asymmetry — optimistic self-estimates vs realistic other-estimates."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        own_estimate: str = "",
        others_estimate: str = "",
        track_record: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect planning fallacy asymmetry."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=PLANNING_FALLACY_ASYMMETRY_PROMPT.format(
                situation=situation,
                own_estimate=own_estimate or "Not specified",
                others_estimate=others_estimate or "Not specified",
                track_record=track_record or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=PLANNING_FALLACY_ASYMMETRY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "asymmetry_present": data.get("asymmetry_present", False),
            "severity": data.get("severity", ""),
            "own_estimate": data.get("own_estimate", ""),
            "others_estimate": data.get("others_estimate", ""),
            "reference_class": data.get("reference_class", ""),
            "inside_view_dominance": data.get("inside_view_dominance", ""),
            "track_record": data.get("track_record", ""),
            "optimism_source": data.get("optimism_source", ""),
            "recommendation": data.get("recommendation", ""),
        }
