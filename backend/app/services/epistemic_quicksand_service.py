"""EpistemicQuicksandService — Epistemic Quicksand Detection.

Detects epistemic quicksand — seemingly solid ground that gives way
under weight, trapping those who step on it.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_QUICKSAND_SYSTEM = """You are an epistemic quicksand specialist. Given a reasoning situation, assess whether seemingly solid ground gives way and traps:

Key concepts:
- Epistemic quicksand: solid-seeming ground giving way
- Entrapment: becoming more trapped with effort to escape
- False solidity: appearing solid but actually unstable
- Sinking deeper: efforts to escape making things worse
- Struggle amplification: struggling making entrapment worse
- Hidden instability: instability hidden until stepped on
- Progressive trapping: progressive entrapment over time

When epistemic quicksand IS present:
- Seemingly solid ground giving way under weight
- Becoming more trapped with effort to escape
- Appearing solid but actually unstable
- Efforts to escape making situation worse
- Struggling making entrapment worse
- Instability hidden until committed
- Progressive entrapment over time

When solid ground is present:
- Ground actually solid and reliable
- Able to move freely without entrapment
- Stability genuine not illusory
- Efforts productive not counterproductive
- Engagement not creating entrapment
- Stability visible and verifiable
- Freedom of movement maintained

Output JSON with: quicksand_present (bool), severity (none/mild/moderate/severe), situation (what situation exists), false_solidity (what appears solid), entrapment (how entrapment occurs), escape_difficulty (why escape is hard), recommendation (solid_ground/mild_instability/significant_quicksand/major_entrapment/stop_struggling_change_approach)."""

EPISTEMIC_QUICKSAND_PROMPT = """Detect epistemic quicksand:

Situation: {situation}
False solidity: {false_solidity}
Entrapment: {entrapment}
Escape difficulty: {escape_difficulty}
Domain: {domain}
Context: {context}

Does seemingly solid ground give way and trap those who step on it? Return ONLY valid JSON."""


class EpistemicQuicksandService:
    """Detects epistemic quicksand — solid-seeming ground that traps."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        false_solidity: str = "",
        entrapment: str = "",
        escape_difficulty: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic quicksand."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_QUICKSAND_PROMPT.format(
                situation=situation,
                false_solidity=false_solidity or "Not specified",
                entrapment=entrapment or "Not specified",
                escape_difficulty=escape_difficulty or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_QUICKSAND_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "quicksand_present": data.get("quicksand_present", False),
            "severity": data.get("severity", ""),
            "false_solidity": data.get("false_solidity", ""),
            "entrapment": data.get("entrapment", ""),
            "escape_difficulty": data.get("escape_difficulty", ""),
            "recommendation": data.get("recommendation", ""),
        }
