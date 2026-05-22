"""EpistemicMemoryIdealizationService — Epistemic Memory Idealization Detection.

Detects epistemic memory idealization — idealizing past intellectual
states or positions as better than they actually were.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_MEMORY_IDEALIZATION_SYSTEM = """You are an epistemic memory idealization specialist. Given idealizing past intellectual states, assess memory idealization:

Key concepts:
- Epistemic memory idealization: idealizing past intellectual states
- Golden age thinking: believing past thinking was better than it was
- Nostalgia distortion: nostalgia distorting memory of past positions
- Past self inflation: inflating past intellectual self
- Former clarity illusion: illusion that one was clearer in the past
- Decline narrative: narrative of intellectual decline from idealized past
- Selective past glorification: glorifying selected past moments

When epistemic memory idealization IS present:
- Idealizing past states
- Believing past was better
- Nostalgia distorting memory
- Inflating past self
- Illusion of former clarity
- Narrative of decline
- Glorifying selected past

When no memory idealization:
- Accurate past assessment
- Realistic about past
- Undistorted by nostalgia
- Accurate past self
- Honest about former clarity
- No decline narrative
- Balanced past view

Output JSON with: memory_idealization_detected (bool), severity (none/mild/moderate/severe), golden_age_thinking (what past thinking idealized), nostalgia_distortion (what nostalgia distorting), past_self_inflation (what past self inflated about), decline_narrative (what decline narrative about), recommendation (no_memory_idealization/mild_reality_check/significant_honest_assessment/major_intensive_past_accuracy/emergency_complete_idealization)."""

EPISTEMIC_MEMORY_IDEALIZATION_PROMPT = """Detect epistemic memory idealization:

Golden age thinking: {golden_age_thinking}
Nostalgia distortion: {nostalgia_distortion}
Past self inflation: {past_self_inflation}
Decline narrative: {decline_narrative}
Domain: {domain}
Context: {context}

Is there idealizing past intellectual states or positions? Return ONLY valid JSON."""


class EpistemicMemoryIdealizationService:
    """Detects epistemic memory idealization — idealizing past intellectual states."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        golden_age_thinking: str,
        *,
        nostalgia_distortion: str = "",
        past_self_inflation: str = "",
        decline_narrative: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic memory idealization."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_MEMORY_IDEALIZATION_PROMPT.format(
                golden_age_thinking=golden_age_thinking,
                nostalgia_distortion=nostalgia_distortion or "Not specified",
                past_self_inflation=past_self_inflation or "Not specified",
                decline_narrative=decline_narrative or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_MEMORY_IDEALIZATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "golden_age_thinking": golden_age_thinking[:200],
            "memory_idealization_detected": data.get("memory_idealization_detected", False),
            "severity": data.get("severity", ""),
            "nostalgia_distortion": data.get("nostalgia_distortion", ""),
            "past_self_inflation": data.get("past_self_inflation", ""),
            "decline_narrative": data.get("decline_narrative", ""),
            "recommendation": data.get("recommendation", ""),
        }
