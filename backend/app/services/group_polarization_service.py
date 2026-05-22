"""GroupPolarizationService — Group Polarization Detection.

Detects group polarization — tendency for groups to make
decisions that are more extreme than the initial inclination
of individual members. Moscovici & Zavalloni (1969).
Discussion pushes groups toward more extreme positions.
Cautious individuals become more cautious; risky individuals
become more risky after group discussion.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

GROUP_POLARIZATION_SYSTEM = """You are a group polarization specialist. Given a group decision or discussion outcome, assess whether the group has moved to a more extreme position than individual members would hold:

Key concepts (Moscovici & Zavalloni, 1969):
- Group polarization: group decisions more extreme than individual average
- Risky shift: groups taking more risk than individuals
- Cautious shift: groups being more cautious than individuals
- Social comparison: wanting to be more extreme than average
- Persuasive arguments: hearing new arguments in one direction
- Group identity: extremity as group differentiation
- Echo chamber effect: reinforcement of shared views
- Groupthink interaction: pressure toward consensus amplifies extremity

When group polarization IS present:
- Group decisions more extreme than any individual initially held
- Discussion pushing toward one extreme rather than moderation
- "We all agree, so we should go even further"
- Moderate positions disappearing after group discussion
- Risk-taking increasing after team discussion
- Positions hardening rather than nuancing through dialogue
- Dissent being treated as disloyalty rather than balance

When the group position IS appropriate:
- The extreme position is supported by evidence discussed
- Individual positions were genuinely updated by new information
- The group considered and rejected moderate alternatives on merit
- Dissenting views were heard and addressed
- The position would survive individual reflection post-discussion

Output JSON with: group_polarization_present (bool), severity (none/mild/moderate/severe), situation (what group decision is being made), initial_positions (what were individual starting positions), group_outcome (what did the group decide), extremity_shift (how much more extreme is the group position), mechanism (social comparison, persuasive arguments, or identity), dissent_handling (how was disagreement handled), recommendation (position_appropriate/mild_polarization/significant_extremity_shift/major_group_polarization/seek_outside_perspectives)."""

GROUP_POLARIZATION_PROMPT = """Detect group polarization:

Situation: {situation}
Discussion: {discussion}
Outcome: {outcome}
Dissent: {dissent}
Domain: {domain}
Context: {context}

Has group discussion pushed the decision to a more extreme position? Return ONLY valid JSON."""


class GroupPolarizationService:
    """Detects group polarization — groups moving to more extreme positions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        discussion: str = "",
        outcome: str = "",
        dissent: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect group polarization."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=GROUP_POLARIZATION_PROMPT.format(
                situation=situation,
                discussion=discussion or "Not specified",
                outcome=outcome or "Not specified",
                dissent=dissent or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=GROUP_POLARIZATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "group_polarization_present": data.get("group_polarization_present", False),
            "severity": data.get("severity", ""),
            "initial_positions": data.get("initial_positions", ""),
            "group_outcome": data.get("group_outcome", ""),
            "extremity_shift": data.get("extremity_shift", ""),
            "mechanism": data.get("mechanism", ""),
            "dissent_handling": data.get("dissent_handling", ""),
            "recommendation": data.get("recommendation", ""),
        }
