"""EpistemicExposureDreadService — Epistemic Exposure Dread Detection.

Detects epistemic exposure dread — terror of intellectual inadequacy being
seen by others, leading to avoidance of intellectual visibility.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_EXPOSURE_DREAD_SYSTEM = """You are an epistemic exposure dread specialist. Given terror of inadequacy being seen, assess exposure dread:

Key concepts:
- Epistemic exposure dread: terror of inadequacy being seen
- Visibility avoidance: refusing to be intellectually visible
- Spotlight fear: panic when intellectual attention directed
- Judgment anticipation: expecting harsh evaluation
- Vulnerability terror: being seen means being destroyed
- Performance anxiety: freezing when observed thinking
- Concealment compulsion: must hide intellectual self

When epistemic exposure dread IS present:
- Terror of inadequacy seen
- Refusing visibility
- Panic at attention
- Expecting harsh judgment
- Being seen means destroyed
- Freezing when observed
- Must hide self

When no exposure dread:
- Comfortable being seen
- Willing to be visible
- Calm with attention
- Expecting fair evaluation
- Being seen is safe
- Performing naturally
- Sharing openly

Output JSON with: exposure_dread_detected (bool), severity (none/mild/moderate/severe), visibility_avoidance (what refusing), spotlight_fear (what panicking at), judgment_anticipation (what expecting), concealment_compulsion (what hiding), recommendation (no_exposure_dread/mild_visibility_practice/significant_exposure_therapy/major_intensive_shame_work/emergency_severe_avoidance)."""

EPISTEMIC_EXPOSURE_DREAD_PROMPT = """Detect epistemic exposure dread:

Visibility avoidance: {visibility_avoidance}
Spotlight fear: {spotlight_fear}
Judgment anticipation: {judgment_anticipation}
Concealment compulsion: {concealment_compulsion}
Domain: {domain}
Context: {context}

Is there terror of intellectual inadequacy being seen by others? Return ONLY valid JSON."""


class EpistemicExposureDreadService:
    """Detects epistemic exposure dread — terror of inadequacy being seen."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        visibility_avoidance: str,
        *,
        spotlight_fear: str = "",
        judgment_anticipation: str = "",
        concealment_compulsion: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic exposure dread."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_EXPOSURE_DREAD_PROMPT.format(
                visibility_avoidance=visibility_avoidance,
                spotlight_fear=spotlight_fear or "Not specified",
                judgment_anticipation=judgment_anticipation or "Not specified",
                concealment_compulsion=concealment_compulsion or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_EXPOSURE_DREAD_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "visibility_avoidance": visibility_avoidance[:200],
            "exposure_dread_detected": data.get("exposure_dread_detected", False),
            "severity": data.get("severity", ""),
            "spotlight_fear": data.get("spotlight_fear", ""),
            "judgment_anticipation": data.get("judgment_anticipation", ""),
            "concealment_compulsion": data.get("concealment_compulsion", ""),
            "recommendation": data.get("recommendation", ""),
        }
