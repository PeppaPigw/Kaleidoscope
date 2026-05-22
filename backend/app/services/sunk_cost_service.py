"""SunkCostService — Sunk Cost Fallacy Detection.

Identifies when past investments (time, money, effort) are
irrationally influencing current decisions. Separates what's
already spent (irrecoverable) from what's still at stake.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

SUNK_COST_SYSTEM = """You are a sunk cost analyst. Given a decision where past investment is being cited, assess whether sunk cost fallacy is present:
- What has already been invested (truly sunk, irrecoverable)?
- Is the past investment influencing the current decision?
- What would a fresh decision-maker choose (ignoring history)?
- Is "we've come this far" being used as justification?
- What are the FUTURE costs and benefits (the only ones that matter)?

Output JSON with: sunk_cost_present (bool), severity (none/mild/moderate/severe), sunk_investments (list of: type, amount, truly_irrecoverable (bool)), future_costs (costs still to come regardless of past), future_benefits (benefits still achievable), fresh_decision (what a new decision-maker would choose), emotional_attachment (0-1, how much emotion is driving continuation), escalation_of_commitment (bool — is this throwing good money after bad?), kill_criteria (what conditions should trigger stopping), continuation_justified (bool — is continuing actually rational despite sunk costs?), justification_reason (if continuation IS justified, why), recommendation (continue/pivot/stop/reassess), key_reframe (how to think about this without the sunk cost bias)."""

SUNK_COST_PROMPT = """Detect sunk cost fallacy:

Decision: {decision}
Past investment: {past_investment}
Current justification: {justification}
Domain: {domain}
Context: {context}

Is sunk cost fallacy influencing this? Return ONLY valid JSON."""


class SunkCostService:
    """Detects sunk cost fallacy in decision-making."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        decision: str,
        *,
        past_investment: str = "",
        justification: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect sunk cost fallacy."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=SUNK_COST_PROMPT.format(
                decision=decision,
                past_investment=past_investment or "Not specified",
                justification=justification or "Not explicitly stated",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=SUNK_COST_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "decision": decision[:200],
            "sunk_cost_present": data.get("sunk_cost_present", False),
            "severity": data.get("severity", ""),
            "sunk_investments": data.get("sunk_investments", []),
            "future_costs": data.get("future_costs", ""),
            "future_benefits": data.get("future_benefits", ""),
            "fresh_decision": data.get("fresh_decision", ""),
            "emotional_attachment": data.get("emotional_attachment", 0),
            "escalation_of_commitment": data.get("escalation_of_commitment", False),
            "kill_criteria": data.get("kill_criteria", ""),
            "continuation_justified": data.get("continuation_justified", False),
            "justification_reason": data.get("justification_reason", ""),
            "recommendation": data.get("recommendation", ""),
            "key_reframe": data.get("key_reframe", ""),
        }
