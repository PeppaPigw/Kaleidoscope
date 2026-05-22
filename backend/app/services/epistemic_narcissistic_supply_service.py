"""EpistemicNarcissisticSupplyService — Epistemic Narcissistic Supply Detection.

Detects epistemic narcissistic supply — seeking admiration and validation
for intellectual superiority as a primary motivational driver.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_NARCISSISTIC_SUPPLY_SYSTEM = """You are an epistemic narcissistic supply specialist. Given intellectual admiration-seeking, assess narcissistic supply:

Key concepts:
- Epistemic narcissistic supply: needing admiration for intellect
- Validation hunger: insatiable need for intellectual recognition
- Superiority display: showcasing knowledge for admiration
- Audience dependence: needing others to witness brilliance
- Supply source: who provides the admiration
- Withdrawal crash: collapse when supply removed
- Performance orientation: thinking as performance not inquiry

When epistemic narcissistic supply IS present:
- Needing admiration for intellect
- Insatiable recognition need
- Showcasing for admiration
- Needing witnesses to brilliance
- Dependent on supply sources
- Crashing without supply
- Thinking as performance

When no narcissistic supply:
- Intrinsic intellectual motivation
- Self-validated understanding
- Sharing for collaboration
- Independent of audience
- Self-sustaining curiosity
- Stable without recognition
- Thinking as genuine inquiry

Output JSON with: narcissistic_supply_detected (bool), severity (none/mild/moderate/severe), validation_hunger (what needing), superiority_display (what showcasing), audience_dependence (what needing witness), withdrawal_pattern (what happens without), recommendation (no_narcissistic_supply/mild_motivation_awareness/significant_supply_reduction/major_intensive_restructuring/emergency_supply_collapse)."""

EPISTEMIC_NARCISSISTIC_SUPPLY_PROMPT = """Detect epistemic narcissistic supply:

Validation hunger: {validation_hunger}
Superiority display: {superiority_display}
Audience dependence: {audience_dependence}
Withdrawal pattern: {withdrawal_pattern}
Domain: {domain}
Context: {context}

Is there seeking of admiration for intellectual superiority as primary motivation? Return ONLY valid JSON."""


class EpistemicNarcissisticSupplyService:
    """Detects epistemic narcissistic supply — seeking intellectual admiration."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        validation_hunger: str,
        *,
        superiority_display: str = "",
        audience_dependence: str = "",
        withdrawal_pattern: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic narcissistic supply."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_NARCISSISTIC_SUPPLY_PROMPT.format(
                validation_hunger=validation_hunger,
                superiority_display=superiority_display or "Not specified",
                audience_dependence=audience_dependence or "Not specified",
                withdrawal_pattern=withdrawal_pattern or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_NARCISSISTIC_SUPPLY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "validation_hunger": validation_hunger[:200],
            "narcissistic_supply_detected": data.get("narcissistic_supply_detected", False),
            "severity": data.get("severity", ""),
            "superiority_display": data.get("superiority_display", ""),
            "audience_dependence": data.get("audience_dependence", ""),
            "withdrawal_pattern": data.get("withdrawal_pattern", ""),
            "recommendation": data.get("recommendation", ""),
        }
