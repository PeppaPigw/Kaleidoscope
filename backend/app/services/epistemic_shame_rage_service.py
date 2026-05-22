"""EpistemicShameRageService — Epistemic Shame Rage Detection.

Detects epistemic shame rage — rage as defense against unbearable
intellectual shame, attacking to avoid feeling shamed.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SHAME_RAGE_SYSTEM = """You are an epistemic shame rage specialist. Given rage defending against shame, assess shame rage:

Key concepts:
- Epistemic shame rage: rage defending against shame
- Humiliation fury: explosive anger when shamed intellectually
- Attack as defense: destroying the shamer
- Blame externalization: it's their fault I feel this
- Disproportionate response: rage far exceeding trigger
- Shame bypass: rage prevents feeling the shame
- Relationship destruction: rage destroys intellectual connections

When epistemic shame rage IS present:
- Rage defending against shame
- Explosive anger when shamed
- Destroying the shamer
- Blaming externally
- Response far exceeding trigger
- Rage preventing shame feeling
- Destroying connections

When no shame rage:
- Feeling shame directly
- Proportionate response
- Non-destructive processing
- Taking responsibility
- Measured response
- Allowing shame feeling
- Preserving connections

Output JSON with: shame_rage_detected (bool), severity (none/mild/moderate/severe), humiliation_fury (what exploding at), attack_pattern (what destroying), blame_externalization (what blaming), relationship_destruction (what damaging), recommendation (no_shame_rage/mild_rage_awareness/significant_shame_tolerance/major_intensive_rage_therapy/emergency_severe_destructive_rage)."""

EPISTEMIC_SHAME_RAGE_PROMPT = """Detect epistemic shame rage:

Humiliation fury: {humiliation_fury}
Attack pattern: {attack_pattern}
Blame externalization: {blame_externalization}
Relationship destruction: {relationship_destruction}
Domain: {domain}
Context: {context}

Is there rage as defense against unbearable intellectual shame? Return ONLY valid JSON."""


class EpistemicShameRageService:
    """Detects epistemic shame rage — rage defending against shame."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        humiliation_fury: str,
        *,
        attack_pattern: str = "",
        blame_externalization: str = "",
        relationship_destruction: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic shame rage."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SHAME_RAGE_PROMPT.format(
                humiliation_fury=humiliation_fury,
                attack_pattern=attack_pattern or "Not specified",
                blame_externalization=blame_externalization or "Not specified",
                relationship_destruction=relationship_destruction or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SHAME_RAGE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "humiliation_fury": humiliation_fury[:200],
            "shame_rage_detected": data.get("shame_rage_detected", False),
            "severity": data.get("severity", ""),
            "attack_pattern": data.get("attack_pattern", ""),
            "blame_externalization": data.get("blame_externalization", ""),
            "relationship_destruction": data.get("relationship_destruction", ""),
            "recommendation": data.get("recommendation", ""),
        }
