"""EpistemicIntellectualIsolationService — Epistemic Intellectual Isolation Detection.

Detects epistemic intellectual isolation — isolation from being unable
to find intellectual peers who share one's level or interests.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_INTELLECTUAL_ISOLATION_SYSTEM = """You are an epistemic intellectual isolation specialist. Given isolation from lack of intellectual peers, assess intellectual isolation:

Key concepts:
- Epistemic intellectual isolation: isolation from lack of peers
- Peer absence: no one at same intellectual level
- Interest mismatch: no one shares intellectual interests
- Conversation hunger: craving substantive intellectual exchange
- Intellectual desert: environment lacking stimulation
- Misfit experience: not fitting into available communities
- Understimulation: chronic lack of intellectual challenge

When epistemic intellectual isolation IS present:
- Isolation from lack of peers
- No one at same level
- No one shares interests
- Craving intellectual exchange
- Environment lacking stimulation
- Not fitting into communities
- Chronic understimulation

When no intellectual isolation:
- Connected to peers
- Finding intellectual matches
- Shared interests
- Satisfied exchange
- Stimulating environment
- Belonging in communities
- Appropriately challenged

Output JSON with: intellectual_isolation_detected (bool), severity (none/mild/moderate/severe), peer_absence (what lacking), interest_mismatch (what not shared), conversation_hunger (what craving), intellectual_desert (what environment lacking), recommendation (no_intellectual_isolation/mild_community_seeking/significant_connection_building/major_intensive_belonging_work/emergency_severe_isolation)."""

EPISTEMIC_INTELLECTUAL_ISOLATION_PROMPT = """Detect epistemic intellectual isolation:

Peer absence: {peer_absence}
Interest mismatch: {interest_mismatch}
Conversation hunger: {conversation_hunger}
Intellectual desert: {intellectual_desert}
Domain: {domain}
Context: {context}

Is there isolation from being unable to find intellectual peers? Return ONLY valid JSON."""


class EpistemicIntellectualIsolationService:
    """Detects epistemic intellectual isolation — isolation from lack of peers."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        peer_absence: str,
        *,
        interest_mismatch: str = "",
        conversation_hunger: str = "",
        intellectual_desert: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic intellectual isolation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_INTELLECTUAL_ISOLATION_PROMPT.format(
                peer_absence=peer_absence,
                interest_mismatch=interest_mismatch or "Not specified",
                conversation_hunger=conversation_hunger or "Not specified",
                intellectual_desert=intellectual_desert or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_INTELLECTUAL_ISOLATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "peer_absence": peer_absence[:200],
            "intellectual_isolation_detected": data.get("intellectual_isolation_detected", False),
            "severity": data.get("severity", ""),
            "interest_mismatch": data.get("interest_mismatch", ""),
            "conversation_hunger": data.get("conversation_hunger", ""),
            "intellectual_desert": data.get("intellectual_desert", ""),
            "recommendation": data.get("recommendation", ""),
        }
