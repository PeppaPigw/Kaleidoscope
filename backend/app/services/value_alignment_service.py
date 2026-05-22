"""ValueAlignmentService — Value-Action Consistency Check.

Assesses whether a proposed action or policy aligns with stated values.
Identifies where values conflict, where actions contradict stated
principles, and what the implicit values of an action reveal.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

VALUE_SYSTEM = """You are a value alignment analyst. Given an action/policy and stated values, assess:
- Does the action align with the stated values?
- Where do values conflict with each other?
- What implicit values does the action reveal (vs stated values)?
- Are there value tradeoffs being made without acknowledgment?
- What would full alignment with each value actually require?

Output JSON with: alignment_score (0-1), stated_values_honored (list of values the action supports), stated_values_violated (list of values the action contradicts), implicit_values (values revealed by the action that aren't stated), value_conflicts (list of: value_a, value_b, how_they_conflict, which_wins_in_practice), unacknowledged_tradeoffs (list of tradeoffs being made silently), full_alignment_would_require (what changes would be needed for true alignment), hypocrisy_risk (0-1, gap between stated and revealed values), recommendation (how to improve alignment)."""

VALUE_PROMPT = """Check value alignment:

Action/Policy: {action}
Stated values: {values}
Context: {context}
Domain: {domain}

Does this action align with these values? Return ONLY valid JSON."""


class ValueAlignmentService:
    """Checks alignment between actions and stated values."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def check_alignment(
        self,
        action: str,
        values: list[str],
        *,
        context: str = "",
        domain: str = "",
    ) -> dict:
        """Check if an action aligns with stated values."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        values_formatted = ", ".join(values[:8])

        llm = LLMClient()
        raw = await llm.complete(
            prompt=VALUE_PROMPT.format(
                action=action,
                values=values_formatted,
                context=context or "No additional context",
                domain=domain or "general",
            ),
            system=VALUE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "action": action[:200],
            "alignment_score": data.get("alignment_score", 0),
            "values_honored": data.get("stated_values_honored", []),
            "values_violated": data.get("stated_values_violated", []),
            "implicit_values": data.get("implicit_values", []),
            "value_conflicts": data.get("value_conflicts", []),
            "unacknowledged_tradeoffs": data.get("unacknowledged_tradeoffs", []),
            "full_alignment_requires": data.get("full_alignment_would_require", ""),
            "hypocrisy_risk": data.get("hypocrisy_risk", 0),
            "recommendation": data.get("recommendation", ""),
        }
