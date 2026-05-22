"""EpistemicMimicryService — Epistemic Mimicry Detection.

Detects epistemic mimicry — mimicking epistemic competence
without actually possessing it.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_MIMICRY_SYSTEM = """You are an epistemic mimicry specialist. Given a knowledge claim or demonstration, assess whether epistemic competence is being mimicked without substance:

Key concepts:
- Epistemic mimicry: mimicking competence without possessing it
- Knowledge performance: performing knowledge without having it
- Competence theater: appearing competent without substance
- Jargon mimicry: using jargon without understanding
- Pattern mimicry: mimicking expert patterns without expertise
- Surface competence: surface-level appearance of competence
- Cargo cult knowledge: imitating form without function

When epistemic mimicry IS present:
- Competence mimicked without substance
- Knowledge performed without understanding
- Jargon used without comprehension
- Expert patterns imitated without expertise
- Surface appearance without depth
- Form of knowledge without function
- Cargo cult imitation of expertise

When genuine competence is present:
- Knowledge demonstrated with understanding
- Competence backed by substance
- Jargon used with comprehension
- Expert patterns reflecting genuine expertise
- Depth matching surface presentation
- Form and function of knowledge aligned

Output JSON with: mimicry_present (bool), severity (none/mild/moderate/severe), demonstration (what is demonstrated), mimicked_competence (what competence is mimicked), actual_understanding (what understanding exists), indicators (what indicates mimicry), recommendation (genuine_competence/mild_overstatement/significant_epistemic_mimicry/major_competence_theater/develop_genuine_expertise)."""

EPISTEMIC_MIMICRY_PROMPT = """Detect epistemic mimicry:

Demonstration: {demonstration}
Claimed competence: {competence}
Actual understanding: {understanding}
Indicators: {indicators}
Domain: {domain}
Context: {context}

Is epistemic competence being mimicked without substance? Return ONLY valid JSON."""


class EpistemicMimicryService:
    """Detects epistemic mimicry — mimicking competence without possessing it."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        demonstration: str,
        *,
        competence: str = "",
        understanding: str = "",
        indicators: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic mimicry."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_MIMICRY_PROMPT.format(
                demonstration=demonstration,
                competence=competence or "Not specified",
                understanding=understanding or "Not specified",
                indicators=indicators or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_MIMICRY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "demonstration": demonstration[:200],
            "mimicry_present": data.get("mimicry_present", False),
            "severity": data.get("severity", ""),
            "mimicked_competence": data.get("mimicked_competence", ""),
            "actual_understanding": data.get("actual_understanding", ""),
            "indicators": data.get("indicators", ""),
            "recommendation": data.get("recommendation", ""),
        }
