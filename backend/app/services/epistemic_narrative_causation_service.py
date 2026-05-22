"""EpistemicNarrativeCausationService — Epistemic Narrative Causation Detection.

Detects epistemic narrative causation — imposing causal narratives on
coincidental or loosely correlated events.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_NARRATIVE_CAUSATION_SYSTEM = """You are an epistemic narrative causation specialist. Given narrative causal imposition, assess false causation through narrative:

Key concepts:
- Epistemic narrative causation: imposing causal stories on coincidental events
- Post hoc narrative: constructing after-the-fact causal stories
- Narrative necessity: treating narrative coherence as evidence of causation
- Coincidence denial: refusing to accept coincidence when narrative available
- Causal chain fabrication: fabricating intermediate causal steps for narrative
- Agency imposition: attributing agency where none exists for narrative purposes
- Deterministic narrative: presenting contingent outcomes as inevitable

When epistemic narrative causation IS present:
- Causal narratives imposed on coincidence
- Post hoc stories constructed
- Narrative coherence treated as evidence
- Coincidence denied
- Causal chains fabricated
- Agency imposed falsely
- Contingency denied

When no narrative causation:
- Causation established through evidence
- Coincidence acknowledged
- Narrative distinguished from evidence
- Causal claims properly supported
- Agency attributed appropriately
- Contingency recognized
- Uncertainty preserved

Output JSON with: narrative_causation_detected (bool), severity (none/mild/moderate/severe), post_hoc_narrative (what post hoc stories), coincidence_denial (what coincidence denied), causal_chain_fabrication (what chains fabricated), agency_imposition (what agency imposed), recommendation (no_narrative_causation/mild_causal_checking/significant_narrative_separation/major_intensive_evidence_requirement/emergency_complete_narrative_causation)."""

EPISTEMIC_NARRATIVE_CAUSATION_PROMPT = """Detect epistemic narrative causation:

Post hoc narrative: {post_hoc_narrative}
Coincidence denial: {coincidence_denial}
Causal chain fabrication: {causal_chain_fabrication}
Agency imposition: {agency_imposition}
Domain: {domain}
Context: {context}

Are causal narratives being imposed on coincidental events? Return ONLY valid JSON."""


class EpistemicNarrativeCausationService:
    """Detects epistemic narrative causation — false causal stories."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        post_hoc_narrative: str,
        *,
        coincidence_denial: str = "",
        causal_chain_fabrication: str = "",
        agency_imposition: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic narrative causation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_NARRATIVE_CAUSATION_PROMPT.format(
                post_hoc_narrative=post_hoc_narrative,
                coincidence_denial=coincidence_denial or "Not specified",
                causal_chain_fabrication=causal_chain_fabrication or "Not specified",
                agency_imposition=agency_imposition or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_NARRATIVE_CAUSATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "post_hoc_narrative": post_hoc_narrative[:200],
            "narrative_causation_detected": data.get("narrative_causation_detected", False),
            "severity": data.get("severity", ""),
            "coincidence_denial": data.get("coincidence_denial", ""),
            "causal_chain_fabrication": data.get("causal_chain_fabrication", ""),
            "agency_imposition": data.get("agency_imposition", ""),
            "recommendation": data.get("recommendation", ""),
        }
