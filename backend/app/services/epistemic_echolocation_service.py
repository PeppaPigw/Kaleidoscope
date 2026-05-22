"""EpistemicEcholocationService — Epistemic Echolocation Detection.

Detects epistemic echolocation — navigating intellectual darkness
by emitting ideas and interpreting what bounces back.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ECHOLOCATION_SYSTEM = """You are an epistemic echolocation specialist. Given a navigation pattern, assess whether ideas are emitted and interpreted for navigation:

Key concepts:
- Epistemic echolocation: navigating by emitting and interpreting returns
- Emission: sending out ideas to see what comes back
- Interpretation: reading the returns to understand environment
- Frequency: how often ideas are emitted for navigation
- Doppler: detecting movement through frequency shifts in returns
- Beam width: how focused or broad the emissions are
- Clutter: noise in the returns making interpretation difficult

When epistemic echolocation IS present:
- Navigating intellectual darkness by emitting ideas
- Sending out ideas specifically to see what bounces back
- Interpreting returns to understand intellectual environment
- Regular emission of ideas for navigation purposes
- Detecting movement through changes in returns
- Focused or broad emissions depending on need
- Noise in returns making interpretation challenging

When visual navigation is present:
- Navigating through direct intellectual vision
- No need to emit ideas for navigation
- Direct observation of environment
- No regular probing needed
- Movement directly observable
- Full field of view available
- Clear observation without noise

Output JSON with: echolocation_present (bool), severity (none/mild/moderate/severe), emissions (what ideas are emitted), returns (what bounces back), navigation (what navigation results), clutter (what noise interferes), recommendation (visual_navigation/mild_probing/significant_echolocation/major_blind_navigation/improve_emission_interpretation)."""

EPISTEMIC_ECHOLOCATION_PROMPT = """Detect epistemic echolocation:

Emissions: {emissions}
Returns: {returns}
Navigation: {navigation}
Clutter: {clutter}
Domain: {domain}
Context: {context}

Is navigation happening by emitting ideas and interpreting what bounces back from the environment? Return ONLY valid JSON."""


class EpistemicEcholocationService:
    """Detects epistemic echolocation — navigating by emitting and interpreting returns."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        emissions: str,
        *,
        returns: str = "",
        navigation: str = "",
        clutter: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic echolocation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ECHOLOCATION_PROMPT.format(
                emissions=emissions,
                returns=returns or "Not specified",
                navigation=navigation or "Not specified",
                clutter=clutter or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ECHOLOCATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "emissions": emissions[:200],
            "echolocation_present": data.get("echolocation_present", False),
            "severity": data.get("severity", ""),
            "returns": data.get("returns", ""),
            "navigation": data.get("navigation", ""),
            "clutter": data.get("clutter", ""),
            "recommendation": data.get("recommendation", ""),
        }
