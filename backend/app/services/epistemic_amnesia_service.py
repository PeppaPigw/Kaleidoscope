"""EpistemicAmnesiaService — Epistemic Amnesia Detection.

Detects epistemic amnesia — gaps in intellectual memory where knowledge
that was once held has become inaccessible or forgotten.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_AMNESIA_SYSTEM = """You are an epistemic amnesia specialist. Given gaps in intellectual memory, assess amnesia:

Key concepts:
- Epistemic amnesia: knowledge once held now inaccessible
- Knowledge gaps: holes in what should be known
- Selective forgetting: specific domains or periods lost
- Motivated amnesia: forgetting serving psychological purpose
- Retrieval failure: knowledge exists but can't be accessed
- Continuity break: gap in intellectual autobiography
- Dissociative barrier: wall between self and knowledge

When epistemic amnesia IS present:
- Knowledge once held now inaccessible
- Holes in what should be known
- Specific domains lost
- Forgetting serving purpose
- Can't access existing knowledge
- Gap in autobiography
- Wall between self and knowledge

When no amnesia:
- Knowledge accessible
- Complete intellectual memory
- All domains available
- No motivated forgetting
- Easy retrieval
- Continuous autobiography
- No barriers

Output JSON with: amnesia_detected (bool), severity (none/mild/moderate/severe), knowledge_gaps (what inaccessible), selective_forgetting (what specifically lost), motivated_purpose (what forgetting serves), continuity_break (what gap in), recommendation (no_amnesia/mild_retrieval_practice/significant_memory_recovery/major_intensive_dissociation_therapy/emergency_severe_amnesia)."""

EPISTEMIC_AMNESIA_PROMPT = """Detect epistemic amnesia:

Knowledge gaps: {knowledge_gaps}
Selective forgetting: {selective_forgetting}
Motivated purpose: {motivated_purpose}
Continuity break: {continuity_break}
Domain: {domain}
Context: {context}

Are there gaps in intellectual memory where knowledge once held is now inaccessible? Return ONLY valid JSON."""


class EpistemicAmnesiaService:
    """Detects epistemic amnesia — knowledge once held now inaccessible."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        knowledge_gaps: str,
        *,
        selective_forgetting: str = "",
        motivated_purpose: str = "",
        continuity_break: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic amnesia."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_AMNESIA_PROMPT.format(
                knowledge_gaps=knowledge_gaps,
                selective_forgetting=selective_forgetting or "Not specified",
                motivated_purpose=motivated_purpose or "Not specified",
                continuity_break=continuity_break or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_AMNESIA_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "knowledge_gaps": knowledge_gaps[:200],
            "amnesia_detected": data.get("amnesia_detected", False),
            "severity": data.get("severity", ""),
            "selective_forgetting": data.get("selective_forgetting", ""),
            "motivated_purpose": data.get("motivated_purpose", ""),
            "continuity_break": data.get("continuity_break", ""),
            "recommendation": data.get("recommendation", ""),
        }
