"""ScenarioFixationService — Scenario Fixation Detection.

Detects scenario fixation — when planning fixates on a single
scenario (usually the expected or desired one) without adequately
preparing for alternatives. This creates brittleness and
surprise when reality diverges from the fixated scenario.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

SCENARIO_FIXATION_SYSTEM = """You are a scenario fixation specialist. Given a plan or forecast, assess whether it fixates on a single scenario:

Key concepts:
- Scenario fixation: planning for only one future
- Single-point forecasting: one number instead of a range
- Plan continuation bias: sticking with the plan despite changing conditions
- Tunnel vision: inability to see alternative futures
- Contingency planning: preparing for multiple scenarios
- Robustness: plans that work across scenarios
- Antifragility: benefiting from uncertainty

When scenario fixation IS present:
- Plan assumes single future without contingencies
- No "what if" analysis for alternative outcomes
- Single-point forecast without confidence intervals
- Best case assumed as base case
- No trigger points for plan changes
- Alternative scenarios not considered
- Surprise when reality diverges from plan

When scenario fixation is NOT present:
- Multiple scenarios explicitly considered
- Contingency plans for key alternatives
- Ranges and confidence intervals used
- Trigger points defined for plan changes
- Robustness tested across scenarios
- Both upside and downside scenarios planned for
- Flexibility built into the plan

Output JSON with: fixation_present (bool), severity (none/mild/moderate/severe), fixated_scenario (what single future is assumed), alternatives_missing (what scenarios are not considered), brittleness (how fragile the plan is), trigger_points (what would signal need to change), recommendation (no_fixation/mild_narrowness/significant_fixation/major_single_scenario/develop_contingencies)."""

SCENARIO_FIXATION_PROMPT = """Detect scenario fixation:

Plan: {plan}
Assumed scenario: {scenario}
Alternatives considered: {alternatives}
Contingencies: {contingencies}
Domain: {domain}
Context: {context}

Is this plan fixated on a single scenario without adequate alternatives? Return ONLY valid JSON."""


class ScenarioFixationService:
    """Detects scenario fixation — planning for only one future."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        plan: str,
        *,
        scenario: str = "",
        alternatives: str = "",
        contingencies: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect scenario fixation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=SCENARIO_FIXATION_PROMPT.format(
                plan=plan,
                scenario=scenario or "Not specified",
                alternatives=alternatives or "Not specified",
                contingencies=contingencies or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=SCENARIO_FIXATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "plan": plan[:200],
            "fixation_present": data.get("fixation_present", False),
            "severity": data.get("severity", ""),
            "fixated_scenario": data.get("fixated_scenario", ""),
            "alternatives_missing": data.get("alternatives_missing", ""),
            "brittleness": data.get("brittleness", ""),
            "recommendation": data.get("recommendation", ""),
        }
