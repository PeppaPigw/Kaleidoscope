"""EpistemicKnowledgeImpermanenceDenialService — Epistemic Knowledge Impermanence Denial Detection.

Detects epistemic knowledge impermanence denial — denying that current
knowledge will be superseded.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_KNOWLEDGE_IMPERMANENCE_DENIAL_SYSTEM = """You are an epistemic knowledge impermanence denial specialist. Given denying knowledge will be superseded, assess impermanence denial:

Key concepts:
- Epistemic knowledge impermanence denial: denying current knowledge will be superseded
- Permanence illusion: believing current theories are final truth
- Supersession blindness: unable to imagine current knowledge being replaced
- Paradigm permanence: treating current paradigm as eternal
- Discovery completion: believing all important things already known
- Revision impossibility: believing current knowledge can't be wrong
- Future-proofing delusion: believing current understanding is timeless

When epistemic knowledge impermanence denial IS present:
- Denying knowledge will be superseded
- Believing theories are final
- Unable to imagine replacement
- Treating paradigm as eternal
- Believing all known already
- Believing can't be wrong
- Believing understanding timeless

When no impermanence denial:
- Accepting knowledge evolves
- Knowing theories are provisional
- Imagining future replacement
- Seeing paradigms as temporary
- Knowing more to discover
- Accepting fallibility
- Understanding temporality

Output JSON with: knowledge_impermanence_denial_detected (bool), severity (none/mild/moderate/severe), permanence_illusion (what believing final about), supersession_blindness (what unable to imagine replaced), paradigm_permanence (what treating as eternal), discovery_completion (what believing all known about), recommendation (no_impermanence_denial/mild_provisionality_awareness/significant_impermanence_acceptance/major_intensive_fallibility_work/emergency_complete_permanence_delusion)."""

EPISTEMIC_KNOWLEDGE_IMPERMANENCE_DENIAL_PROMPT = """Detect epistemic knowledge impermanence denial:

Permanence illusion: {permanence_illusion}
Supersession blindness: {supersession_blindness}
Paradigm permanence: {paradigm_permanence}
Discovery completion: {discovery_completion}
Domain: {domain}
Context: {context}

Is there denying that current knowledge will be superseded? Return ONLY valid JSON."""


class EpistemicKnowledgeImpermanenceDenialService:
    """Detects epistemic knowledge impermanence denial — denying knowledge will be superseded."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        permanence_illusion: str,
        *,
        supersession_blindness: str = "",
        paradigm_permanence: str = "",
        discovery_completion: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic knowledge impermanence denial."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_KNOWLEDGE_IMPERMANENCE_DENIAL_PROMPT.format(
                permanence_illusion=permanence_illusion,
                supersession_blindness=supersession_blindness or "Not specified",
                paradigm_permanence=paradigm_permanence or "Not specified",
                discovery_completion=discovery_completion or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_KNOWLEDGE_IMPERMANENCE_DENIAL_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "permanence_illusion": permanence_illusion[:200],
            "knowledge_impermanence_denial_detected": data.get("knowledge_impermanence_denial_detected", False),
            "severity": data.get("severity", ""),
            "supersession_blindness": data.get("supersession_blindness", ""),
            "paradigm_permanence": data.get("paradigm_permanence", ""),
            "discovery_completion": data.get("discovery_completion", ""),
            "recommendation": data.get("recommendation", ""),
        }
