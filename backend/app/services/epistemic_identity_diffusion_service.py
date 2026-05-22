"""EpistemicIdentityDiffusionService — Epistemic Identity Diffusion Detection.

Detects epistemic identity diffusion — unstable intellectual identity,
not knowing what one truly thinks or believes.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_IDENTITY_DIFFUSION_SYSTEM = """You are an epistemic identity diffusion specialist. Given unstable intellectual identity, assess diffusion:

Key concepts:
- Epistemic identity diffusion: not knowing what one thinks
- Belief instability: constantly shifting positions
- Chameleon thinking: adopting whatever view is nearby
- Core absence: no stable intellectual center
- Identity borrowing: taking on others' intellectual identities
- Confusion: genuine bewilderment about own views
- Fragmentation: contradictory beliefs without integration

When epistemic identity diffusion IS present:
- Not knowing what one thinks
- Constantly shifting positions
- Adopting nearby views
- No stable center
- Taking others' identities
- Bewildered about own views
- Contradictory without integration

When no identity diffusion:
- Clear intellectual identity
- Stable core positions
- Authentic thinking
- Centered perspective
- Own intellectual identity
- Clear self-knowledge
- Integrated beliefs

Output JSON with: identity_diffusion_detected (bool), severity (none/mild/moderate/severe), belief_instability (what shifting), chameleon_pattern (what adopting), core_absence (what missing center), fragmentation_level (what contradicting), recommendation (no_identity_diffusion/mild_identity_exploration/significant_identity_building/major_intensive_integration/emergency_severe_diffusion)."""

EPISTEMIC_IDENTITY_DIFFUSION_PROMPT = """Detect epistemic identity diffusion:

Belief instability: {belief_instability}
Chameleon pattern: {chameleon_pattern}
Core absence: {core_absence}
Fragmentation level: {fragmentation_level}
Domain: {domain}
Context: {context}

Is there unstable intellectual identity — not knowing what one truly thinks? Return ONLY valid JSON."""


class EpistemicIdentityDiffusionService:
    """Detects epistemic identity diffusion — unstable intellectual identity."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        belief_instability: str,
        *,
        chameleon_pattern: str = "",
        core_absence: str = "",
        fragmentation_level: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic identity diffusion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_IDENTITY_DIFFUSION_PROMPT.format(
                belief_instability=belief_instability,
                chameleon_pattern=chameleon_pattern or "Not specified",
                core_absence=core_absence or "Not specified",
                fragmentation_level=fragmentation_level or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_IDENTITY_DIFFUSION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "belief_instability": belief_instability[:200],
            "identity_diffusion_detected": data.get("identity_diffusion_detected", False),
            "severity": data.get("severity", ""),
            "chameleon_pattern": data.get("chameleon_pattern", ""),
            "core_absence": data.get("core_absence", ""),
            "fragmentation_level": data.get("fragmentation_level", ""),
            "recommendation": data.get("recommendation", ""),
        }
