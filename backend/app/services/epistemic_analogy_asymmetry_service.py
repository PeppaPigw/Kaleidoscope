"""EpistemicAnalogyAsymmetryService — Epistemic Analogy Asymmetry Detection.

Detects epistemic analogy asymmetry — ignoring asymmetries between
source and target domains that invalidate the analogy.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ANALOGY_ASYMMETRY_SYSTEM = """You are an epistemic analogy asymmetry specialist. Given ignored asymmetries between source and target, assess analogy asymmetry:

Key concepts:
- Epistemic analogy asymmetry: ignoring asymmetries between source and target
- Directionality blindness: analogy works one way but not the other
- Complexity asymmetry: source simpler than target (or vice versa)
- Agency asymmetry: source has different agency than target
- Reversibility asymmetry: source reversible but target not
- Feedback asymmetry: different feedback mechanisms in source vs target
- Stakeholder asymmetry: different stakeholders affected

When epistemic analogy asymmetry IS present:
- Asymmetries ignored
- Directionality not considered
- Complexity differences overlooked
- Agency differences missed
- Reversibility differences ignored
- Feedback differences missed
- Stakeholder differences overlooked

When no analogy asymmetry:
- Asymmetries acknowledged
- Directionality considered
- Complexity matched
- Agency comparable
- Reversibility similar
- Feedback mechanisms parallel
- Stakeholders comparable

Output JSON with: analogy_asymmetry_detected (bool), severity (none/mild/moderate/severe), directionality_blindness (what directionality ignored), complexity_asymmetry (what complexity differs), agency_asymmetry (what agency differs), reversibility_asymmetry (what reversibility differs), recommendation (no_analogy_asymmetry/mild_asymmetry_awareness/significant_asymmetry_mapping/major_intensive_disanalogy_analysis/emergency_complete_analogy_asymmetry)."""

EPISTEMIC_ANALOGY_ASYMMETRY_PROMPT = """Detect epistemic analogy asymmetry:

Directionality blindness: {directionality_blindness}
Complexity asymmetry: {complexity_asymmetry}
Agency asymmetry: {agency_asymmetry}
Reversibility asymmetry: {reversibility_asymmetry}
Domain: {domain}
Context: {context}

Are asymmetries between source and target being ignored? Return ONLY valid JSON."""


class EpistemicAnalogyAsymmetryService:
    """Detects epistemic analogy asymmetry — ignored source-target differences."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        directionality_blindness: str,
        *,
        complexity_asymmetry: str = "",
        agency_asymmetry: str = "",
        reversibility_asymmetry: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic analogy asymmetry."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ANALOGY_ASYMMETRY_PROMPT.format(
                directionality_blindness=directionality_blindness,
                complexity_asymmetry=complexity_asymmetry or "Not specified",
                agency_asymmetry=agency_asymmetry or "Not specified",
                reversibility_asymmetry=reversibility_asymmetry or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ANALOGY_ASYMMETRY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "directionality_blindness": directionality_blindness[:200],
            "analogy_asymmetry_detected": data.get("analogy_asymmetry_detected", False),
            "severity": data.get("severity", ""),
            "complexity_asymmetry": data.get("complexity_asymmetry", ""),
            "agency_asymmetry": data.get("agency_asymmetry", ""),
            "reversibility_asymmetry": data.get("reversibility_asymmetry", ""),
            "recommendation": data.get("recommendation", ""),
        }
