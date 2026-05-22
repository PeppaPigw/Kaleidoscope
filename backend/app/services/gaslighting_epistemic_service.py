"""GaslightingEpistemicService — Epistemic Gaslighting Detection.

Detects epistemic gaslighting — making someone doubt their own
justified beliefs through manipulation rather than evidence.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

GASLIGHTING_EPISTEMIC_SYSTEM = """You are an epistemic gaslighting specialist. Given a discourse interaction, assess whether someone is being made to doubt their justified beliefs through manipulation:

Key concepts:
- Epistemic gaslighting: making someone doubt justified beliefs
- Reality denial: denying what someone has directly experienced
- Memory manipulation: making someone doubt their own memory
- Perception undermining: undermining someone's perceptual reliability
- Competence questioning: questioning someone's epistemic competence
- Isolation from validation: cutting off sources of epistemic support
- Confidence erosion: systematically eroding epistemic confidence

When epistemic gaslighting IS present:
- Justified beliefs being undermined through manipulation
- Direct experience being denied or reinterpreted
- Memory being questioned without legitimate basis
- Perceptual reliability being undermined strategically
- Epistemic competence questioned to control
- Sources of validation being cut off
- Confidence eroded systematically not through evidence

When legitimate disagreement is present:
- Beliefs challenged through evidence and argument
- Experience reinterpreted with good reason
- Memory questioned with legitimate basis
- Perceptual reliability discussed honestly
- Competence assessed fairly
- Multiple perspectives offered genuinely
- Confidence adjusted through evidence

Output JSON with: gaslighting_present (bool), severity (none/mild/moderate/severe), interaction (what interaction occurs), manipulation (how beliefs are undermined), justified_belief (what justified belief is targeted), method (method of manipulation), recommendation (legitimate_disagreement/mild_undermining/significant_epistemic_gaslighting/major_reality_denial/respect_epistemic_autonomy)."""

GASLIGHTING_EPISTEMIC_PROMPT = """Detect epistemic gaslighting:

Interaction: {interaction}
Belief targeted: {belief}
Method used: {method}
Effect on target: {effect}
Domain: {domain}
Context: {context}

Is someone being made to doubt their justified beliefs through manipulation? Return ONLY valid JSON."""


class GaslightingEpistemicService:
    """Detects epistemic gaslighting — undermining justified beliefs through manipulation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        interaction: str,
        *,
        belief: str = "",
        method: str = "",
        effect: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic gaslighting."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=GASLIGHTING_EPISTEMIC_PROMPT.format(
                interaction=interaction,
                belief=belief or "Not specified",
                method=method or "Not specified",
                effect=effect or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=GASLIGHTING_EPISTEMIC_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "interaction": interaction[:200],
            "gaslighting_present": data.get("gaslighting_present", False),
            "severity": data.get("severity", ""),
            "manipulation": data.get("manipulation", ""),
            "justified_belief": data.get("justified_belief", ""),
            "method": data.get("method", ""),
            "recommendation": data.get("recommendation", ""),
        }
