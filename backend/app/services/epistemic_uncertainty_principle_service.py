"""EpistemicUncertaintyPrincipleService — Epistemic Uncertainty Principle Detection.

Detects the epistemic uncertainty principle — examining a belief
changes it, making accurate assessment impossible.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_UNCERTAINTY_PRINCIPLE_SYSTEM = """You are an epistemic uncertainty principle specialist. Given an examination situation, assess whether examining beliefs changes them:

Key concepts:
- Epistemic uncertainty principle: examining beliefs changes them
- Observer effect: observation altering what is observed
- Assessment impossibility: accurate assessment impossible due to interference
- Reflexive distortion: self-examination distorting what is examined
- Measurement problem: measuring beliefs changing their state
- Introspection paradox: looking at beliefs changing their nature
- Heisenberg epistemics: cannot simultaneously know and examine a belief

When epistemic uncertainty principle IS present:
- Examining beliefs changes them in the process
- Observation altering the beliefs being observed
- Accurate assessment impossible due to examination interference
- Self-examination distorting what is being examined
- Measuring beliefs changing their state
- Looking at beliefs changing their nature
- Cannot simultaneously hold and examine a belief accurately

When stable examination is present:
- Beliefs can be examined without significant distortion
- Observation does not materially alter beliefs
- Assessment possible with reasonable accuracy
- Self-examination producing reliable results
- Measurement not significantly changing state
- Introspection yielding accurate information
- Examination and holding beliefs compatible

Output JSON with: uncertainty_principle_present (bool), severity (none/mild/moderate/severe), examination (what examination is attempted), distortion (how examination distorts), mechanism (how the effect operates), impossibility (what becomes impossible to assess), recommendation (stable_examination/mild_observer_effect/significant_uncertainty_principle/major_assessment_impossibility/use_indirect_methods)."""

EPISTEMIC_UNCERTAINTY_PRINCIPLE_PROMPT = """Detect epistemic uncertainty principle:

Examination: {examination}
Distortion: {distortion}
Mechanism: {mechanism}
Impossibility: {impossibility}
Domain: {domain}
Context: {context}

Does examining beliefs change them, making accurate assessment impossible? Return ONLY valid JSON."""


class EpistemicUncertaintyPrincipleService:
    """Detects epistemic uncertainty principle — examining beliefs changes them."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        examination: str,
        *,
        distortion: str = "",
        mechanism: str = "",
        impossibility: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic uncertainty principle."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_UNCERTAINTY_PRINCIPLE_PROMPT.format(
                examination=examination,
                distortion=distortion or "Not specified",
                mechanism=mechanism or "Not specified",
                impossibility=impossibility or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_UNCERTAINTY_PRINCIPLE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "examination": examination[:200],
            "uncertainty_principle_present": data.get("uncertainty_principle_present", False),
            "severity": data.get("severity", ""),
            "distortion": data.get("distortion", ""),
            "mechanism": data.get("mechanism", ""),
            "impossibility": data.get("impossibility", ""),
            "recommendation": data.get("recommendation", ""),
        }
