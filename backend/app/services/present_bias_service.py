"""PresentBiasService — Present Bias Detection.

Detects present bias — overweighting immediate rewards relative
to future rewards in a way that is inconsistent over time.
O'Donoghue & Rabin (1999). "I'll start tomorrow" but tomorrow
never comes. Distinct from standard discounting because
preferences reverse as the future becomes the present.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

PRESENT_BIAS_SYSTEM = """You are a present bias specialist. Given a decision involving tradeoffs between present and future, assess whether present bias is causing time-inconsistent choices:

Key concepts (O'Donoghue & Rabin, 1999):
- Present bias: disproportionate weight on immediate outcomes
- Beta-delta discounting: extra discount for "now vs later" beyond normal patience
- Time inconsistency: preferences that reverse as future becomes present
- Naive vs sophisticated: unaware of own bias vs. aware but still affected
- Commitment devices: tools to bind future self
- Procrastination: present bias applied to costs (delay pain)
- Preproperation: present bias applied to rewards (grab now)

When present bias IS present:
- "I'll start the diet/exercise/saving tomorrow" repeatedly
- Choosing smaller-sooner over larger-later rewards inconsistently
- Plans that always get postponed when the time comes
- Inability to follow through on long-term commitments
- Preference reversals as deadlines approach
- Overconsumption now with plans to compensate later
- "Just this once" that happens repeatedly

When the choice IS time-consistent:
- The person has stable preferences about timing
- Immediate choice reflects genuine values, not impulse
- There are legitimate reasons to prefer sooner (uncertainty, liquidity)
- The person follows through on stated plans
- Discount rate is consistent across time horizons

Output JSON with: present_bias_present (bool), severity (none/mild/moderate/severe), decision (what decision is being made), immediate_reward (what is the immediate payoff), future_reward (what is the future payoff), time_inconsistency (evidence of preference reversal), pattern (is this a repeated pattern?), awareness (is the person aware of their bias?), commitment_device (could a commitment device help?), recommendation (time_consistent/mild_present_bias/significant_procrastination/major_time_inconsistency/use_commitment_devices)."""

PRESENT_BIAS_PROMPT = """Detect present bias:

Decision: {decision}
Immediate option: {immediate}
Future option: {future}
Pattern: {pattern}
Domain: {domain}
Context: {context}

Is present bias causing time-inconsistent choices? Return ONLY valid JSON."""


class PresentBiasService:
    """Detects present bias — time-inconsistent overweighting of immediate outcomes."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        decision: str,
        *,
        immediate: str = "",
        future: str = "",
        pattern: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect present bias."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=PRESENT_BIAS_PROMPT.format(
                decision=decision,
                immediate=immediate or "Not specified",
                future=future or "Not specified",
                pattern=pattern or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=PRESENT_BIAS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "decision": decision[:200],
            "present_bias_present": data.get("present_bias_present", False),
            "severity": data.get("severity", ""),
            "immediate_reward": data.get("immediate_reward", ""),
            "future_reward": data.get("future_reward", ""),
            "time_inconsistency": data.get("time_inconsistency", ""),
            "pattern": data.get("pattern", ""),
            "awareness": data.get("awareness", ""),
            "commitment_device": data.get("commitment_device", ""),
            "recommendation": data.get("recommendation", ""),
        }
