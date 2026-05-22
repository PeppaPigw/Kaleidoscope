"""SanewashingService — Sanewashing Detection.

Detects sanewashing — making extreme, radical, or dangerous positions
sound reasonable by restating them in moderate, professional language.
The substance remains extreme but the presentation is sanitized to
bypass critical evaluation.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

SANEWASHING_SYSTEM = """You are a sanewashing specialist. Given a communication, assess whether extreme positions are being made to sound reasonable through moderate presentation:

Key concepts:
- Sanewashing: restating extreme positions in moderate language
- Normalization through tone: substance unchanged, presentation sanitized
- Professional veneer: using institutional language to legitimize extremism
- Euphemistic reframing: replacing alarming terms with neutral ones
- Tone policing inversion: using calm tone to bypass content scrutiny
- Mainstreaming: moving fringe ideas into acceptable discourse
- Respectability laundering: making radical ideas seem establishment

When sanewashing IS present:
- Extreme policy positions stated in calm, professional language
- Radical proposals framed as "common sense" or "moderate"
- Dangerous ideas presented with academic or institutional framing
- The substance would alarm if stated plainly but doesn't in this form
- Euphemisms replace accurate but alarming descriptions
- Fringe positions presented as mainstream consensus
- The moderate tone is doing the persuasive work, not the evidence

When moderate presentation IS appropriate:
- The position is genuinely moderate, not just presented that way
- Professional language serves clarity, not concealment
- The substance is accurately represented by the moderate framing
- Calm discussion of controversial topics for genuine understanding
- Academic analysis of extreme positions (studying, not advocating)
- The audience can evaluate substance independently of tone
- Nuance genuinely exists and moderate language captures it

Output JSON with: sanewashing_present (bool), severity (none/mild/moderate/severe), communication (what is being communicated), surface_framing (how it's presented), actual_substance (what it actually proposes), gap (difference between presentation and substance), plain_language (how it would sound stated plainly), recommendation (moderate_appropriate/mild_euphemism/significant_sanewashing/major_normalization/state_plainly)."""

SANEWASHING_PROMPT = """Detect sanewashing:

Communication: {communication}
Framing: {framing}
Substance: {substance}
Plain version: {plain_version}
Domain: {domain}
Context: {context}

Is an extreme position being made to sound reasonable through moderate presentation? Return ONLY valid JSON."""


class SanewashingService:
    """Detects sanewashing — making extreme positions sound moderate."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        communication: str,
        *,
        framing: str = "",
        substance: str = "",
        plain_version: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect sanewashing."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=SANEWASHING_PROMPT.format(
                communication=communication,
                framing=framing or "Not specified",
                substance=substance or "Not specified",
                plain_version=plain_version or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=SANEWASHING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "communication": communication[:200],
            "sanewashing_present": data.get("sanewashing_present", False),
            "severity": data.get("severity", ""),
            "surface_framing": data.get("surface_framing", ""),
            "actual_substance": data.get("actual_substance", ""),
            "gap": data.get("gap", ""),
            "plain_language": data.get("plain_language", ""),
            "recommendation": data.get("recommendation", ""),
        }
