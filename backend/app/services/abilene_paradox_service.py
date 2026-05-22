"""AbileneParadoxService — Abilene Paradox Detection.

Detects Abilene paradox — a group collectively decides on a course
of action that no individual member actually wants, because each
assumes the others want it. Jerry Harvey (1974). Everyone goes along
with what they think the group wants, but no one actually wants it.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

ABILENE_PARADOX_SYSTEM = """You are an Abilene paradox specialist. Given a group decision, assess whether the group is agreeing to something no individual member actually wants:

Key concepts (Harvey, 1974):
- Abilene paradox: group agrees to what no individual wants
- Pluralistic ignorance overlap: everyone assumes others want it
- False consensus: each person thinks they're the only dissenter
- Agreement without agreement: surface consensus, private disagreement
- Social pressure: fear of being the one to object
- Preference falsification: publicly supporting what you privately oppose
- Action anxiety: fear of consequences of speaking up

When Abilene paradox IS present:
- The group decision doesn't reflect any individual's actual preference
- People go along because they think others want it
- Private conversations reveal widespread disagreement with the decision
- No one can identify who actually wanted this outcome
- The decision was made by default rather than genuine consensus
- People are surprised to learn others also didn't want it
- "I thought you wanted to" is a common refrain

When group agreement IS genuine:
- Individual preferences were explicitly solicited
- Dissent was possible and some was expressed
- The decision reflects a genuine compromise
- People can articulate why they support it (not just going along)
- Anonymous polling would yield similar results
- The decision process included space for objection
- At least some members genuinely advocate for the choice

Output JSON with: abilene_paradox_present (bool), severity (none/mild/moderate/severe), decision (what was decided), group (who is involved), individual_preferences (what do individuals actually want), false_consensus (what consensus is assumed), dissent_suppression (why aren't people speaking up), recommendation (consensus_genuine/mild_conformity/significant_abilene/major_false_agreement/poll_individual_preferences)."""

ABILENE_PARADOX_PROMPT = """Detect Abilene paradox:

Decision: {decision}
Group: {group}
Individual preferences: {preferences}
Dissent: {dissent}
Domain: {domain}
Context: {context}

Is this group agreeing to something no individual member actually wants? Return ONLY valid JSON."""


class AbileneParadoxService:
    """Detects Abilene paradox — group agreeing to what no one wants."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        decision: str,
        *,
        group: str = "",
        preferences: str = "",
        dissent: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect Abilene paradox."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=ABILENE_PARADOX_PROMPT.format(
                decision=decision,
                group=group or "Not specified",
                preferences=preferences or "Not specified",
                dissent=dissent or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=ABILENE_PARADOX_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "decision": decision[:200],
            "abilene_paradox_present": data.get("abilene_paradox_present", False),
            "severity": data.get("severity", ""),
            "individual_preferences": data.get("individual_preferences", ""),
            "false_consensus": data.get("false_consensus", ""),
            "dissent_suppression": data.get("dissent_suppression", ""),
            "recommendation": data.get("recommendation", ""),
        }
