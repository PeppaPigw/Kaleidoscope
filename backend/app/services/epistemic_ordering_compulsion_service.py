"""EpistemicOrderingCompulsionService — Epistemic Ordering Compulsion Detection.

Detects epistemic ordering compulsion — compulsive need for intellectual
symmetry, order, and taxonomic completeness.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ORDERING_COMPULSION_SYSTEM = """You are an epistemic ordering compulsion specialist. Given compulsive need for intellectual order, assess ordering:

Key concepts:
- Epistemic ordering compulsion: compulsive need for symmetry/order
- Taxonomic completeness: must categorize everything perfectly
- Symmetry demand: intellectual structures must be balanced
- Incompleteness distress: anxiety when framework has gaps
- Arrangement rituals: repeatedly reorganizing intellectual content
- Just-right feeling: seeking perfect intellectual arrangement
- Rigidity: unable to tolerate disorder in thinking

When epistemic ordering compulsion IS present:
- Compulsive need for symmetry
- Must categorize perfectly
- Structures must be balanced
- Anxiety at gaps
- Repeatedly reorganizing
- Seeking perfect arrangement
- Unable to tolerate disorder

When no ordering compulsion:
- Comfortable with asymmetry
- Flexible categorization
- Tolerating imbalance
- Comfortable with gaps
- Organizing once sufficient
- Good enough arrangement
- Tolerating disorder

Output JSON with: ordering_compulsion_detected (bool), severity (none/mild/moderate/severe), symmetry_demand (what must balance), incompleteness_distress (what gaps), arrangement_ritual (what reorganizing), rigidity_level (what can't tolerate), recommendation (no_ordering_compulsion/mild_flexibility_practice/significant_disorder_tolerance/major_intensive_erp/emergency_severe_ordering_ocd)."""

EPISTEMIC_ORDERING_COMPULSION_PROMPT = """Detect epistemic ordering compulsion:

Symmetry demand: {symmetry_demand}
Incompleteness distress: {incompleteness_distress}
Arrangement ritual: {arrangement_ritual}
Rigidity level: {rigidity_level}
Domain: {domain}
Context: {context}

Is there compulsive need for intellectual symmetry and taxonomic completeness? Return ONLY valid JSON."""


class EpistemicOrderingCompulsionService:
    """Detects epistemic ordering compulsion — compulsive need for intellectual order."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        symmetry_demand: str,
        *,
        incompleteness_distress: str = "",
        arrangement_ritual: str = "",
        rigidity_level: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic ordering compulsion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ORDERING_COMPULSION_PROMPT.format(
                symmetry_demand=symmetry_demand,
                incompleteness_distress=incompleteness_distress or "Not specified",
                arrangement_ritual=arrangement_ritual or "Not specified",
                rigidity_level=rigidity_level or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ORDERING_COMPULSION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "symmetry_demand": symmetry_demand[:200],
            "ordering_compulsion_detected": data.get("ordering_compulsion_detected", False),
            "severity": data.get("severity", ""),
            "incompleteness_distress": data.get("incompleteness_distress", ""),
            "arrangement_ritual": data.get("arrangement_ritual", ""),
            "rigidity_level": data.get("rigidity_level", ""),
            "recommendation": data.get("recommendation", ""),
        }
