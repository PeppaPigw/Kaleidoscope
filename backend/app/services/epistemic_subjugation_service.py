"""EpistemicSubjugationService — Epistemic Subjugation Detection.

Detects epistemic subjugation — internalized acceptance of intellectual
inferiority imposed by dominant epistemic authority.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SUBJUGATION_SYSTEM = """You are an epistemic subjugation specialist. Given internalized intellectual inferiority, assess subjugation:

Key concepts:
- Epistemic subjugation: internalized acceptance of inferiority
- Self-silencing: not speaking because believe unworthy
- Deference pattern: always yielding to authority
- Internalized oppression: believing own inferiority
- Voice suppression: own perspective doesn't matter
- Learned submission: trained to accept subordination
- Intellectual servitude: existing to serve others' knowledge

When epistemic subjugation IS present:
- Internalized inferiority
- Not speaking due to unworthiness
- Always yielding to authority
- Believing own inferiority
- Own perspective doesn't matter
- Trained to accept subordination
- Existing to serve others

When no subjugation:
- Intellectual equality
- Speaking freely
- Appropriate deference
- Believing own worth
- Perspective valued
- Autonomous engagement
- Mutual knowledge exchange

Output JSON with: subjugation_detected (bool), severity (none/mild/moderate/severe), self_silencing (what not speaking), deference_pattern (what yielding), internalized_oppression (what believing inferior), voice_suppression (what doesn't matter), recommendation (no_subjugation/mild_voice_recovery/significant_empowerment_therapy/major_intensive_liberation/emergency_complete_submission)."""

EPISTEMIC_SUBJUGATION_PROMPT = """Detect epistemic subjugation:

Self silencing: {self_silencing}
Deference pattern: {deference_pattern}
Internalized oppression: {internalized_oppression}
Voice suppression: {voice_suppression}
Domain: {domain}
Context: {context}

Is there internalized acceptance of intellectual inferiority imposed by authority? Return ONLY valid JSON."""


class EpistemicSubjugationService:
    """Detects epistemic subjugation — internalized intellectual inferiority."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        self_silencing: str,
        *,
        deference_pattern: str = "",
        internalized_oppression: str = "",
        voice_suppression: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic subjugation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SUBJUGATION_PROMPT.format(
                self_silencing=self_silencing,
                deference_pattern=deference_pattern or "Not specified",
                internalized_oppression=internalized_oppression or "Not specified",
                voice_suppression=voice_suppression or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SUBJUGATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "self_silencing": self_silencing[:200],
            "subjugation_detected": data.get("subjugation_detected", False),
            "severity": data.get("severity", ""),
            "deference_pattern": data.get("deference_pattern", ""),
            "internalized_oppression": data.get("internalized_oppression", ""),
            "voice_suppression": data.get("voice_suppression", ""),
            "recommendation": data.get("recommendation", ""),
        }
