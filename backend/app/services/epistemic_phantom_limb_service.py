"""EpistemicPhantomLimbService — Epistemic Phantom Limb Detection.

Detects epistemic phantom limb — continued sensation of beliefs
or frameworks that have been removed or disproven.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PHANTOM_LIMB_SYSTEM = """You are an epistemic phantom limb specialist. Given a belief pattern, assess whether removed beliefs continue to influence thinking:

Key concepts:
- Epistemic phantom limb: sensation of removed beliefs persisting
- Ghost framework: removed framework still influencing thinking
- Residual influence: disproven beliefs still shaping reasoning
- Habit persistence: intellectual habits persisting after belief removal
- Structural echo: structure of removed belief still present
- Invisible assumption: removed assumption still operating
- Cognitive afterimage: afterimage of removed belief persisting

When epistemic phantom limb IS present:
- Removed beliefs continuing to influence thinking
- Removed framework still shaping reasoning
- Disproven beliefs still influencing conclusions
- Intellectual habits persisting after belief removal
- Structure of removed belief still constraining thought
- Removed assumptions still operating invisibly
- Afterimage of removed belief persisting in reasoning

When clean removal is present:
- Removed beliefs no longer influencing thinking
- Removed frameworks fully replaced
- Disproven beliefs no longer affecting conclusions
- Intellectual habits updated after belief removal
- New structures replacing old ones
- Assumptions updated after removal
- Clean transition to new frameworks

Output JSON with: phantom_limb_present (bool), severity (none/mild/moderate/severe), removed_belief (what belief was removed), residual_influence (what influence persists), manifestation (how it manifests), awareness (awareness of the phantom), recommendation (clean_removal/mild_residual/significant_phantom_limb/major_ghost_framework/complete_the_removal)."""

EPISTEMIC_PHANTOM_LIMB_PROMPT = """Detect epistemic phantom limb:

Removed belief: {removed_belief}
Residual influence: {residual_influence}
Manifestation: {manifestation}
Awareness: {awareness}
Domain: {domain}
Context: {context}

Are removed beliefs continuing to influence thinking? Return ONLY valid JSON."""


class EpistemicPhantomLimbService:
    """Detects epistemic phantom limb — removed beliefs still influencing thinking."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        removed_belief: str,
        *,
        residual_influence: str = "",
        manifestation: str = "",
        awareness: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic phantom limb."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PHANTOM_LIMB_PROMPT.format(
                removed_belief=removed_belief,
                residual_influence=residual_influence or "Not specified",
                manifestation=manifestation or "Not specified",
                awareness=awareness or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PHANTOM_LIMB_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "removed_belief": removed_belief[:200],
            "phantom_limb_present": data.get("phantom_limb_present", False),
            "severity": data.get("severity", ""),
            "residual_influence": data.get("residual_influence", ""),
            "manifestation": data.get("manifestation", ""),
            "awareness": data.get("awareness", ""),
            "recommendation": data.get("recommendation", ""),
        }
