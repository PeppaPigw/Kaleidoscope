"""StatusQuoBiasService — Status Quo Bias Detection.

Detects status quo bias — the preference for the current state
of affairs, where any change is perceived as a loss. Combines
loss aversion, mere exposure effect, and omission bias. The
default wins not because it's best, but because switching
requires effort and feels risky.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

STATUS_QUO_SYSTEM = """You are a status quo bias specialist. Given a decision where maintaining the current state is an option, assess whether status quo bias is distorting the choice:

Key mechanisms:
- Loss aversion: losses from switching loom larger than equivalent gains
- Endowment effect: overvaluing what you already have
- Omission bias: preferring harm from inaction over harm from action
- Default effect: whatever is pre-selected gets chosen disproportionately
- Mere exposure: familiarity breeds preference regardless of quality
- Switching costs (real and perceived): effort of change deters even beneficial switches
- Regret asymmetry: anticipated regret from action > anticipated regret from inaction

Output JSON with: status_quo_bias_present (bool), severity (none/mild/moderate/severe/extreme), current_state (what the status quo is), alternative (what the change would be), loss_aversion_factor (what losses are being overweighted), endowment_effect (what is being overvalued due to ownership), omission_bias (bool — is inaction being preferred to avoid blame?), switching_cost_real (actual cost of switching), switching_cost_perceived (perceived cost — often inflated), default_effect (bool — is the status quo winning because it's the default?), rational_choice (what an unbiased analysis would recommend), bias_magnitude (0-1 — how much bias is distorting the decision), regret_asymmetry (bool — is regret from action feared more than regret from inaction?), who_benefits_from_inertia (who gains from things staying the same), accumulated_cost_of_inaction (what is lost by not switching), nudge_suggestion (how to overcome the bias without forcing change), recommendation (status_quo_justified/mild_bias_present/significant_bias/change_clearly_better/design_better_default)."""

STATUS_QUO_PROMPT = """Detect status quo bias:

Decision: {decision}
Current state: {current_state}
Proposed change: {proposed_change}
Switching costs: {switching_costs}
Domain: {domain}
Context: {context}

Is status quo bias at play? Return ONLY valid JSON."""


class StatusQuoBiasService:
    """Detects status quo bias and default effects."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        decision: str,
        *,
        current_state: str = "",
        proposed_change: str = "",
        switching_costs: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect status quo bias."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=STATUS_QUO_PROMPT.format(
                decision=decision,
                current_state=current_state or "Not specified",
                proposed_change=proposed_change or "Not specified",
                switching_costs=switching_costs or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=STATUS_QUO_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "decision": decision[:200],
            "status_quo_bias_present": data.get("status_quo_bias_present", False),
            "severity": data.get("severity", ""),
            "current_state": data.get("current_state", ""),
            "alternative": data.get("alternative", ""),
            "loss_aversion_factor": data.get("loss_aversion_factor", ""),
            "endowment_effect": data.get("endowment_effect", ""),
            "omission_bias": data.get("omission_bias", False),
            "switching_cost_real": data.get("switching_cost_real", ""),
            "switching_cost_perceived": data.get("switching_cost_perceived", ""),
            "default_effect": data.get("default_effect", False),
            "rational_choice": data.get("rational_choice", ""),
            "bias_magnitude": data.get("bias_magnitude", 0),
            "regret_asymmetry": data.get("regret_asymmetry", False),
            "who_benefits_from_inertia": data.get("who_benefits_from_inertia", ""),
            "accumulated_cost_of_inaction": data.get("accumulated_cost_of_inaction", ""),
            "nudge_suggestion": data.get("nudge_suggestion", ""),
            "recommendation": data.get("recommendation", ""),
        }
