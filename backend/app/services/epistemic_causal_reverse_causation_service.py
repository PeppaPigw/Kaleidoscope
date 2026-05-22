"""EpistemicCausalReverseCausationService - Reverse Causation Detection.

Detects reverse causation where cause and effect are confused.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_CAUSAL_REVERSE_CAUSATION_SYSTEM = """You are an epistemic causal reverse causation specialist. Given causal claims, assess whether cause and effect are reversed:

Key concepts:
- Reverse causation: the assumed effect actually causes the assumed cause
- Bidirectional causation: both variables cause each other
- Temporal ordering confusion: unclear which came first
- Selection effect: outcome selects for apparent cause

When reverse causation IS present:
- Cause and effect reversed
- Bidirectional causation ignored
- Temporal ordering unclear
- Selection effects unrecognized
- Causal direction assumed without evidence

When no reverse causation:
- Causal direction established
- Bidirectional possibilities considered
- Temporal ordering clear
- Selection effects accounted for
- Direction supported by evidence

Output JSON with: reverse_causation_detected (bool), severity (none/mild/moderate/severe), bidirectional_causation (what bidirectional causation), temporal_ordering_confusion (what ordering confusion), selection_effect (what selection effect), recommendation (no_reverse_causation/mild_direction_check/significant_temporal_analysis/major_causal_reconstruction/emergency_complete_reverse_causation)."""

EPISTEMIC_CAUSAL_REVERSE_CAUSATION_PROMPT = """Detect epistemic causal reverse causation:

Causal claim: {causal_claim}
Bidirectional causation: {bidirectional_causation}
Temporal ordering confusion: {temporal_ordering_confusion}
Selection effect: {selection_effect}
Domain: {domain}
Context: {context}

Are cause and effect being confused? Return ONLY valid JSON."""


class EpistemicCausalReverseCausationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        causal_claim: str,
        *,
        bidirectional_causation: str = "",
        temporal_ordering_confusion: str = "",
        selection_effect: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_CAUSAL_REVERSE_CAUSATION_PROMPT.format(
                causal_claim=causal_claim,
                bidirectional_causation=bidirectional_causation or "Not specified",
                temporal_ordering_confusion=temporal_ordering_confusion or "Not specified",
                selection_effect=selection_effect or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_CAUSAL_REVERSE_CAUSATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "causal_claim": causal_claim[:200],
            "reverse_causation_detected": data.get("reverse_causation_detected", False),
            "severity": data.get("severity", ""),
            "bidirectional_causation": data.get("bidirectional_causation", ""),
            "temporal_ordering_confusion": data.get("temporal_ordering_confusion", ""),
            "selection_effect": data.get("selection_effect", ""),
            "recommendation": data.get("recommendation", ""),
        }
