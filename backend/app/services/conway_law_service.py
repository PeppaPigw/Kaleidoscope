"""ConwayLawService — Conway's Law Detection.

Detects Conway's Law effects — organizations designing systems
that mirror their communication structure. Conway (1967):
"Any organization that designs a system will produce a design
whose structure is a copy of the organization's communication
structure." Applies to software architecture, product design,
API boundaries, and organizational dysfunction.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

CONWAY_SYSTEM = """You are a Conway's Law specialist. Given a system design or organizational structure, assess whether Conway's Law is shaping (or distorting) the architecture:

Key concepts (Conway, 1967):
- Conway's Law: system structure mirrors organizational communication structure
- Inverse Conway Maneuver: deliberately structuring teams to get desired architecture
- Team boundaries → API boundaries: where teams split, interfaces form
- Communication overhead → coupling: teams that talk a lot produce coupled systems
- Organizational silos → system silos: isolated teams produce isolated components
- Coordination costs: cross-team features are harder than within-team features

When Conway's Law IS creating problems:
- Architecture doesn't match domain boundaries, it matches team boundaries
- APIs exist because of org chart, not because of logical separation
- Cross-cutting concerns are poorly handled because they cross team boundaries
- System integration points reflect political boundaries, not technical ones
- Refactoring is blocked by organizational structure

When organizational alignment IS appropriate:
- Teams are deliberately structured around domain boundaries (inverse Conway)
- Communication patterns genuinely reflect the right decomposition
- Team autonomy enables independent deployment and scaling
- The organizational structure was designed for the desired architecture

Output JSON with: conway_effect_present (bool), severity (none/mild/moderate/severe), system_structure (how the system is organized), org_structure (how the organization is structured), mirror_points (where system boundaries match org boundaries), misalignment_points (where the system should be structured differently), team_boundary_apis (APIs that exist because of team splits, not domain logic), cross_cutting_failures (features that suffer from crossing team boundaries), inverse_conway_applied (bool — was org structure deliberately designed for architecture?), refactoring_blocked (what architectural improvements are blocked by org structure), communication_overhead (where coordination costs are highest), recommended_org_change (how teams should be restructured), recommended_arch_change (how architecture should change given current org), recommendation (alignment_appropriate/mild_conway_effect/significant_org_architecture_mismatch/severe_conway_dysfunction/apply_inverse_conway)."""

CONWAY_PROMPT = """Detect Conway's Law effects:

System/Architecture: {system}
Organization structure: {org_structure}
Team boundaries: {team_boundaries}
Pain points: {pain_points}
Domain: {domain}
Context: {context}

Is Conway's Law distorting the system architecture? Return ONLY valid JSON."""


class ConwayLawService:
    """Detects Conway's Law — system structure mirroring org communication structure."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        system: str,
        *,
        org_structure: str = "",
        team_boundaries: str = "",
        pain_points: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect Conway's Law effects."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=CONWAY_PROMPT.format(
                system=system,
                org_structure=org_structure or "Not specified",
                team_boundaries=team_boundaries or "Not specified",
                pain_points=pain_points or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=CONWAY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "system": system[:200],
            "conway_effect_present": data.get("conway_effect_present", False),
            "severity": data.get("severity", ""),
            "system_structure": data.get("system_structure", ""),
            "org_structure": data.get("org_structure", ""),
            "mirror_points": data.get("mirror_points", ""),
            "misalignment_points": data.get("misalignment_points", ""),
            "team_boundary_apis": data.get("team_boundary_apis", ""),
            "cross_cutting_failures": data.get("cross_cutting_failures", ""),
            "inverse_conway_applied": data.get("inverse_conway_applied", False),
            "refactoring_blocked": data.get("refactoring_blocked", ""),
            "communication_overhead": data.get("communication_overhead", ""),
            "recommended_org_change": data.get("recommended_org_change", ""),
            "recommended_arch_change": data.get("recommended_arch_change", ""),
            "recommendation": data.get("recommendation", ""),
        }
