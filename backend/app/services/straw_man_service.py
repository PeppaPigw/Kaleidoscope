"""StrawManService — Straw Man Detection.

Detects straw man fallacy — misrepresenting someone's argument
to make it easier to attack. Instead of addressing the actual
position, a weaker or distorted version is constructed and then
refuted, creating the illusion of having defeated the real argument.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

STRAW_MAN_SYSTEM = """You are a straw man fallacy specialist. Given a debate or argument, assess whether one party is misrepresenting the other's position:

Key concepts:
- Straw man: attacking a distorted version of the opponent's argument
- Steelmanning: the opposite — presenting the strongest version of an argument
- Misrepresentation: changing what someone actually said or meant
- Oversimplification: reducing a nuanced position to a caricature
- Extremification: making a moderate position sound extreme
- Selective quotation: taking words out of context to change meaning
- Weak man: attacking a real but unrepresentative version of a position

When straw man IS present:
- The rebuttal addresses a position the opponent didn't actually hold
- A nuanced argument is reduced to an extreme caricature
- "So you're saying..." followed by a distortion
- Attacking implications the opponent explicitly denied
- Ignoring qualifications and caveats in the original argument
- Substituting a weaker argument for the one actually made
- Refuting a position no one holds

When straw man is NOT present:
- The rebuttal accurately represents the opponent's position
- Logical implications are drawn that genuinely follow
- The opponent's position is quoted directly and in context
- Simplification is acknowledged as such
- The strongest version of the argument is addressed
- Disagreement is about the actual stated position
- The characterization would be accepted by the original arguer

Output JSON with: straw_man_present (bool), severity (none/mild/moderate/severe), original_position (what was actually argued), misrepresentation (how it was distorted), distortion_type (oversimplification/extremification/fabrication/selective_quotation), actual_rebuttal (what a fair response would address), recommendation (no_straw_man/mild_mischaracterization/significant_straw_man/major_position_fabrication/address_actual_argument)."""

STRAW_MAN_PROMPT = """Detect straw man:

Debate: {debate}
Original position: {original_position}
Characterization: {characterization}
Rebuttal: {rebuttal}
Domain: {domain}
Context: {context}

Does this misrepresent someone's argument to make it easier to attack? Return ONLY valid JSON."""


class StrawManService:
    """Detects straw man — misrepresenting arguments to attack a weaker version."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        debate: str,
        *,
        original_position: str = "",
        characterization: str = "",
        rebuttal: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect straw man."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=STRAW_MAN_PROMPT.format(
                debate=debate,
                original_position=original_position or "Not specified",
                characterization=characterization or "Not specified",
                rebuttal=rebuttal or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=STRAW_MAN_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "debate": debate[:200],
            "straw_man_present": data.get("straw_man_present", False),
            "severity": data.get("severity", ""),
            "original_position": data.get("original_position", ""),
            "misrepresentation": data.get("misrepresentation", ""),
            "distortion_type": data.get("distortion_type", ""),
            "recommendation": data.get("recommendation", ""),
        }
