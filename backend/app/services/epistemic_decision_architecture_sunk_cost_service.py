"""EpistemicDecisionArchitectureSunkCostService — Sunk Cost Distortion Detection.

Detects sunk cost fallacy distorting forward-looking decisions.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_DECISION_ARCHITECTURE_SUNK_COST_SYSTEM = """You are an epistemic decision architecture sunk cost specialist. Given past investment weight, assess whether sunk costs are distorting forward-looking decisions:

Key concepts:
- Sunk cost fallacy: past irrecoverable investments distort future choices
- Past investment weight: giving prior cost evidential or decision weight
- Escalation of commitment: investing more to justify earlier investment
- Loss realization avoidance: continuing to avoid admitting or realizing a loss
- Emotional accounting: treating effort, money, or identity investment as reasons to continue

When sunk cost distortion IS present:
- Past investment outweighs forward-looking expected value
- Commitment escalates despite poor prospects
- Loss realization is avoided by continuing
- Emotional accounting substitutes for current fit

When no sunk cost distortion:
- Decisions use future costs, benefits, and opportunity costs
- Past investment is acknowledged as unrecoverable
- Exit criteria are explicit
- Continuing requires independent forward-looking justification

Output JSON with: sunk_cost_detected (bool), severity (none/mild/moderate/severe), escalation_of_commitment (how commitment escalates), loss_realization_avoidance (how loss realization is avoided), emotional_accounting (how emotional accounting distorts choice), recommendation (no_sunk_cost/mild_future_value_review/significant_exit_criteria/major_commitment_audit/emergency_stop_loss_review)."""

EPISTEMIC_DECISION_ARCHITECTURE_SUNK_COST_PROMPT = """Detect decision architecture sunk cost distortion:

Past investment weight: {past_investment_weight}
Escalation of commitment: {escalation_of_commitment}
Loss realization avoidance: {loss_realization_avoidance}
Emotional accounting: {emotional_accounting}
Domain: {domain}
Context: {context}

Are sunk costs distorting forward-looking decisions? Return ONLY valid JSON."""


class EpistemicDecisionArchitectureSunkCostService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        past_investment_weight: str,
        *,
        escalation_of_commitment: str = "",
        loss_realization_avoidance: str = "",
        emotional_accounting: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_DECISION_ARCHITECTURE_SUNK_COST_PROMPT.format(
                past_investment_weight=past_investment_weight,
                escalation_of_commitment=escalation_of_commitment or "Not specified",
                loss_realization_avoidance=loss_realization_avoidance or "Not specified",
                emotional_accounting=emotional_accounting or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_DECISION_ARCHITECTURE_SUNK_COST_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "past_investment_weight": past_investment_weight[:200],
            "sunk_cost_detected": data.get("sunk_cost_detected", False),
            "severity": data.get("severity", ""),
            "escalation_of_commitment": data.get("escalation_of_commitment", ""),
            "loss_realization_avoidance": data.get("loss_realization_avoidance", ""),
            "emotional_accounting": data.get("emotional_accounting", ""),
            "recommendation": data.get("recommendation", ""),
        }
