"""EpistemicReverseCausationService — Epistemic Reverse Causation Detection.

Detects epistemic reverse causation — confusing the direction of
cause and effect, mistaking effect for cause.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_REVERSE_CAUSATION_SYSTEM = """You are an epistemic reverse causation specialist. Given confusion about causal direction, assess reverse causation:

Key concepts:
- Epistemic reverse causation: confusing cause and effect direction
- Direction confusion: getting causal arrow backwards
- Effect-as-cause: treating effect as if it were the cause
- Temporal confusion: confusing temporal order with causal order
- Bidirectional blindness: missing bidirectional causation
- Selection effect: confusing selection with causation
- Symptom-cause confusion: treating symptoms as causes

When epistemic reverse causation IS present:
- Causal direction confused
- Arrow backwards
- Effect treated as cause
- Temporal order confused
- Bidirectionality missed
- Selection confused with causation
- Symptoms treated as causes

When no reverse causation:
- Causal direction clear
- Arrow correct
- Cause and effect distinguished
- Temporal order respected
- Bidirectionality considered
- Selection effects recognized
- Symptoms distinguished from causes

Output JSON with: reverse_causation_detected (bool), severity (none/mild/moderate/severe), direction_confusion (what direction confused), effect_as_cause (what effect treated as cause), temporal_confusion (what temporal order confused), selection_effect (what selection confused), recommendation (no_reverse_causation/mild_direction_checking/significant_causal_analysis/major_intensive_direction_correction/emergency_complete_reverse_causation)."""

EPISTEMIC_REVERSE_CAUSATION_PROMPT = """Detect epistemic reverse causation:

Direction confusion: {direction_confusion}
Effect as cause: {effect_as_cause}
Temporal confusion: {temporal_confusion}
Selection effect: {selection_effect}
Domain: {domain}
Context: {context}

Is the direction of cause and effect being confused? Return ONLY valid JSON."""


class EpistemicReverseCausationService:
    """Detects epistemic reverse causation — causal arrow backwards."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        direction_confusion: str,
        *,
        effect_as_cause: str = "",
        temporal_confusion: str = "",
        selection_effect: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic reverse causation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_REVERSE_CAUSATION_PROMPT.format(
                direction_confusion=direction_confusion,
                effect_as_cause=effect_as_cause or "Not specified",
                temporal_confusion=temporal_confusion or "Not specified",
                selection_effect=selection_effect or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_REVERSE_CAUSATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "direction_confusion": direction_confusion[:200],
            "reverse_causation_detected": data.get("reverse_causation_detected", False),
            "severity": data.get("severity", ""),
            "effect_as_cause": data.get("effect_as_cause", ""),
            "temporal_confusion": data.get("temporal_confusion", ""),
            "selection_effect": data.get("selection_effect", ""),
            "recommendation": data.get("recommendation", ""),
        }
