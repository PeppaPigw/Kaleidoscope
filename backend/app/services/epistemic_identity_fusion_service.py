"""EpistemicIdentityFusionService — Epistemic Identity Fusion Detection.

Detects epistemic identity fusion — fusing personal identity with
intellectual positions so challenges feel like personal attacks.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_IDENTITY_FUSION_SYSTEM = """You are an epistemic identity fusion specialist. Given fusing identity with positions, assess identity fusion:

Key concepts:
- Epistemic identity fusion: fusing identity with intellectual positions
- Belief-self merger: beliefs become inseparable from self
- Challenge as attack: intellectual challenges feel like personal attacks
- Position rigidity: can't change positions without identity crisis
- Defensive intellectualism: defending ideas as defending self
- Ego-belief entanglement: ego wrapped up in being right
- Existential stakes: every disagreement feels existential

When epistemic identity fusion IS present:
- Fusing identity with positions
- Beliefs inseparable from self
- Challenges feel like attacks
- Can't change without crisis
- Defending ideas as self
- Ego wrapped in being right
- Disagreements feel existential

When no identity fusion:
- Identity separate from positions
- Beliefs held lightly
- Challenges feel intellectual
- Can change freely
- Ideas separate from self
- Ego independent of rightness
- Disagreements feel normal

Output JSON with: identity_fusion_detected (bool), severity (none/mild/moderate/severe), belief_self_merger (what beliefs inseparable from self), challenge_as_attack (what challenges feel like attacks about), position_rigidity (what can't change without crisis), existential_stakes (what disagreements feel existential about), recommendation (no_identity_fusion/mild_separation_practice/significant_differentiation_work/major_intensive_identity_rebuilding/emergency_complete_identity_fusion)."""

EPISTEMIC_IDENTITY_FUSION_PROMPT = """Detect epistemic identity fusion:

Belief self merger: {belief_self_merger}
Challenge as attack: {challenge_as_attack}
Position rigidity: {position_rigidity}
Existential stakes: {existential_stakes}
Domain: {domain}
Context: {context}

Is there fusing personal identity with intellectual positions? Return ONLY valid JSON."""


class EpistemicIdentityFusionService:
    """Detects epistemic identity fusion — fusing identity with positions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        belief_self_merger: str,
        *,
        challenge_as_attack: str = "",
        position_rigidity: str = "",
        existential_stakes: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic identity fusion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_IDENTITY_FUSION_PROMPT.format(
                belief_self_merger=belief_self_merger,
                challenge_as_attack=challenge_as_attack or "Not specified",
                position_rigidity=position_rigidity or "Not specified",
                existential_stakes=existential_stakes or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_IDENTITY_FUSION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "belief_self_merger": belief_self_merger[:200],
            "identity_fusion_detected": data.get("identity_fusion_detected", False),
            "severity": data.get("severity", ""),
            "challenge_as_attack": data.get("challenge_as_attack", ""),
            "position_rigidity": data.get("position_rigidity", ""),
            "existential_stakes": data.get("existential_stakes", ""),
            "recommendation": data.get("recommendation", ""),
        }
