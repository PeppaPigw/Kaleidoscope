"""EpistemicTemporalOrderFallacyService — Epistemic Temporal Order Fallacy Detection.

Detects epistemic temporal order fallacy — assuming temporal order implies
causal order, confusing sequence with causation.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_TEMPORAL_ORDER_FALLACY_SYSTEM = """You are an epistemic temporal order fallacy specialist. Given assumed causation from sequence, assess temporal order fallacy:

Key concepts:
- Epistemic temporal order fallacy: assuming sequence implies causation
- Post hoc reasoning: because B followed A, A caused B
- Coincidental sequence: coincidental temporal proximity mistaken for causation
- Confounding timeline: third factor causing both in sequence
- Reverse temporal causation: effect actually preceding cause through anticipation
- Temporal proximity bias: closer in time assumed more causally related
- Narrative sequencing: imposing causal narrative on temporal sequence

When epistemic temporal order fallacy IS present:
- Sequence assumed as causation
- Post hoc reasoning applied
- Coincidental proximity mistaken
- Confounders ignored
- Reverse causation missed
- Temporal proximity overweighted
- Narrative imposed on sequence

When no temporal order fallacy:
- Sequence distinguished from causation
- Mechanisms identified
- Coincidence considered
- Confounders checked
- Direction verified
- Proximity not overweighted
- Narrative tested against evidence

Output JSON with: temporal_order_fallacy_detected (bool), severity (none/mild/moderate/severe), post_hoc_reasoning (what post hoc reasoning), coincidental_sequence (what coincidental sequences), confounding_timeline (what confounders missed), reverse_causation (what reverse causation missed), recommendation (no_temporal_order_fallacy/mild_sequence_awareness/significant_mechanism_requirement/major_intensive_causal_verification/emergency_complete_temporal_order_fallacy)."""

EPISTEMIC_TEMPORAL_ORDER_FALLACY_PROMPT = """Detect epistemic temporal order fallacy:

Post hoc reasoning: {post_hoc_reasoning}
Coincidental sequence: {coincidental_sequence}
Confounding timeline: {confounding_timeline}
Reverse causation: {reverse_causation}
Domain: {domain}
Context: {context}

Is temporal order being confused with causal order? Return ONLY valid JSON."""


class EpistemicTemporalOrderFallacyService:
    """Detects epistemic temporal order fallacy — sequence as causation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        post_hoc_reasoning: str,
        *,
        coincidental_sequence: str = "",
        confounding_timeline: str = "",
        reverse_causation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic temporal order fallacy."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_TEMPORAL_ORDER_FALLACY_PROMPT.format(
                post_hoc_reasoning=post_hoc_reasoning,
                coincidental_sequence=coincidental_sequence or "Not specified",
                confounding_timeline=confounding_timeline or "Not specified",
                reverse_causation=reverse_causation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_TEMPORAL_ORDER_FALLACY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "post_hoc_reasoning": post_hoc_reasoning[:200],
            "temporal_order_fallacy_detected": data.get("temporal_order_fallacy_detected", False),
            "severity": data.get("severity", ""),
            "coincidental_sequence": data.get("coincidental_sequence", ""),
            "confounding_timeline": data.get("confounding_timeline", ""),
            "reverse_causation": data.get("reverse_causation", ""),
            "recommendation": data.get("recommendation", ""),
        }
