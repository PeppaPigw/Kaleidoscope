"""EpistemicSpeechTherapyService — Epistemic Speech Therapy Detection.

Detects need for epistemic speech therapy — restoring intellectual
communication capacity after damage to expression systems.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SPEECH_THERAPY_SYSTEM = """You are an epistemic speech therapy specialist. Given intellectual communication limitations, assess whether expression restoration is needed:

Key concepts:
- Epistemic speech therapy: restoring intellectual communication capacity
- Aphasia: loss of intellectual language ability
- Dysarthria: impaired intellectual articulation
- Apraxia: inability to plan intellectual expression
- Fluency: smoothness of intellectual output
- Comprehension: understanding intellectual input
- Pragmatics: appropriate use of intellectual communication

When epistemic speech therapy IS needed:
- Impaired intellectual communication capacity
- Loss of intellectual language ability
- Impaired intellectual articulation
- Inability to plan intellectual expression
- Disrupted smoothness of output
- Impaired understanding of input
- Inappropriate communication patterns

When no therapy needed:
- Full communication capacity
- Complete language ability
- Clear articulation
- Smooth expression planning
- Fluent output
- Full comprehension
- Appropriate pragmatics

Output JSON with: speech_therapy_needed (bool), severity (none/mild/moderate/severe), aphasia (what language loss), dysarthria (what articulation impairment), apraxia (what planning inability), fluency_disruption (what output disruption), recommendation (no_therapy_needed/mild_therapy/significant_rehabilitation/major_communication_restoration/comprehensive_intellectual_expression_program)."""

EPISTEMIC_SPEECH_THERAPY_PROMPT = """Detect epistemic speech therapy need:

Aphasia: {aphasia}
Dysarthria: {dysarthria}
Apraxia: {apraxia}
Fluency disruption: {fluency_disruption}
Domain: {domain}
Context: {context}

Is restoration of intellectual communication capacity needed? Return ONLY valid JSON."""


class EpistemicSpeechTherapyService:
    """Detects epistemic speech therapy need — intellectual communication restoration."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        aphasia: str,
        *,
        dysarthria: str = "",
        apraxia: str = "",
        fluency_disruption: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic speech therapy need."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SPEECH_THERAPY_PROMPT.format(
                aphasia=aphasia,
                dysarthria=dysarthria or "Not specified",
                apraxia=apraxia or "Not specified",
                fluency_disruption=fluency_disruption or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SPEECH_THERAPY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "aphasia": aphasia[:200],
            "speech_therapy_needed": data.get("speech_therapy_needed", False),
            "severity": data.get("severity", ""),
            "dysarthria": data.get("dysarthria", ""),
            "apraxia": data.get("apraxia", ""),
            "fluency_disruption": data.get("fluency_disruption", ""),
            "recommendation": data.get("recommendation", ""),
        }
