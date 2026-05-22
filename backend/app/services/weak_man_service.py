"""WeakManService — Weak Man Fallacy Detection.

Detects weak man fallacy — attacking the weakest version of an
opponent's argument or the weakest proponent of a position, rather
than engaging the strongest version. Unlike straw man (which
misrepresents), weak man selects a real but unrepresentative example.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

WEAK_MAN_SYSTEM = """You are a weak man fallacy specialist. Given an argument engagement, assess whether the weakest version of the opposing position is being targeted rather than the strongest:

Key concepts:
- Weak man: attacking real but weakest version of opposing argument
- Straw man distinction: straw man fabricates; weak man cherry-picks
- Nutpicking: selecting the worst representatives of a group
- Nut-gathering: collecting extreme examples to characterize a position
- Representative sampling: are the targeted arguments representative?
- Strongest version: what would a sophisticated proponent actually argue?
- Selection bias in argumentation: choosing easy targets over hard ones

When weak man IS present:
- Responding to the worst tweet rather than the best paper
- Engaging fringe proponents rather than mainstream scholars
- Selecting the most extreme version of a position to refute
- "Look what this random person said" as refutation of a position
- Ignoring sophisticated versions while demolishing naive ones
- Choosing the least credentialed opponent to debate
- Refuting a position by its worst examples rather than its best arguments

When targeting weak versions IS appropriate:
- The weak version is actually the most common/influential one
- The critique explicitly acknowledges stronger versions exist
- The weak version is the one being acted upon (policy, decisions)
- The analysis addresses both weak and strong versions
- The weak version is what the specific interlocutor actually argued
- The goal is to show a spectrum, not to refute the whole position

Output JSON with: weak_man_present (bool), severity (none/mild/moderate/severe), position (what position is being engaged), target (what version is being attacked), strongest_version (what would the strongest version be), representativeness (how representative is the target), recommendation (targeting_appropriate/mild_cherry_picking/significant_weak_man/major_nutpicking/engage_strongest_version)."""

WEAK_MAN_PROMPT = """Detect weak man fallacy:

Position: {position}
Target: {target}
Strongest version: {strongest}
Selection: {selection}
Domain: {domain}
Context: {context}

Is the weakest version of the opposing position being targeted rather than the strongest? Return ONLY valid JSON."""


class WeakManService:
    """Detects weak man fallacy — attacking weakest version of opposing argument."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        position: str,
        *,
        target: str = "",
        strongest: str = "",
        selection: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect weak man fallacy."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=WEAK_MAN_PROMPT.format(
                position=position,
                target=target or "Not specified",
                strongest=strongest or "Not specified",
                selection=selection or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=WEAK_MAN_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "position": position[:200],
            "weak_man_present": data.get("weak_man_present", False),
            "severity": data.get("severity", ""),
            "target": data.get("target", ""),
            "strongest_version": data.get("strongest_version", ""),
            "representativeness": data.get("representativeness", ""),
            "recommendation": data.get("recommendation", ""),
        }
