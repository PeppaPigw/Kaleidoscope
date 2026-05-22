"""EpistemicBioluminescenceService — Epistemic Bioluminescence Detection.

Detects epistemic bioluminescence — ideas that generate their own
light in dark intellectual environments, attracting attention.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_BIOLUMINESCENCE_SYSTEM = """You are an epistemic bioluminescence specialist. Given an idea in a dark environment, assess whether it generates its own light:

Key concepts:
- Epistemic bioluminescence: ideas generating their own light
- Dark environment: intellectual darkness where nothing is visible
- Self-illumination: ideas that make themselves visible without external light
- Attraction: light attracting attention and other ideas
- Energy cost: metabolic cost of generating light
- Deception: light used to lure others into traps
- Communication: light used to signal between ideas

When epistemic bioluminescence IS present:
- Ideas generating their own light in dark environments
- Intellectual darkness where most things are invisible
- Ideas making themselves visible without external illumination
- Light attracting attention and drawing other ideas
- Energy cost of self-illumination
- Potential for deceptive use of self-generated light
- Light used for communication between ideas

When externally lit ideas are present:
- Ideas visible through external illumination
- Intellectual environment well-lit
- Ideas visible because of external light sources
- No self-generated attraction
- No energy cost for visibility
- No deceptive self-illumination
- Communication through normal channels

Output JSON with: bioluminescence_present (bool), severity (none/mild/moderate/severe), idea (what idea generates light), darkness (what dark environment), attraction (what the light attracts), deception (whether light is deceptive), recommendation (externally_lit/mild_glow/significant_bioluminescence/major_self_illumination/assess_whether_light_is_honest)."""

EPISTEMIC_BIOLUMINESCENCE_PROMPT = """Detect epistemic bioluminescence:

Idea: {idea}
Darkness: {darkness}
Attraction: {attraction}
Deception: {deception}
Domain: {domain}
Context: {context}

Are ideas generating their own light in dark intellectual environments to attract attention? Return ONLY valid JSON."""


class EpistemicBioluminescenceService:
    """Detects epistemic bioluminescence — self-illuminating ideas in dark environments."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        idea: str,
        *,
        darkness: str = "",
        attraction: str = "",
        deception: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic bioluminescence."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_BIOLUMINESCENCE_PROMPT.format(
                idea=idea,
                darkness=darkness or "Not specified",
                attraction=attraction or "Not specified",
                deception=deception or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_BIOLUMINESCENCE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "idea": idea[:200],
            "bioluminescence_present": data.get("bioluminescence_present", False),
            "severity": data.get("severity", ""),
            "darkness": data.get("darkness", ""),
            "attraction": data.get("attraction", ""),
            "deception": data.get("deception", ""),
            "recommendation": data.get("recommendation", ""),
        }
