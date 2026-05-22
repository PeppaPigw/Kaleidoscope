"""EpistemicIrritableBowelService — Epistemic Irritable Bowel Detection.

Detects epistemic irritable bowel — functional disorder where intellectual
processing alternates between too fast and too slow without structural cause.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_IRRITABLE_BOWEL_SYSTEM = """You are an epistemic irritable bowel specialist. Given functional intellectual processing disorder, assess IBS:

Key concepts:
- Epistemic IBS: processing alternates fast/slow without structural cause
- Diarrhea-predominant: processing too fast, incomplete absorption
- Constipation-predominant: processing too slow, excessive retention
- Mixed type: alternating between both extremes
- Visceral hypersensitivity: normal processing perceived as painful
- FODMAP: specific inputs triggering symptoms
- Gut-brain axis: bidirectional stress-processing connection

When epistemic IBS IS present:
- Processing alternating fast and slow
- No structural cause found
- Incomplete absorption from speed
- Excessive retention from slowness
- Normal processing perceived as painful
- Specific inputs triggering symptoms
- Stress-processing connection active

When no IBS:
- Consistent processing speed
- No functional disorder
- Normal absorption
- Normal retention
- Processing not painful
- No trigger sensitivity
- Normal stress-processing relationship

Output JSON with: ibs_detected (bool), severity (none/mild/moderate/severe), predominant_type (what pattern), trigger_sensitivity (what inputs), visceral_response (what pain perception), gut_brain_status (what stress connection), recommendation (no_ibs/mild_dietary/significant_antispasmodic/major_comprehensive_management/emergency_severe_flare)."""

EPISTEMIC_IRRITABLE_BOWEL_PROMPT = """Detect epistemic irritable bowel:

Predominant type: {predominant_type}
Trigger sensitivity: {trigger_sensitivity}
Visceral response: {visceral_response}
Gut-brain status: {gut_brain_status}
Domain: {domain}
Context: {context}

Is intellectual processing alternating between too fast and too slow without structural cause? Return ONLY valid JSON."""


class EpistemicIrritableBowelService:
    """Detects epistemic IBS — processing alternates fast/slow without cause."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        predominant_type: str,
        *,
        trigger_sensitivity: str = "",
        visceral_response: str = "",
        gut_brain_status: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic irritable bowel."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_IRRITABLE_BOWEL_PROMPT.format(
                predominant_type=predominant_type,
                trigger_sensitivity=trigger_sensitivity or "Not specified",
                visceral_response=visceral_response or "Not specified",
                gut_brain_status=gut_brain_status or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_IRRITABLE_BOWEL_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "predominant_type": predominant_type[:200],
            "ibs_detected": data.get("ibs_detected", False),
            "severity": data.get("severity", ""),
            "trigger_sensitivity": data.get("trigger_sensitivity", ""),
            "visceral_response": data.get("visceral_response", ""),
            "gut_brain_status": data.get("gut_brain_status", ""),
            "recommendation": data.get("recommendation", ""),
        }
