"""IronLawBureaucracyService — Iron Law of Bureaucracy Detection.

Detects iron law of bureaucracy — in any organization, people devoted
to the benefit of the organization itself always gain control over
those dedicated to the organization's stated purpose. Jerry Pournelle.
The bureaucrats who serve the bureaucracy outcompete those who serve
the mission.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

IRON_LAW_BUREAUCRACY_SYSTEM = """You are an iron law of bureaucracy specialist. Given an organizational dynamic, assess whether those devoted to the organization itself have gained control over those devoted to its mission:

Key concepts (Pournelle):
- Iron law: bureaucracy-servers outcompete mission-servers
- Two types: those who serve the mission vs those who serve the organization
- Process over purpose: procedures become more important than outcomes
- Administrative capture: administrators control the organization
- Mission subordination: the stated purpose becomes secondary
- Procedural compliance: following rules matters more than achieving goals
- Institutional inertia: the organization resists change that threatens its structure

When iron law IS present:
- Administrative processes take priority over mission outcomes
- People who follow procedures are rewarded over those who achieve results
- The organization's internal needs dominate over external mission
- Meetings about meetings, reports about reports
- Those who challenge inefficiency are punished
- Resources flow to administration rather than mission delivery
- Success is measured by compliance rather than impact

When organizational focus IS appropriate:
- Administrative functions genuinely support the mission
- Process exists to prevent known failure modes
- Organizational health enables better mission delivery
- Compliance serves legitimate accountability
- Internal investment builds capacity for future mission work
- The balance between process and purpose is explicitly managed
- Administrative overhead is proportional to organizational complexity

Output JSON with: iron_law_present (bool), severity (none/mild/moderate/severe), organization (what organization), mission (stated purpose), bureaucratic_behavior (how bureaucracy dominates), mission_subordination (how mission is being subordinated), power_structure (who controls the organization), recommendation (administration_appropriate/mild_bureaucratic_drift/significant_iron_law/major_mission_capture/realign_with_mission)."""

IRON_LAW_BUREAUCRACY_PROMPT = """Detect iron law of bureaucracy:

Organization: {organization}
Mission: {mission}
Behavior: {behavior}
Power structure: {power}
Domain: {domain}
Context: {context}

Have those devoted to the organization itself gained control over those devoted to its mission? Return ONLY valid JSON."""


class IronLawBureaucracyService:
    """Detects iron law of bureaucracy — bureaucracy-servers outcompeting mission-servers."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        organization: str,
        *,
        mission: str = "",
        behavior: str = "",
        power: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect iron law of bureaucracy."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=IRON_LAW_BUREAUCRACY_PROMPT.format(
                organization=organization,
                mission=mission or "Not specified",
                behavior=behavior or "Not specified",
                power=power or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=IRON_LAW_BUREAUCRACY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "organization": organization[:200],
            "iron_law_present": data.get("iron_law_present", False),
            "severity": data.get("severity", ""),
            "bureaucratic_behavior": data.get("bureaucratic_behavior", ""),
            "mission_subordination": data.get("mission_subordination", ""),
            "power_structure": data.get("power_structure", ""),
            "recommendation": data.get("recommendation", ""),
        }
