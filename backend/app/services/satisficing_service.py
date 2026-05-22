"""SatisficingService — Satisficing vs Maximizing Assessment.

Evaluates whether a decision context calls for satisficing (good
enough) or maximizing (best possible). Herbert Simon's bounded
rationality. Failures come from maximizing when satisficing is
appropriate (analysis paralysis) or satisficing when maximizing
is needed (cutting corners on safety-critical systems).
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

SATISFICING_SYSTEM = """You are a satisficing/maximizing specialist. Given a decision, assess whether the approach matches the context:
- Is the decision-maker maximizing when satisficing would be appropriate?
- Is the decision-maker satisficing when maximizing is needed?
- What are the costs of additional search/optimization?
- What are the costs of a suboptimal choice?
- Is the decision reversible (favoring satisficing) or irreversible (favoring maximizing)?

Output JSON with: current_approach (satisficing/maximizing/unclear), appropriate_approach (satisficing/maximizing/depends), mismatch_present (bool — is the wrong approach being used?), mismatch_type (over_optimizing/under_optimizing/none), decision_reversibility (easily_reversible/moderately_reversible/irreversible), stakes (low/moderate/high/critical), search_cost (cost of continuing to look for better options), opportunity_cost_of_delay (what is lost by not deciding now), marginal_improvement_likely (0-1 — probability that more search finds meaningfully better option), good_enough_threshold (what "good enough" looks like here), current_option_quality (how good the current best option is relative to threshold), analysis_paralysis_risk (0-1 — risk of over-analyzing), regret_risk (0-1 — risk of regretting a hasty choice), time_pressure (none/low/moderate/high/critical), information_available (how much relevant info exists: abundant/moderate/scarce), recommendation (satisfice_now/maximize_carefully/set_deadline/accept_current/keep_searching)."""

SATISFICING_PROMPT = """Assess satisficing vs maximizing:

Decision: {decision}
Current options: {options}
Time available: {time_available}
Stakes: {stakes}
Domain: {domain}
Context: {context}

Should this be satisficed or maximized? Return ONLY valid JSON."""


class SatisficingService:
    """Assesses whether to satisfice or maximize."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def assess(
        self,
        decision: str,
        *,
        options: str = "",
        time_available: str = "",
        stakes: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Assess satisficing vs maximizing."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=SATISFICING_PROMPT.format(
                decision=decision,
                options=options or "Not specified",
                time_available=time_available or "Not specified",
                stakes=stakes or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=SATISFICING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "decision": decision[:200],
            "current_approach": data.get("current_approach", ""),
            "appropriate_approach": data.get("appropriate_approach", ""),
            "mismatch_present": data.get("mismatch_present", False),
            "mismatch_type": data.get("mismatch_type", ""),
            "decision_reversibility": data.get("decision_reversibility", ""),
            "stakes": data.get("stakes", ""),
            "search_cost": data.get("search_cost", ""),
            "opportunity_cost_of_delay": data.get("opportunity_cost_of_delay", ""),
            "marginal_improvement_likely": data.get("marginal_improvement_likely", 0),
            "good_enough_threshold": data.get("good_enough_threshold", ""),
            "current_option_quality": data.get("current_option_quality", ""),
            "analysis_paralysis_risk": data.get("analysis_paralysis_risk", 0),
            "regret_risk": data.get("regret_risk", 0),
            "time_pressure": data.get("time_pressure", ""),
            "information_available": data.get("information_available", ""),
            "recommendation": data.get("recommendation", ""),
        }
