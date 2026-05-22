"""EffortParadoxService — Effort Paradox Detection.

Detects the effort paradox — valuing things more when they're
harder to obtain even when difficulty adds no actual value.
Related to effort justification (Aronson & Mills, 1959) but
distinct: this is about prospective valuation of difficulty,
not retrospective justification. "If it's hard to get, it must
be worth getting" — confusing access difficulty with intrinsic value.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EFFORT_PARADOX_SYSTEM = """You are an effort paradox specialist. Given a valuation, assess whether difficulty of access is being confused with intrinsic value:

Key concepts:
- Effort paradox: harder to get = more valuable (regardless of actual value)
- Scarcity-value confusion: rare = valuable (not always true)
- Effort justification: past effort inflates perceived value
- Artificial barriers: difficulty that adds no value
- Gatekeeping as value signal: exclusivity as quality proxy
- Pain-gain confusion: suffering = earning/deserving
- Accessibility devaluation: easy access = low value

When effort paradox IS present:
- Valuing credentials more because they were hard to obtain
- Preferring complex solutions over simple equally-effective ones
- Dismissing accessible knowledge as less valuable
- "If everyone can do it, it can't be worth much"
- Artificial difficulty mistaken for quality filtering
- Suffering during acquisition treated as value-adding
- Rejecting efficient paths because they feel "too easy"

When difficulty-value correlation IS appropriate:
- Difficulty genuinely filters for quality (selective programs)
- The effort develops relevant skills (deliberate practice)
- Scarcity reflects genuine resource constraints
- The difficulty is inherent to the domain, not artificial
- Effort signals genuine commitment and investment

Output JSON with: effort_paradox_present (bool), severity (none/mild/moderate/severe), valuation (what is being valued), difficulty (what makes it hard), value_added_by_difficulty (does difficulty actually add value), alternative_path (is there an easier equally-good option), confusion_type (scarcity/effort/gatekeeping/pain), intrinsic_value (what is the actual value independent of difficulty), recommendation (difficulty_value_valid/mild_effort_confusion/significant_effort_paradox/major_difficulty_worship/evaluate_intrinsic_value)."""

EFFORT_PARADOX_PROMPT = """Detect effort paradox:

Valuation: {valuation}
Difficulty: {difficulty}
Alternative: {alternative}
Value claim: {value_claim}
Domain: {domain}
Context: {context}

Is difficulty of access being confused with intrinsic value? Return ONLY valid JSON."""


class EffortParadoxService:
    """Detects effort paradox — confusing difficulty with value."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        valuation: str,
        *,
        difficulty: str = "",
        alternative: str = "",
        value_claim: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect effort paradox."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EFFORT_PARADOX_PROMPT.format(
                valuation=valuation,
                difficulty=difficulty or "Not specified",
                alternative=alternative or "Not specified",
                value_claim=value_claim or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EFFORT_PARADOX_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "valuation": valuation[:200],
            "effort_paradox_present": data.get("effort_paradox_present", False),
            "severity": data.get("severity", ""),
            "difficulty": data.get("difficulty", ""),
            "value_added_by_difficulty": data.get("value_added_by_difficulty", ""),
            "alternative_path": data.get("alternative_path", ""),
            "confusion_type": data.get("confusion_type", ""),
            "intrinsic_value": data.get("intrinsic_value", ""),
            "recommendation": data.get("recommendation", ""),
        }
