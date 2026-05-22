"""EpistemicIdentityDiffusionDeeperService — Epistemic Identity Diffusion Deeper Detection.

Detects deeper epistemic identity diffusion — where one has no coherent
intellectual self.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_IDENTITY_DIFFUSION_DEEPER_SYSTEM = """You are an epistemic identity diffusion specialist. Given no coherent intellectual self, assess deeper identity diffusion:

Key concepts:
- Epistemic identity diffusion deeper: no coherent intellectual self
- Belief chaos: beliefs scattered without coherent organization
- Position instability: positions changing randomly without reason
- Intellectual shapelessness: no recognizable intellectual form
- Value vacuum: no intellectual values guiding thought
- Commitment inability: unable to commit to any position
- Self-absence: no intellectual self present

When epistemic identity diffusion deeper IS present:
- No coherent intellectual self
- Beliefs scattered without organization
- Positions changing randomly
- No recognizable intellectual form
- No values guiding thought
- Unable to commit to positions
- No intellectual self present

When no deeper identity diffusion:
- Coherent intellectual self
- Organized beliefs
- Stable positions with reasons
- Recognizable form
- Values guiding thought
- Able to commit
- Self present

Output JSON with: identity_diffusion_deeper_detected (bool), severity (none/mild/moderate/severe), belief_chaos (what beliefs scattered about), position_instability (what changing randomly), intellectual_shapelessness (what lacking form about), commitment_inability (what unable to commit to), recommendation (no_identity_diffusion/mild_coherence_building/significant_identity_formation/major_intensive_self_construction/emergency_complete_identity_absence)."""

EPISTEMIC_IDENTITY_DIFFUSION_DEEPER_PROMPT = """Detect deeper epistemic identity diffusion:

Belief chaos: {belief_chaos}
Position instability: {position_instability}
Intellectual shapelessness: {intellectual_shapelessness}
Commitment inability: {commitment_inability}
Domain: {domain}
Context: {context}

Is there no coherent intellectual self? Return ONLY valid JSON."""


class EpistemicIdentityDiffusionDeeperService:
    """Detects deeper epistemic identity diffusion — no coherent intellectual self."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        belief_chaos: str,
        *,
        position_instability: str = "",
        intellectual_shapelessness: str = "",
        commitment_inability: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect deeper epistemic identity diffusion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_IDENTITY_DIFFUSION_DEEPER_PROMPT.format(
                belief_chaos=belief_chaos,
                position_instability=position_instability or "Not specified",
                intellectual_shapelessness=intellectual_shapelessness or "Not specified",
                commitment_inability=commitment_inability or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_IDENTITY_DIFFUSION_DEEPER_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "belief_chaos": belief_chaos[:200],
            "identity_diffusion_deeper_detected": data.get("identity_diffusion_deeper_detected", False),
            "severity": data.get("severity", ""),
            "position_instability": data.get("position_instability", ""),
            "intellectual_shapelessness": data.get("intellectual_shapelessness", ""),
            "commitment_inability": data.get("commitment_inability", ""),
            "recommendation": data.get("recommendation", ""),
        }
