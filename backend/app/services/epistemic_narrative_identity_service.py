"""EpistemicNarrativeIdentityService — Epistemic Narrative Identity Detection.

Detects epistemic narrative identity — identity so tied to a narrative
that changing the narrative feels impossible or threatening.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_NARRATIVE_IDENTITY_SYSTEM = """You are an epistemic narrative identity specialist. Given identity tied to narrative, assess narrative identity:

Key concepts:
- Epistemic narrative identity: identity so tied to narrative that change feels impossible
- Self-story fusion: self fused with story about self
- Narrative imprisonment: imprisoned by own narrative
- Identity-story lock: identity locked to specific story
- Change as self-destruction: changing narrative feels like self-destruction
- Story-dependent self: self dependent on maintaining story
- Narrative rigidity as identity: rigidity of narrative as identity protection

When epistemic narrative identity IS present:
- Identity tied to narrative
- Self fused with story
- Imprisoned by narrative
- Identity locked to story
- Change feels like self-destruction
- Self dependent on story
- Rigidity as identity protection

When no narrative identity:
- Identity flexible beyond narrative
- Self separate from story
- Free from narrative
- Identity adaptable
- Change feels like growth
- Self independent of story
- Flexibility as strength

Output JSON with: narrative_identity_detected (bool), severity (none/mild/moderate/severe), self_story_fusion (what self fused with story about), narrative_imprisonment (what imprisoned by), change_as_self_destruction (what change feels destructive about), story_dependent_self (what self dependent on maintaining), recommendation (no_narrative_identity/mild_flexibility_practice/significant_identity_expansion/major_intensive_narrative_liberation/emergency_complete_narrative_imprisonment)."""

EPISTEMIC_NARRATIVE_IDENTITY_PROMPT = """Detect epistemic narrative identity:

Self story fusion: {self_story_fusion}
Narrative imprisonment: {narrative_imprisonment}
Change as self destruction: {change_as_self_destruction}
Story dependent self: {story_dependent_self}
Domain: {domain}
Context: {context}

Is there identity so tied to a narrative that changing it feels impossible? Return ONLY valid JSON."""


class EpistemicNarrativeIdentityService:
    """Detects epistemic narrative identity — identity tied to narrative."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        self_story_fusion: str,
        *,
        narrative_imprisonment: str = "",
        change_as_self_destruction: str = "",
        story_dependent_self: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic narrative identity."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_NARRATIVE_IDENTITY_PROMPT.format(
                self_story_fusion=self_story_fusion,
                narrative_imprisonment=narrative_imprisonment or "Not specified",
                change_as_self_destruction=change_as_self_destruction or "Not specified",
                story_dependent_self=story_dependent_self or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_NARRATIVE_IDENTITY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "self_story_fusion": self_story_fusion[:200],
            "narrative_identity_detected": data.get("narrative_identity_detected", False),
            "severity": data.get("severity", ""),
            "narrative_imprisonment": data.get("narrative_imprisonment", ""),
            "change_as_self_destruction": data.get("change_as_self_destruction", ""),
            "story_dependent_self": data.get("story_dependent_self", ""),
            "recommendation": data.get("recommendation", ""),
        }
