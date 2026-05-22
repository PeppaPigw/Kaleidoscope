"""EpistemicCognitiveOverloadService — Epistemic Cognitive Overload Detection.

Detects epistemic cognitive overload — too much information overwhelming
processing capacity and degrading epistemic quality.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_COGNITIVE_OVERLOAD_SYSTEM = """You are an epistemic cognitive overload specialist. Given information overwhelming processing capacity, assess cognitive overload:

Key concepts:
- Epistemic cognitive overload: too much information overwhelming processing
- Information saturation: saturated with more info than can process
- Decision fatigue: too many decisions degrading quality
- Attention fragmentation: attention split across too many inputs
- Processing bottleneck: more input than processing capacity
- Comprehension collapse: understanding collapsing under volume
- Priority confusion: unable to prioritize under information flood

When epistemic cognitive overload IS present:
- Information overwhelming capacity
- Saturated beyond processing
- Decisions degraded by fatigue
- Attention fragmented
- Processing bottlenecked
- Comprehension collapsing
- Priorities confused

When no cognitive overload:
- Information manageable
- Processing capacity adequate
- Decisions made with clarity
- Attention focused
- Processing flowing
- Comprehension maintained
- Priorities clear

Output JSON with: cognitive_overload_detected (bool), severity (none/mild/moderate/severe), information_saturation (what saturated with), decision_fatigue (what decisions degraded), attention_fragmentation (what fragmenting attention), processing_bottleneck (what bottlenecking processing), recommendation (no_cognitive_overload/mild_information_triage/significant_load_reduction/major_intensive_simplification/emergency_complete_cognitive_overload)."""

EPISTEMIC_COGNITIVE_OVERLOAD_PROMPT = """Detect epistemic cognitive overload:

Information saturation: {information_saturation}
Decision fatigue: {decision_fatigue}
Attention fragmentation: {attention_fragmentation}
Processing bottleneck: {processing_bottleneck}
Domain: {domain}
Context: {context}

Is too much information overwhelming processing capacity? Return ONLY valid JSON."""


class EpistemicCognitiveOverloadService:
    """Detects epistemic cognitive overload — information overwhelming processing."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        information_saturation: str,
        *,
        decision_fatigue: str = "",
        attention_fragmentation: str = "",
        processing_bottleneck: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic cognitive overload."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_COGNITIVE_OVERLOAD_PROMPT.format(
                information_saturation=information_saturation,
                decision_fatigue=decision_fatigue or "Not specified",
                attention_fragmentation=attention_fragmentation or "Not specified",
                processing_bottleneck=processing_bottleneck or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_COGNITIVE_OVERLOAD_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "information_saturation": information_saturation[:200],
            "cognitive_overload_detected": data.get("cognitive_overload_detected", False),
            "severity": data.get("severity", ""),
            "decision_fatigue": data.get("decision_fatigue", ""),
            "attention_fragmentation": data.get("attention_fragmentation", ""),
            "processing_bottleneck": data.get("processing_bottleneck", ""),
            "recommendation": data.get("recommendation", ""),
        }
