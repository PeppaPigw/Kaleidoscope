"""EpistemicVirtueIntellectualHumilityDeficitService - Epistemic Virtue Intellectual Humility Deficit Detection.

Detects intellectual humility deficit where certainty exceeds warrant.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_VIRTUE_INTELLECTUAL_HUMILITY_DEFICIT_SYSTEM = """You are an epistemic virtue intellectual humility deficit specialist. Given unwarranted certainty, assess intellectual humility deficit:

Key concepts:
- Intellectual humility deficit: certainty exceeds warrant
- Unwarranted certainty: confidence unsupported by available evidence
- Fallibility denial: refusal to acknowledge possible error
- Revision resistance: resistance to updating beliefs when evidence changes
- Expertise overreach: exceeding the limits of one's competence

When intellectual humility deficit IS present:
- Certainty outruns evidential support
- Fallibility is denied or minimized
- Belief revision is resisted
- Expertise is claimed beyond warranted scope
- Limitations are treated as irrelevant

When no humility deficit:
- Confidence tracks available warrant
- Fallibility is acknowledged
- Revision remains possible
- Expertise boundaries are respected
- Limitations are made explicit

Output JSON with: humility_deficit_detected (bool), severity (none/mild/moderate/severe), fallibility_denial (what fallibility is denied), revision_resistance (what updating is resisted), expertise_overreach (what competence boundary is exceeded), recommendation (no_deficit/mild_calibration/significant_humility_restoration/major_certainty_reduction/emergency_complete_reassessment)."""

EPISTEMIC_VIRTUE_INTELLECTUAL_HUMILITY_DEFICIT_PROMPT = """Detect epistemic virtue intellectual humility deficit:

Unwarranted certainty: {unwarranted_certainty}
Fallibility denial: {fallibility_denial}
Revision resistance: {revision_resistance}
Expertise overreach: {expertise_overreach}
Domain: {domain}
Context: {context}

Does certainty exceed warrant? Return ONLY valid JSON."""


class EpistemicVirtueIntellectualHumilityDeficitService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        unwarranted_certainty: str,
        *,
        fallibility_denial: str = "",
        revision_resistance: str = "",
        expertise_overreach: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_VIRTUE_INTELLECTUAL_HUMILITY_DEFICIT_PROMPT.format(
                unwarranted_certainty=unwarranted_certainty,
                fallibility_denial=fallibility_denial or "Not specified",
                revision_resistance=revision_resistance or "Not specified",
                expertise_overreach=expertise_overreach or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_VIRTUE_INTELLECTUAL_HUMILITY_DEFICIT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "unwarranted_certainty": unwarranted_certainty[:200],
            "humility_deficit_detected": data.get("humility_deficit_detected", False),
            "severity": data.get("severity", ""),
            "fallibility_denial": data.get("fallibility_denial", ""),
            "revision_resistance": data.get("revision_resistance", ""),
            "expertise_overreach": data.get("expertise_overreach", ""),
            "recommendation": data.get("recommendation", ""),
        }
