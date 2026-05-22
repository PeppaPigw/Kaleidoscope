"""EpistemicExistentialDreadService — Epistemic Existential Dread Detection.

Detects epistemic existential dread — overwhelming anxiety about the
fundamental uncertainty and groundlessness of all intellectual knowledge.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_EXISTENTIAL_DREAD_SYSTEM = """You are an epistemic existential dread specialist. Given overwhelming intellectual uncertainty anxiety, assess existential dread:

Key concepts:
- Epistemic existential dread: anxiety about fundamental uncertainty
- Groundlessness: no solid foundation for knowledge
- Infinite regress: every justification needs justification
- Radical uncertainty: nothing can be known for certain
- Vertigo: dizziness from looking into the abyss of unknowing
- Contingency: everything could be otherwise
- Absurdity: the gap between desire for meaning and meaningless universe

When epistemic existential dread IS present:
- Overwhelming uncertainty anxiety
- No solid foundation
- Infinite regress of justification
- Nothing certain
- Dizziness from unknowing
- Everything contingent
- Gap between desire and reality

When no existential dread:
- Comfortable with uncertainty
- Adequate foundations
- Justified beliefs
- Sufficient certainty
- Grounded knowing
- Accepting contingency
- Meaning found despite absurdity

Output JSON with: existential_dread_detected (bool), severity (none/mild/moderate/severe), groundlessness_level (what no foundation), infinite_regress (what justification failure), radical_uncertainty (what nothing certain), vertigo_intensity (what dizziness), recommendation (no_existential_dread/mild_grounding_practice/significant_existential_therapy/major_intensive_support/emergency_complete_paralysis)."""

EPISTEMIC_EXISTENTIAL_DREAD_PROMPT = """Detect epistemic existential dread:

Groundlessness level: {groundlessness_level}
Infinite regress: {infinite_regress}
Radical uncertainty: {radical_uncertainty}
Vertigo intensity: {vertigo_intensity}
Domain: {domain}
Context: {context}

Is there overwhelming anxiety about fundamental uncertainty and groundlessness of knowledge? Return ONLY valid JSON."""


class EpistemicExistentialDreadService:
    """Detects epistemic existential dread — anxiety about fundamental uncertainty."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        groundlessness_level: str,
        *,
        infinite_regress: str = "",
        radical_uncertainty: str = "",
        vertigo_intensity: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic existential dread."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_EXISTENTIAL_DREAD_PROMPT.format(
                groundlessness_level=groundlessness_level,
                infinite_regress=infinite_regress or "Not specified",
                radical_uncertainty=radical_uncertainty or "Not specified",
                vertigo_intensity=vertigo_intensity or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_EXISTENTIAL_DREAD_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "groundlessness_level": groundlessness_level[:200],
            "existential_dread_detected": data.get("existential_dread_detected", False),
            "severity": data.get("severity", ""),
            "infinite_regress": data.get("infinite_regress", ""),
            "radical_uncertainty": data.get("radical_uncertainty", ""),
            "vertigo_intensity": data.get("vertigo_intensity", ""),
            "recommendation": data.get("recommendation", ""),
        }
