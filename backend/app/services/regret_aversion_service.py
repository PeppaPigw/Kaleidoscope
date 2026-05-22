"""RegretAversionService — Regret Aversion Detection.

Detects regret aversion — making decisions to minimize anticipated
regret rather than maximize expected value, where fear of future
regret distorts rational decision-making.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

REGRET_AVERSION_SYSTEM = """You are a regret aversion specialist. Given a decision, assess whether anticipated regret is distorting rational choice:

Key concepts:
- Regret aversion: choosing to minimize regret, not maximize value
- Anticipated regret: imagined future regret driving current choice
- Minimax regret: minimizing worst-case regret
- Regret asymmetry: regret from action vs. inaction weighted differently
- Counterfactual thinking: imagining 'what if' driving decisions
- Regret salience: vivid regret scenarios overweighting
- Decision justifiability: choosing what's easiest to justify later

When regret aversion IS present:
- Decision driven by minimizing anticipated regret
- Expected value sacrificed to avoid potential regret
- Vivid regret scenarios overweighting rational analysis
- Choice made for justifiability rather than optimality
- Counterfactual thinking dominating decision process
- Risk avoidance beyond what expected value justifies
- Conventional choice preferred because unconventional risks regret

When regret consideration is appropriate:
- Regret as one factor among many in decision
- Expected value still primary criterion
- Regret consideration proportionate to stakes
- Emotional cost of regret genuinely relevant
- Regret analysis informing but not dominating
- Both action and inaction regret considered
- Regret used as signal, not sole criterion

Output JSON with: aversion_present (bool), severity (none/mild/moderate/severe), decision (what decision is being made), regret_scenario (what regret is anticipated), expected_value (what expected value analysis shows), distortion (how regret distorts choice), recommendation (appropriate_regret_consideration/mild_regret_weighting/significant_regret_aversion/major_value_sacrifice/decide_on_expected_value)."""

REGRET_AVERSION_PROMPT = """Detect regret aversion:

Decision: {decision}
Anticipated regret: {regret}
Expected value: {value}
Alternative: {alternative}
Domain: {domain}
Context: {context}

Is anticipated regret distorting rational decision-making? Return ONLY valid JSON."""


class RegretAversionService:
    """Detects regret aversion — decisions driven by minimizing anticipated regret."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        decision: str,
        *,
        regret: str = "",
        value: str = "",
        alternative: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect regret aversion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=REGRET_AVERSION_PROMPT.format(
                decision=decision,
                regret=regret or "Not specified",
                value=value or "Not specified",
                alternative=alternative or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=REGRET_AVERSION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "decision": decision[:200],
            "aversion_present": data.get("aversion_present", False),
            "severity": data.get("severity", ""),
            "regret_scenario": data.get("regret_scenario", ""),
            "expected_value": data.get("expected_value", ""),
            "distortion": data.get("distortion", ""),
            "recommendation": data.get("recommendation", ""),
        }
