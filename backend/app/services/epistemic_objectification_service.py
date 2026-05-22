"""EpistemicObjectificationService — Epistemic Objectification Detection.

Detects epistemic objectification — treating knowers as objects of
study rather than subjects with knowledge, where people are studied
rather than consulted.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_OBJECTIFICATION_SYSTEM = """You are an epistemic objectification specialist. Given a knowledge production context, assess whether knowers are being treated as objects rather than subjects:

Key concepts:
- Epistemic objectification: knowers treated as objects of study
- Subject-object inversion: those with knowledge treated as data
- Extractive epistemology: knowledge extracted not co-produced
- Studied not consulted: people studied rather than asked
- Agency denial: epistemic agency of knowers denied
- Knowledge extraction: taking knowledge without partnership
- Objectifying gaze: treating knowers as specimens

When epistemic objectification IS present:
- People with knowledge treated as objects of study
- Knowledge extracted rather than co-produced
- Those studied not consulted as knowers
- Epistemic agency of subjects denied
- Knowledge taken without partnership or credit
- People treated as data sources not knowledge holders
- Objectifying approach to those with relevant knowledge

When appropriate study is present:
- Subjects recognized as knowers
- Knowledge co-produced with participants
- Those studied also consulted
- Epistemic agency respected
- Knowledge shared with partnership
- People treated as collaborators
- Respectful approach to knowledge holders

Output JSON with: objectification_present (bool), severity (none/mild/moderate/severe), context (what knowledge context), objectified (who is objectified), treatment (how they are treated), agency_denied (what agency is denied), recommendation (respectful_inquiry/mild_objectification/significant_epistemic_objectification/major_agency_denial/recognize_subjects_as_knowers)."""

EPISTEMIC_OBJECTIFICATION_PROMPT = """Detect epistemic objectification:

Knowledge context: {knowledge_context}
Treatment of subjects: {treatment}
Agency recognized: {agency}
Partnership level: {partnership}
Domain: {domain}
Context: {context}

Are knowers being treated as objects of study rather than subjects with knowledge? Return ONLY valid JSON."""


class EpistemicObjectificationService:
    """Detects epistemic objectification — knowers treated as objects not subjects."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        knowledge_context: str,
        *,
        treatment: str = "",
        agency: str = "",
        partnership: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic objectification."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_OBJECTIFICATION_PROMPT.format(
                knowledge_context=knowledge_context,
                treatment=treatment or "Not specified",
                agency=agency or "Not specified",
                partnership=partnership or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_OBJECTIFICATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "knowledge_context": knowledge_context[:200],
            "objectification_present": data.get("objectification_present", False),
            "severity": data.get("severity", ""),
            "objectified": data.get("objectified", ""),
            "treatment": data.get("treatment", ""),
            "agency_denied": data.get("agency_denied", ""),
            "recommendation": data.get("recommendation", ""),
        }
