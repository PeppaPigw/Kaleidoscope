"""EpistemicMultipleSclerosisService — Epistemic Multiple Sclerosis Detection.

Detects epistemic multiple sclerosis — autoimmune demyelination of
intellectual nerve sheaths causing intermittent signal failure.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_MULTIPLE_SCLEROSIS_SYSTEM = """You are an epistemic MS specialist. Given autoimmune intellectual demyelination, assess MS:

Key concepts:
- Epistemic MS: autoimmune demyelination of nerve sheaths
- Relapsing-remitting: attacks followed by recovery
- Progressive: steady worsening without recovery
- Lesion: area of demyelination (plaque)
- Dissemination in time: attacks at different times
- Dissemination in space: lesions in different locations
- Disease-modifying therapy: slowing progression

When epistemic MS IS present:
- Autoimmune demyelination occurring
- Attacks followed by partial recovery
- Steady worsening between attacks
- Areas of demyelination present
- Attacks at different times
- Lesions in different locations
- Progression needs slowing

When no MS:
- No autoimmune demyelination
- No relapsing pattern
- No progressive worsening
- No demyelination areas
- No temporal dissemination
- No spatial dissemination
- No disease modification needed

Output JSON with: ms_detected (bool), severity (none/mild/moderate/severe), disease_course (what pattern), lesion_burden (what demyelination extent), relapse_rate (what attack frequency), disability_accumulation (what progressive loss), recommendation (no_ms/mild_monitoring/significant_first_line_dmt/major_escalation/emergency_acute_relapse)."""

EPISTEMIC_MULTIPLE_SCLEROSIS_PROMPT = """Detect epistemic multiple sclerosis:

Disease course: {disease_course}
Lesion burden: {lesion_burden}
Relapse rate: {relapse_rate}
Disability accumulation: {disability_accumulation}
Domain: {domain}
Context: {context}

Is there autoimmune demyelination of intellectual nerve sheaths causing intermittent signal failure? Return ONLY valid JSON."""


class EpistemicMultipleSclerosisService:
    """Detects epistemic MS — autoimmune demyelination causing signal failure."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        disease_course: str,
        *,
        lesion_burden: str = "",
        relapse_rate: str = "",
        disability_accumulation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic multiple sclerosis."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_MULTIPLE_SCLEROSIS_PROMPT.format(
                disease_course=disease_course,
                lesion_burden=lesion_burden or "Not specified",
                relapse_rate=relapse_rate or "Not specified",
                disability_accumulation=disability_accumulation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_MULTIPLE_SCLEROSIS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "disease_course": disease_course[:200],
            "ms_detected": data.get("ms_detected", False),
            "severity": data.get("severity", ""),
            "lesion_burden": data.get("lesion_burden", ""),
            "relapse_rate": data.get("relapse_rate", ""),
            "disability_accumulation": data.get("disability_accumulation", ""),
            "recommendation": data.get("recommendation", ""),
        }
