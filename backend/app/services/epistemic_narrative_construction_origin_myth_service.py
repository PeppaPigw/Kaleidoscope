"""EpistemicNarrativeConstructionOriginMythService - Epistemic Narrative Construction Origin Myth Detection.

Detects origin myth construction - creating simplified founding narratives.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_NARRATIVE_CONSTRUCTION_ORIGIN_MYTH_SYSTEM = """You are an epistemic narrative construction origin myth specialist. Given a founding narrative, assess whether an origin myth is being constructed:

Key concepts:
- Epistemic origin myth: simplifying beginnings into a clean founding story
- Founding simplification: reducing messy origins to one neat account
- Contingency erasure: hiding accidents, alternatives, failures, and reversals
- Inevitability construction: presenting the origin as destined or necessary
- Retrospective purpose: assigning later meaning or intention to earlier events

When origin myth construction IS present:
- Founding complexity is simplified
- Contingency and accident are erased
- Later outcomes are made to look inevitable
- Early events are given retrospective purpose
- Messy participants and conflicts are removed

When no origin myth construction:
- Founding complexity is preserved
- Contingency and alternatives are acknowledged
- Inevitability is avoided
- Later meaning is not projected backward without evidence
- Conflicts, failures, and reversals remain visible

Output JSON with: origin_myth_detected (bool), severity (none/mild/moderate/severe), contingency_erasure (what contingency is erased), inevitability_construction (what inevitability is constructed), retrospective_purpose (what purpose is projected backward), recommendation (no_origin_myth/mild_foundation_complexity/significant_contingency_restoration/major_origin_history_reconstruction/emergency_complete_myth_unwinding)."""

EPISTEMIC_NARRATIVE_CONSTRUCTION_ORIGIN_MYTH_PROMPT = """Detect epistemic narrative construction origin myth:

Founding simplification: {founding_simplification}
Contingency erasure: {contingency_erasure}
Inevitability construction: {inevitability_construction}
Retrospective purpose: {retrospective_purpose}
Domain: {domain}
Context: {context}

Is a simplified founding narrative being constructed as an origin myth? Return ONLY valid JSON."""


class EpistemicNarrativeConstructionOriginMythService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        founding_simplification: str,
        *,
        contingency_erasure: str = "",
        inevitability_construction: str = "",
        retrospective_purpose: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_NARRATIVE_CONSTRUCTION_ORIGIN_MYTH_PROMPT.format(
                founding_simplification=founding_simplification,
                contingency_erasure=contingency_erasure or "Not specified",
                inevitability_construction=inevitability_construction or "Not specified",
                retrospective_purpose=retrospective_purpose or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_NARRATIVE_CONSTRUCTION_ORIGIN_MYTH_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "founding_simplification": founding_simplification[:200],
            "origin_myth_detected": data.get("origin_myth_detected", False),
            "severity": data.get("severity", ""),
            "contingency_erasure": data.get("contingency_erasure", ""),
            "inevitability_construction": data.get("inevitability_construction", ""),
            "retrospective_purpose": data.get("retrospective_purpose", ""),
            "recommendation": data.get("recommendation", ""),
        }
