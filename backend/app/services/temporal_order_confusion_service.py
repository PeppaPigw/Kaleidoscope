"""TemporalOrderConfusionService — Temporal Order Confusion Detection.

Detects temporal order confusion — confusing temporal sequence
with causal order, or misattributing causation based on the
order in which events were observed or reported.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

TEMPORAL_ORDER_CONFUSION_SYSTEM = """You are a temporal order confusion specialist. Given an argument, assess whether temporal sequence is being confused with causal order:

Key concepts:
- Post hoc ergo propter hoc: after therefore because of
- Temporal precedence: earlier events assumed to cause later ones
- Reverse causation: effect mistaken for cause due to timing
- Confounding temporal variables: third factor causing both
- Reporting order vs occurrence order: when learned vs when happened
- Simultaneity: events appearing sequential due to measurement
- Temporal aggregation: grouping obscuring true sequence

When temporal order confusion IS present:
- Sequence alone used as evidence of causation
- Earlier event assumed to cause later without mechanism
- Reverse causation not considered
- Reporting order confused with occurrence order
- Temporal coincidence treated as causal link
- No mechanism connecting temporal sequence to causation
- Alternative temporal explanations not explored

When temporal reasoning is sound:
- Temporal sequence combined with mechanism
- Reverse causation explicitly ruled out
- Confounders considered
- Reporting vs occurrence order distinguished
- Temporal evidence combined with other evidence types
- Alternative temporal explanations examined
- Appropriate caution about sequence-causation inference

Output JSON with: confusion_present (bool), severity (none/mild/moderate/severe), sequence (what temporal sequence is cited), causal_claim (what causation is inferred), alternative_order (what other temporal explanations exist), mechanism (whether causal mechanism is identified), recommendation (sound_temporal_reasoning/mild_sequence_bias/significant_order_confusion/major_post_hoc_error/establish_mechanism)."""

TEMPORAL_ORDER_CONFUSION_PROMPT = """Detect temporal order confusion:

Argument: {argument}
Sequence cited: {sequence}
Causal claim: {causal_claim}
Alternative explanations: {alternatives}
Domain: {domain}
Context: {context}

Is temporal sequence being confused with causal order? Return ONLY valid JSON."""


class TemporalOrderConfusionService:
    """Detects temporal order confusion — sequence mistaken for causation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        argument: str,
        *,
        sequence: str = "",
        causal_claim: str = "",
        alternatives: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect temporal order confusion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=TEMPORAL_ORDER_CONFUSION_PROMPT.format(
                argument=argument,
                sequence=sequence or "Not specified",
                causal_claim=causal_claim or "Not specified",
                alternatives=alternatives or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=TEMPORAL_ORDER_CONFUSION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "argument": argument[:200],
            "confusion_present": data.get("confusion_present", False),
            "severity": data.get("severity", ""),
            "sequence": data.get("sequence", ""),
            "causal_claim": data.get("causal_claim", ""),
            "alternative_order": data.get("alternative_order", ""),
            "recommendation": data.get("recommendation", ""),
        }
