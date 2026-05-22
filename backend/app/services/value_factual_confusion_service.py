"""ValueFactualConfusionService — Value-Factual Confusion Detection.

Detects value-factual confusion — confusing value disagreements with
factual ones or vice versa. When a disagreement is actually about
values but is argued as if it's about facts, no amount of evidence
will resolve it. Conversely, treating factual disputes as value
disputes prevents resolution through evidence.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

VALUE_FACTUAL_SYSTEM = """You are a value-factual confusion specialist. Given a disagreement, assess whether it confuses value disagreements with factual ones:

Key concepts:
- Value disagreement: about what SHOULD be (normative)
- Factual disagreement: about what IS (empirical)
- Is-ought problem: can't derive values from facts alone (Hume)
- Disguised values: value claims dressed up as factual claims
- Disguised facts: factual claims treated as if they're value claims
- Resolution mismatch: using evidence for value disputes or authority for factual ones
- Operationalization: making the disagreement type explicit

When value-factual confusion IS present:
- A value disagreement is argued with evidence as if it's factual
- A factual disagreement is treated as irresolvable "difference of opinion"
- "Studies show X" used to argue for a value conclusion
- "That's just your opinion" applied to empirically testable claims
- The disagreement would persist regardless of what evidence showed
- Facts are cited but the real disagreement is about priorities
- Neither party has identified whether the dispute is factual or normative

When the disagreement type IS clear:
- Both parties agree on whether they're disputing facts or values
- Factual disputes are addressed with evidence
- Value disputes are addressed through value clarification
- The is-ought distinction is respected
- Evidence is relevant to the factual components
- Value components are acknowledged as such
- The resolution strategy matches the disagreement type

Output JSON with: value_factual_confusion_present (bool), severity (none/mild/moderate/severe), disagreement (what is disagreed about), apparent_type (what type it appears to be), actual_type (what type it actually is), confusion_direction (values_as_facts/facts_as_values/mixed), resolution_mismatch (how resolution strategy is mismatched), recommendation (type_clear/mild_confusion/significant_value_factual_confusion/major_type_mismatch/clarify_disagreement_type)."""

VALUE_FACTUAL_PROMPT = """Detect value-factual confusion:

Disagreement: {disagreement}
Arguments used: {arguments}
Evidence cited: {evidence}
Resolution attempts: {resolution}
Domain: {domain}
Context: {context}

Is this disagreement confusing value disputes with factual ones? Return ONLY valid JSON."""


class ValueFactualConfusionService:
    """Detects value-factual confusion — confusing value and factual disagreements."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        disagreement: str,
        *,
        arguments: str = "",
        evidence: str = "",
        resolution: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect value-factual confusion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=VALUE_FACTUAL_PROMPT.format(
                disagreement=disagreement,
                arguments=arguments or "Not specified",
                evidence=evidence or "Not specified",
                resolution=resolution or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=VALUE_FACTUAL_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "disagreement": disagreement[:200],
            "value_factual_confusion_present": data.get("value_factual_confusion_present", False),
            "severity": data.get("severity", ""),
            "apparent_type": data.get("apparent_type", ""),
            "actual_type": data.get("actual_type", ""),
            "confusion_direction": data.get("confusion_direction", ""),
            "recommendation": data.get("recommendation", ""),
        }
