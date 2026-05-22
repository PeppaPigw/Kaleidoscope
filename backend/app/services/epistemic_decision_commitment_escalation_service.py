"""EpistemicDecisionCommitmentEscalationService - Commitment Escalation Detection.

Detects commitment escalation where prior investment drives continued investment despite failure.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_DECISION_COMMITMENT_ESCALATION_SYSTEM = """You are an epistemic decision commitment escalation specialist. Given investment patterns, assess whether sunk costs drive continued commitment:

Key concepts:
- Commitment escalation: increasing investment in failing course of action due to prior investment
- Sunk cost reasoning: treating irrecoverable costs as relevant to future decisions
- Self-justification: continuing to validate prior decisions
- Loss aversion amplification: fear of admitting loss driving further investment

When commitment escalation IS present:
- Prior investment drives continued commitment
- Sunk costs treated as relevant
- Self-justification overrides evidence
- Loss aversion amplified
- Exit signals ignored

When no commitment escalation:
- Decisions based on future prospects
- Sunk costs recognized as irrelevant
- Evidence drives continuation decisions
- Losses acknowledged when appropriate
- Exit signals heeded

Output JSON with: commitment_escalation_detected (bool), severity (none/mild/moderate/severe), sunk_cost_reasoning (what sunk cost reasoning), self_justification (what self-justification), loss_aversion_amplification (what loss aversion), recommendation (no_commitment_escalation/mild_sunk_cost_check/significant_exit_analysis/major_decision_reconstruction/emergency_complete_commitment_escalation)."""

EPISTEMIC_DECISION_COMMITMENT_ESCALATION_PROMPT = """Detect epistemic decision commitment escalation:

Investment pattern: {investment_pattern}
Sunk cost reasoning: {sunk_cost_reasoning}
Self justification: {self_justification}
Loss aversion amplification: {loss_aversion_amplification}
Domain: {domain}
Context: {context}

Is prior investment driving continued commitment despite failure? Return ONLY valid JSON."""


class EpistemicDecisionCommitmentEscalationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        investment_pattern: str,
        *,
        sunk_cost_reasoning: str = "",
        self_justification: str = "",
        loss_aversion_amplification: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_DECISION_COMMITMENT_ESCALATION_PROMPT.format(
                investment_pattern=investment_pattern,
                sunk_cost_reasoning=sunk_cost_reasoning or "Not specified",
                self_justification=self_justification or "Not specified",
                loss_aversion_amplification=loss_aversion_amplification or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_DECISION_COMMITMENT_ESCALATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "investment_pattern": investment_pattern[:200],
            "commitment_escalation_detected": data.get("commitment_escalation_detected", False),
            "severity": data.get("severity", ""),
            "sunk_cost_reasoning": data.get("sunk_cost_reasoning", ""),
            "self_justification": data.get("self_justification", ""),
            "loss_aversion_amplification": data.get("loss_aversion_amplification", ""),
            "recommendation": data.get("recommendation", ""),
        }
