"""EpistemicPresentFixationService — Epistemic Present Fixation Detection.

Detects epistemic present fixation — fixation on present knowledge refusing
to consider how understanding evolves.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PRESENT_FIXATION_SYSTEM = """You are an epistemic present fixation specialist. Given fixation on present knowledge, assess present fixation:

Key concepts:
- Epistemic present fixation: fixation on present refusing to consider evolution
- Temporal arrogance: believing current knowledge is final
- Evolution denial: refusing to accept knowledge will change
- Static worldview: treating current understanding as permanent
- Finality illusion: believing we've reached the end of knowledge
- Change resistance: resisting any revision of current views
- Temporal blindness: unable to see knowledge in temporal context

When epistemic present fixation IS present:
- Fixation on present knowledge
- Believing current is final
- Refusing to accept change
- Treating understanding as permanent
- Believing end of knowledge reached
- Resisting any revision
- Unable to see temporal context

When no present fixation:
- Temporal awareness
- Knowing knowledge evolves
- Accepting future change
- Understanding impermanence
- Knowing more to learn
- Open to revision
- Seeing temporal context

Output JSON with: present_fixation_detected (bool), severity (none/mild/moderate/severe), temporal_arrogance (what believing final about), evolution_denial (what refusing to accept will change), static_worldview (what treating as permanent), finality_illusion (what believing complete about), recommendation (no_present_fixation/mild_temporal_awareness/significant_evolution_acceptance/major_intensive_impermanence_work/emergency_complete_temporal_arrogance)."""

EPISTEMIC_PRESENT_FIXATION_PROMPT = """Detect epistemic present fixation:

Temporal arrogance: {temporal_arrogance}
Evolution denial: {evolution_denial}
Static worldview: {static_worldview}
Finality illusion: {finality_illusion}
Domain: {domain}
Context: {context}

Is there fixation on present knowledge refusing to consider how understanding evolves? Return ONLY valid JSON."""


class EpistemicPresentFixationService:
    """Detects epistemic present fixation — fixation on present knowledge."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        temporal_arrogance: str,
        *,
        evolution_denial: str = "",
        static_worldview: str = "",
        finality_illusion: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic present fixation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PRESENT_FIXATION_PROMPT.format(
                temporal_arrogance=temporal_arrogance,
                evolution_denial=evolution_denial or "Not specified",
                static_worldview=static_worldview or "Not specified",
                finality_illusion=finality_illusion or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PRESENT_FIXATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "temporal_arrogance": temporal_arrogance[:200],
            "present_fixation_detected": data.get("present_fixation_detected", False),
            "severity": data.get("severity", ""),
            "evolution_denial": data.get("evolution_denial", ""),
            "static_worldview": data.get("static_worldview", ""),
            "finality_illusion": data.get("finality_illusion", ""),
            "recommendation": data.get("recommendation", ""),
        }
