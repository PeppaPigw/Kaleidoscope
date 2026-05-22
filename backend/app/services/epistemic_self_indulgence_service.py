"""EpistemicSelfIndulgenceService — Epistemic Self-Indulgence Detection.

Detects epistemic self-indulgence — pursuing intellectual pleasure
at the expense of epistemic responsibility, where the enjoyment of
theorizing replaces the discipline of truth-seeking.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SELF_INDULGENCE_SYSTEM = """You are an epistemic self-indulgence specialist. Given intellectual activity, assess whether pleasure is replacing responsibility:

Key concepts:
- Epistemic self-indulgence: intellectual pleasure over responsibility
- Theory addiction: enjoying theorizing more than testing
- Intellectual entertainment: ideas as entertainment not inquiry
- Complexity fetish: enjoying complexity for its own sake
- Speculation indulgence: speculating without grounding
- Intellectual play without stakes: theorizing without commitment
- Aesthetic epistemology: preferring beautiful theories over true ones

When epistemic self-indulgence IS present:
- Intellectual pleasure prioritized over truth-seeking
- Theorizing enjoyed without testing or grounding
- Ideas treated as entertainment not serious inquiry
- Complexity pursued for aesthetic not epistemic reasons
- Speculation indulged without accountability
- Beautiful theories preferred over accurate ones
- Intellectual play replaces disciplined inquiry

When intellectual exploration is appropriate:
- Exploration serves eventual truth-seeking
- Theorizing leads to testable predictions
- Ideas engaged with seriously and critically
- Complexity proportional to subject matter
- Speculation acknowledged and bounded
- Aesthetic appreciation doesn't override evidence
- Play and discipline balanced

Output JSON with: indulgence_present (bool), severity (none/mild/moderate/severe), activity (what intellectual activity), pleasure (what pleasure is pursued), responsibility_neglected (what responsibility is neglected), grounding (what grounding is missing), recommendation (appropriate_intellectual_exploration/mild_theory_preference/significant_epistemic_indulgence/major_responsibility_neglect/balance_pleasure_and_discipline)."""

EPISTEMIC_SELF_INDULGENCE_PROMPT = """Detect epistemic self-indulgence:

Activity: {activity}
Purpose: {purpose}
Grounding: {grounding}
Accountability: {accountability}
Domain: {domain}
Context: {context}

Is intellectual pleasure being pursued at the expense of epistemic responsibility? Return ONLY valid JSON."""


class EpistemicSelfIndulgenceService:
    """Detects epistemic self-indulgence — pleasure replacing responsibility."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        activity: str,
        *,
        purpose: str = "",
        grounding: str = "",
        accountability: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic self-indulgence."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SELF_INDULGENCE_PROMPT.format(
                activity=activity,
                purpose=purpose or "Not specified",
                grounding=grounding or "Not specified",
                accountability=accountability or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SELF_INDULGENCE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "activity": activity[:200],
            "indulgence_present": data.get("indulgence_present", False),
            "severity": data.get("severity", ""),
            "pleasure": data.get("pleasure", ""),
            "responsibility_neglected": data.get("responsibility_neglected", ""),
            "grounding": data.get("grounding", ""),
            "recommendation": data.get("recommendation", ""),
        }
