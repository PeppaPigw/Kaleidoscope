"""EpistemicCausalExclusionService — Epistemic Causal Exclusion Detection.

Detects epistemic causal exclusion — excluding valid causal factors
to simplify explanation or support preferred narrative.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_CAUSAL_EXCLUSION_SYSTEM = """You are an epistemic causal exclusion specialist. Given exclusion of valid causal factors, assess causal exclusion:

Key concepts:
- Epistemic causal exclusion: excluding valid causal factors to simplify
- Factor omission: omitting relevant causal factors
- Convenient simplification: simplifying by excluding inconvenient causes
- Monocausal preference: preferring single-cause explanations
- Interaction blindness: blind to causal interactions
- Context exclusion: excluding contextual causal factors
- Structural cause exclusion: excluding structural/systemic causes

When epistemic causal exclusion IS present:
- Valid factors excluded
- Relevant factors omitted
- Simplification convenient
- Single cause preferred
- Interactions missed
- Context excluded
- Structural causes excluded

When no causal exclusion:
- All valid factors included
- Relevant factors considered
- Simplification principled
- Multiple causes considered
- Interactions examined
- Context included
- Structural causes considered

Output JSON with: causal_exclusion_detected (bool), severity (none/mild/moderate/severe), factor_omission (what factors omitted), monocausal_preference (what single cause preferred), interaction_blindness (what interactions missed), structural_exclusion (what structural causes excluded), recommendation (no_causal_exclusion/mild_factor_inclusion/significant_multicausal_analysis/major_intensive_causal_completeness/emergency_complete_causal_exclusion)."""

EPISTEMIC_CAUSAL_EXCLUSION_PROMPT = """Detect epistemic causal exclusion:

Factor omission: {factor_omission}
Monocausal preference: {monocausal_preference}
Interaction blindness: {interaction_blindness}
Structural exclusion: {structural_exclusion}
Domain: {domain}
Context: {context}

Are valid causal factors being excluded? Return ONLY valid JSON."""


class EpistemicCausalExclusionService:
    """Detects epistemic causal exclusion — valid factors excluded."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        factor_omission: str,
        *,
        monocausal_preference: str = "",
        interaction_blindness: str = "",
        structural_exclusion: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic causal exclusion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_CAUSAL_EXCLUSION_PROMPT.format(
                factor_omission=factor_omission,
                monocausal_preference=monocausal_preference or "Not specified",
                interaction_blindness=interaction_blindness or "Not specified",
                structural_exclusion=structural_exclusion or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_CAUSAL_EXCLUSION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "factor_omission": factor_omission[:200],
            "causal_exclusion_detected": data.get("causal_exclusion_detected", False),
            "severity": data.get("severity", ""),
            "monocausal_preference": data.get("monocausal_preference", ""),
            "interaction_blindness": data.get("interaction_blindness", ""),
            "structural_exclusion": data.get("structural_exclusion", ""),
            "recommendation": data.get("recommendation", ""),
        }
