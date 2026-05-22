"""MissionCreepService — Mission Creep Detection.

Detects mission creep — the gradual expansion of a project, organization,
or initiative beyond its original goals, often without explicit decision
or acknowledgment. Each incremental expansion seems reasonable but the
cumulative drift can be enormous.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

MISSION_CREEP_SYSTEM = """You are a mission creep specialist. Given a project or organizational trajectory, assess whether scope has gradually expanded beyond original goals:

Key concepts:
- Mission creep: gradual expansion beyond original goals
- Scope creep overlap: each addition seems small but cumulative drift is large
- Incremental expansion: no single decision to expand, just gradual drift
- Original mandate: what was the initial purpose?
- Current scope: what is the current scope?
- Expansion justification: each step seems reasonable in isolation
- Accountability gap: no one decided to expand, it just happened

When mission creep IS present:
- Current activities bear little resemblance to original mandate
- Each expansion was individually justified but collectively transformative
- No explicit decision was made to change the mission
- Resources are spread across activities far from core purpose
- The organization can no longer clearly articulate its primary mission
- "While we're at it" additions have accumulated
- Original stakeholders wouldn't recognize the current scope

When scope expansion IS appropriate:
- The expansion was explicitly decided and acknowledged
- New activities genuinely serve the original mission
- Resources are adequate for the expanded scope
- The expansion reflects genuine learning about what's needed
- Stakeholders were consulted about the expansion
- The original mission is still being served effectively
- The expansion has clear boundaries and success criteria

Output JSON with: mission_creep_present (bool), severity (none/mild/moderate/severe), entity (what project/organization), original_mission (what was the original goal), current_scope (what is the current scope), expansion_path (how did it expand), explicit_decision (was expansion explicitly decided), recommendation (expansion_appropriate/mild_scope_drift/significant_mission_creep/major_mandate_abandonment/return_to_core_mission)."""

MISSION_CREEP_PROMPT = """Detect mission creep:

Entity: {entity}
Original mission: {original}
Current scope: {current}
Expansion: {expansion}
Domain: {domain}
Context: {context}

Has this project or organization gradually expanded beyond its original goals without explicit decision? Return ONLY valid JSON."""


class MissionCreepService:
    """Detects mission creep — gradual expansion beyond original goals."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        entity: str,
        *,
        original: str = "",
        current: str = "",
        expansion: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect mission creep."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=MISSION_CREEP_PROMPT.format(
                entity=entity,
                original=original or "Not specified",
                current=current or "Not specified",
                expansion=expansion or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=MISSION_CREEP_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "entity": entity[:200],
            "mission_creep_present": data.get("mission_creep_present", False),
            "severity": data.get("severity", ""),
            "original_mission": data.get("original_mission", ""),
            "current_scope": data.get("current_scope", ""),
            "expansion_path": data.get("expansion_path", ""),
            "explicit_decision": data.get("explicit_decision", ""),
            "recommendation": data.get("recommendation", ""),
        }
