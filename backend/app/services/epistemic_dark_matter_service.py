"""EpistemicDarkMatterService — Epistemic Dark Matter Detection.

Detects epistemic dark matter — invisible assumptions exerting
gravitational pull on reasoning without being acknowledged.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_DARK_MATTER_SYSTEM = """You are an epistemic dark matter specialist. Given a reasoning pattern, assess whether invisible assumptions are exerting unacknowledged influence:

Key concepts:
- Epistemic dark matter: invisible assumptions influencing reasoning
- Hidden assumptions: assumptions operating without acknowledgment
- Invisible influence: influence exerted without being seen
- Unacknowledged premises: premises operating without recognition
- Background beliefs: beliefs influencing without being examined
- Implicit frameworks: frameworks shaping thought without awareness
- Gravitational assumptions: assumptions pulling reasoning in directions

When epistemic dark matter IS present:
- Invisible assumptions exerting influence on reasoning
- Hidden assumptions operating without acknowledgment
- Influence exerted without being recognized
- Premises operating without being stated
- Background beliefs shaping conclusions unexamined
- Implicit frameworks directing thought without awareness
- Assumptions pulling reasoning without being identified

When transparent reasoning is present:
- Assumptions made explicit and examined
- Influence acknowledged and accounted for
- Premises stated and evaluated
- Background beliefs examined
- Frameworks made explicit
- Assumptions identified and assessed
- Reasoning transparent about its foundations

Output JSON with: dark_matter_present (bool), severity (none/mild/moderate/severe), reasoning (what reasoning is affected), hidden_assumptions (what assumptions are hidden), influence (how they influence reasoning), invisibility (why they remain invisible), recommendation (transparent_reasoning/mild_hidden_assumptions/significant_epistemic_dark_matter/major_invisible_influence/make_assumptions_explicit)."""

EPISTEMIC_DARK_MATTER_PROMPT = """Detect epistemic dark matter:

Reasoning: {reasoning}
Hidden assumptions: {assumptions}
Influence: {influence}
Visibility: {visibility}
Domain: {domain}
Context: {context}

Are invisible assumptions exerting unacknowledged influence on reasoning? Return ONLY valid JSON."""


class EpistemicDarkMatterService:
    """Detects epistemic dark matter — invisible assumptions influencing reasoning."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        reasoning: str,
        *,
        assumptions: str = "",
        influence: str = "",
        visibility: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic dark matter."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_DARK_MATTER_PROMPT.format(
                reasoning=reasoning,
                assumptions=assumptions or "Not specified",
                influence=influence or "Not specified",
                visibility=visibility or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_DARK_MATTER_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "reasoning": reasoning[:200],
            "dark_matter_present": data.get("dark_matter_present", False),
            "severity": data.get("severity", ""),
            "hidden_assumptions": data.get("hidden_assumptions", ""),
            "influence": data.get("influence", ""),
            "invisibility": data.get("invisibility", ""),
            "recommendation": data.get("recommendation", ""),
        }
