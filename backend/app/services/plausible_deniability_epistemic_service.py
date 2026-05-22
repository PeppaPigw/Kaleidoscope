"""PlausibleDeniabilityEpistemicService — Epistemic Plausible Deniability Detection.

Detects epistemic plausible deniability — structuring knowledge to
maintain plausible deniability, where ignorance is strategically
constructed to avoid accountability.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

PLAUSIBLE_DENIABILITY_EPISTEMIC_SYSTEM = """You are an epistemic plausible deniability specialist. Given a knowledge structure, assess whether ignorance is being strategically maintained:

Key concepts:
- Plausible deniability: structured ignorance for accountability avoidance
- Strategic not-knowing: deliberately not learning to avoid responsibility
- Information architecture for deniability: systems designed to not know
- Willful ignorance structures: organizational ignorance by design
- Knowledge firewalls: barriers to knowing for deniability
- Accountability avoidance through ignorance: not knowing to not be responsible
- Constructed ignorance: ignorance as a deliberate product

When plausible deniability IS present:
- Ignorance strategically maintained
- Knowledge structures designed to avoid knowing
- Information barriers serving deniability
- Not-knowing deliberate rather than accidental
- Accountability avoided through constructed ignorance
- Systems designed to prevent knowledge reaching decision-makers
- Ignorance serving as shield against responsibility

When appropriate information boundaries are present:
- Information boundaries serving legitimate purposes
- Need-to-know based on genuine operational requirements
- Ignorance incidental not strategic
- Accountability maintained despite information boundaries
- Knowledge structures serving efficiency not deniability
- Information architecture serving organization not avoidance
- Boundaries transparent and justified

Output JSON with: deniability_present (bool), severity (none/mild/moderate/severe), structure (what knowledge structure exists), strategic_ignorance (what ignorance is maintained), accountability_avoided (what accountability is avoided), mechanism (how deniability is constructed), recommendation (appropriate_boundaries/mild_strategic_ignorance/significant_plausible_deniability/major_constructed_ignorance/dismantle_deniability_structures)."""

PLAUSIBLE_DENIABILITY_EPISTEMIC_PROMPT = """Detect epistemic plausible deniability:

Knowledge structure: {structure}
Information available: {available}
Information avoided: {avoided}
Accountability pattern: {accountability}
Domain: {domain}
Context: {context}

Is ignorance being strategically maintained for plausible deniability? Return ONLY valid JSON."""


class PlausibleDeniabilityEpistemicService:
    """Detects epistemic plausible deniability — structured ignorance for accountability."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        structure: str,
        *,
        available: str = "",
        avoided: str = "",
        accountability: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic plausible deniability."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=PLAUSIBLE_DENIABILITY_EPISTEMIC_PROMPT.format(
                structure=structure,
                available=available or "Not specified",
                avoided=avoided or "Not specified",
                accountability=accountability or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=PLAUSIBLE_DENIABILITY_EPISTEMIC_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "structure": structure[:200],
            "deniability_present": data.get("deniability_present", False),
            "severity": data.get("severity", ""),
            "strategic_ignorance": data.get("strategic_ignorance", ""),
            "accountability_avoided": data.get("accountability_avoided", ""),
            "mechanism": data.get("mechanism", ""),
            "recommendation": data.get("recommendation", ""),
        }
