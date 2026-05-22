"""EpistemicFibromyalgiaService — Epistemic Fibromyalgia Detection.

Detects epistemic fibromyalgia — widespread intellectual pain without
identifiable structural cause, with amplified pain processing.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_FIBROMYALGIA_SYSTEM = """You are an epistemic fibromyalgia specialist. Given widespread intellectual pain without structural cause, assess fibromyalgia:

Key concepts:
- Epistemic fibromyalgia: widespread pain without structural cause
- Central sensitization: pain processing amplified
- Tender points: specific locations of heightened sensitivity
- Fatigue: exhaustion disproportionate to activity
- Cognitive fog: difficulty with intellectual clarity
- Sleep disruption: restorative processes failing
- Multimodal treatment: addressing multiple pathways

When epistemic fibromyalgia IS present:
- Widespread pain without structural cause
- Pain processing amplified centrally
- Specific locations of heightened sensitivity
- Exhaustion disproportionate to activity
- Difficulty with intellectual clarity
- Restorative processes failing
- Multiple pathways need addressing

When no fibromyalgia:
- No widespread unexplained pain
- Normal pain processing
- No heightened sensitivity points
- Proportionate energy levels
- Clear intellectual function
- Normal restorative processes
- No multimodal treatment needed

Output JSON with: fibromyalgia_detected (bool), severity (none/mild/moderate/severe), pain_distribution (what widespread pattern), sensitization_level (what amplification), fatigue_status (what exhaustion), cognitive_fog (what clarity loss), recommendation (no_fibromyalgia/mild_exercise/significant_multimodal/major_pharmacological/emergency_functional_crisis)."""

EPISTEMIC_FIBROMYALGIA_PROMPT = """Detect epistemic fibromyalgia:

Pain distribution: {pain_distribution}
Sensitization level: {sensitization_level}
Fatigue status: {fatigue_status}
Cognitive fog: {cognitive_fog}
Domain: {domain}
Context: {context}

Is there widespread intellectual pain without structural cause with amplified processing? Return ONLY valid JSON."""


class EpistemicFibromyalgiaService:
    """Detects epistemic fibromyalgia — widespread pain without structural cause."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        pain_distribution: str,
        *,
        sensitization_level: str = "",
        fatigue_status: str = "",
        cognitive_fog: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic fibromyalgia."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_FIBROMYALGIA_PROMPT.format(
                pain_distribution=pain_distribution,
                sensitization_level=sensitization_level or "Not specified",
                fatigue_status=fatigue_status or "Not specified",
                cognitive_fog=cognitive_fog or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_FIBROMYALGIA_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "pain_distribution": pain_distribution[:200],
            "fibromyalgia_detected": data.get("fibromyalgia_detected", False),
            "severity": data.get("severity", ""),
            "sensitization_level": data.get("sensitization_level", ""),
            "fatigue_status": data.get("fatigue_status", ""),
            "cognitive_fog": data.get("cognitive_fog", ""),
            "recommendation": data.get("recommendation", ""),
        }
