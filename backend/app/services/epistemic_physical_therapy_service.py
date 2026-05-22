"""EpistemicPhysicalTherapyService — Epistemic Physical Therapy Detection.

Detects need for epistemic physical therapy — structured exercises to
restore intellectual movement and range of motion after injury.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PHYSICAL_THERAPY_SYSTEM = """You are an epistemic physical therapy specialist. Given intellectual movement limitations, assess whether structured rehabilitation is needed:

Key concepts:
- Epistemic physical therapy: structured exercises for intellectual movement
- Range of motion: extent of intellectual flexibility
- Strengthening: building intellectual muscle
- Gait training: relearning intellectual walking patterns
- Modalities: heat, cold, electrical stimulation for healing
- Progressive loading: gradually increasing intellectual demands
- Functional goals: specific activities to restore

When epistemic physical therapy IS needed:
- Limited intellectual movement requiring exercises
- Reduced range of intellectual flexibility
- Weakened intellectual capacity needing strengthening
- Abnormal intellectual movement patterns
- Need for healing modalities
- Gradual increase in demands required
- Specific functional goals to achieve

When no therapy needed:
- Full intellectual movement
- Complete range of flexibility
- Full intellectual strength
- Normal movement patterns
- No healing modalities needed
- Can handle full demands
- All functional goals met

Output JSON with: physical_therapy_needed (bool), severity (none/mild/moderate/severe), range_of_motion (what flexibility limitation), strengthening_need (what weakness), gait_abnormality (what pattern problem), progressive_loading (what gradual increase), recommendation (no_therapy_needed/mild_therapy/significant_rehabilitation/major_intensive_therapy/structured_intellectual_exercise_program)."""

EPISTEMIC_PHYSICAL_THERAPY_PROMPT = """Detect epistemic physical therapy need:

Range of motion: {range_of_motion}
Strengthening need: {strengthening_need}
Gait abnormality: {gait_abnormality}
Progressive loading: {progressive_loading}
Domain: {domain}
Context: {context}

Are structured exercises needed to restore intellectual movement? Return ONLY valid JSON."""


class EpistemicPhysicalTherapyService:
    """Detects epistemic physical therapy need — intellectual movement restoration."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        range_of_motion: str,
        *,
        strengthening_need: str = "",
        gait_abnormality: str = "",
        progressive_loading: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic physical therapy need."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PHYSICAL_THERAPY_PROMPT.format(
                range_of_motion=range_of_motion,
                strengthening_need=strengthening_need or "Not specified",
                gait_abnormality=gait_abnormality or "Not specified",
                progressive_loading=progressive_loading or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PHYSICAL_THERAPY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "range_of_motion": range_of_motion[:200],
            "physical_therapy_needed": data.get("physical_therapy_needed", False),
            "severity": data.get("severity", ""),
            "strengthening_need": data.get("strengthening_need", ""),
            "gait_abnormality": data.get("gait_abnormality", ""),
            "progressive_loading": data.get("progressive_loading", ""),
            "recommendation": data.get("recommendation", ""),
        }
