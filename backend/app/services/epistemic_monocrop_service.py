"""EpistemicMonocropService — Epistemic Monocrop Detection.

Detects epistemic monocropping — over-reliance on a single
methodology, framework, or knowledge tradition, reducing
intellectual diversity and resilience.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_MONOCROP_SYSTEM = """You are an epistemic monocrop specialist. Given a knowledge ecosystem, assess whether dangerous intellectual monoculture exists:

Key concepts:
- Epistemic monocrop: single methodology dominates all inquiry
- Intellectual monoculture: one framework crowds out alternatives
- Methodological monopoly: only one approach considered valid
- Paradigm lock-in: inability to think outside dominant framework
- Diversity collapse: loss of alternative knowledge traditions
- Resilience failure: inability to adapt when dominant approach fails
- Epistemic fragility: vulnerability from lack of diversity

When epistemic monocropping IS present:
- Single methodology dominates without justification
- Alternative approaches dismissed or invisible
- Intellectual diversity actively suppressed
- Framework treated as only valid approach
- Knowledge ecosystem lacks resilience
- Failure of dominant approach would be catastrophic
- No fallback frameworks available

When methodological focus is appropriate:
- Dominant approach justified by evidence
- Alternatives acknowledged and available
- Focus is pragmatic, not dogmatic
- Diversity maintained at ecosystem level
- Limitations of approach recognized
- Fallback approaches exist
- Dominance earned through merit

Output JSON with: monocrop_present (bool), severity (none/mild/moderate/severe), ecosystem (what knowledge ecosystem), dominant (what dominates), excluded (what is excluded), fragility (what fragility results), recommendation (appropriate_methodological_focus/mild_diversity_reduction/significant_epistemic_monocrop/major_intellectual_monoculture/restore_epistemic_diversity)."""

EPISTEMIC_MONOCROP_PROMPT = """Detect epistemic monocropping:

Ecosystem: {ecosystem}
Dominant approach: {dominant}
Alternatives available: {alternatives}
Exclusion mechanisms: {exclusion}
Domain: {domain}
Context: {context}

Is dangerous intellectual monoculture reducing epistemic resilience? Return ONLY valid JSON."""


class EpistemicMonocropService:
    """Detects epistemic monocropping — dangerous intellectual monoculture."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        ecosystem: str,
        *,
        dominant: str = "",
        alternatives: str = "",
        exclusion: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic monocropping."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_MONOCROP_PROMPT.format(
                ecosystem=ecosystem,
                dominant=dominant or "Not specified",
                alternatives=alternatives or "Not specified",
                exclusion=exclusion or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_MONOCROP_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "ecosystem": ecosystem[:200],
            "monocrop_present": data.get("monocrop_present", False),
            "severity": data.get("severity", ""),
            "dominant": data.get("dominant", ""),
            "excluded": data.get("excluded", ""),
            "fragility": data.get("fragility", ""),
            "recommendation": data.get("recommendation", ""),
        }
