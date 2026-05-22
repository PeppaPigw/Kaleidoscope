"""PlanningFallacyService — Planning Fallacy Detection.

Detects the planning fallacy — systematic underestimation of time,
cost, and risk for planned actions while knowing that similar past
projects overran. Kahneman & Tversky (1979). The inside view
(this project's specifics) dominates the outside view (base rates
from similar projects).
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

PLANNING_SYSTEM = """You are a planning fallacy specialist. Given a plan or estimate, assess whether the planning fallacy is distorting expectations:

Key concepts (Kahneman & Tversky, 1979; Buehler et al., 1994):
- Inside view: focusing on the specific case, its unique features, and best-case scenarios
- Outside view: looking at base rates from similar past projects (reference class forecasting)
- Optimism bias: systematic tendency to expect better outcomes than warranted
- Coordination neglect: underestimating how many things must go right simultaneously
- Best-case planning: the estimate assumes everything goes smoothly
- Uniqueness bias: "this project is different" (it usually isn't)
- Completion bias: focusing on what's been done rather than what remains

Reference class forecasting (Flyvbjerg):
- IT projects: average 45% over budget, 7% over time
- Infrastructure: average 28% over budget
- Olympic Games: average 156% over budget
- Software: 66% of projects exceed estimates by >50%

When the planning fallacy IS present:
- Estimate based on best-case scenario
- No reference to similar past projects
- "This time is different" reasoning
- Ignoring coordination complexity
- Anchoring on desired completion date rather than realistic assessment

When the estimate MAY be reasonable:
- Based on reference class data
- Includes explicit contingency buffers
- Accounts for coordination risks
- Has been adjusted upward from initial intuition
- Uses pre-mortem analysis

Output JSON with: planning_fallacy_present (bool), severity (none/mild/moderate/severe), inside_view_estimate (what the plan says), outside_view_estimate (what reference class data suggests), optimism_factor (ratio of likely actual to estimated), reference_class (what similar projects actually took), uniqueness_bias (bool — treating this as special when it's not), coordination_neglect (bool — underestimating dependencies), best_case_planning (bool — assuming everything goes right), anchoring_on_deadline (bool — working backward from desired date), contingency_buffer (what buffer exists, if any), known_unknowns (acknowledged risks), unknown_unknowns_likely (what surprises are probable), pre_mortem_done (bool — has failure been imagined?), debiasing_applied (what corrections have been made), realistic_range (low/mid/high estimates based on outside view), recommendation (estimate_reasonable/mild_optimism/significant_planning_fallacy/major_underestimate/apply_reference_class_forecasting)."""

PLANNING_PROMPT = """Detect planning fallacy:

Plan/Estimate: {plan}
Timeline/Budget: {timeline}
Similar past projects: {past_similar}
Key assumptions: {assumptions}
Domain: {domain}
Context: {context}

Is the planning fallacy distorting this estimate? Return ONLY valid JSON."""


class PlanningFallacyService:
    """Detects planning fallacy — systematic underestimation via inside view."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        plan: str,
        *,
        timeline: str = "",
        past_similar: str = "",
        assumptions: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect planning fallacy."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=PLANNING_PROMPT.format(
                plan=plan,
                timeline=timeline or "Not specified",
                past_similar=past_similar or "Not specified",
                assumptions=assumptions or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=PLANNING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "plan": plan[:200],
            "planning_fallacy_present": data.get("planning_fallacy_present", False),
            "severity": data.get("severity", ""),
            "inside_view_estimate": data.get("inside_view_estimate", ""),
            "outside_view_estimate": data.get("outside_view_estimate", ""),
            "optimism_factor": data.get("optimism_factor", ""),
            "reference_class": data.get("reference_class", ""),
            "uniqueness_bias": data.get("uniqueness_bias", False),
            "coordination_neglect": data.get("coordination_neglect", False),
            "best_case_planning": data.get("best_case_planning", False),
            "anchoring_on_deadline": data.get("anchoring_on_deadline", False),
            "contingency_buffer": data.get("contingency_buffer", ""),
            "known_unknowns": data.get("known_unknowns", ""),
            "unknown_unknowns_likely": data.get("unknown_unknowns_likely", ""),
            "pre_mortem_done": data.get("pre_mortem_done", False),
            "debiasing_applied": data.get("debiasing_applied", ""),
            "realistic_range": data.get("realistic_range", ""),
            "recommendation": data.get("recommendation", ""),
        }
