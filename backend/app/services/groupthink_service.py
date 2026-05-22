"""GroupthinkService — Groupthink Detection (Janis).

Detects groupthink — a mode of thinking where desire for
conformity and harmony overrides realistic appraisal of
alternatives. Irving Janis (1972). Bay of Pigs, Challenger
disaster, and countless corporate failures. The group
collectively suppresses dissent and maintains illusions.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

GROUPTHINK_SYSTEM = """You are a groupthink specialist (Janis model). Given a group decision-making process, assess whether groupthink symptoms are present:

Janis's 8 symptoms:
1. Illusion of invulnerability — excessive optimism, extreme risk-taking
2. Collective rationalization — discounting warnings, not reconsidering assumptions
3. Belief in inherent morality — ignoring ethical consequences
4. Stereotyped views of out-groups — seeing opponents as evil/stupid/weak
5. Direct pressure on dissenters — members pressured not to express contrary views
6. Self-censorship — individuals withhold dissenting views
7. Illusion of unanimity — silence interpreted as agreement
8. Self-appointed mindguards — members protect group from adverse information

Antecedent conditions:
- High group cohesiveness
- Insulation from outside experts
- Lack of methodical procedures
- Directive leadership
- High stress with low hope of better solution

Output JSON with: groupthink_present (bool), severity (none/mild/moderate/severe/extreme), symptoms_present (list of which Janis symptoms are active), antecedent_conditions (which conditions are met), illusion_of_invulnerability (bool), collective_rationalization (bool), pressure_on_dissenters (bool), self_censorship_likely (bool), illusion_of_unanimity (bool), mindguards_present (bool), group_cohesiveness (low/moderate/high/extreme), insulation_from_experts (bool), directive_leadership (bool), dissent_channels (do safe channels for disagreement exist?), devil_advocate_present (bool — is anyone assigned to challenge?), decision_quality_risk (0-1 — how much groupthink threatens decision quality), historical_analogues (similar groupthink failures), remedies (what could break the groupthink: devil's advocate, outside experts, anonymous input, subgroups), recommendation (healthy_consensus/mild_conformity_pressure/significant_groupthink/dangerous_groupthink/intervention_needed)."""

GROUPTHINK_PROMPT = """Detect groupthink:

Group/Decision: {group_decision}
Group dynamics: {dynamics}
Dissent observed: {dissent}
Decision process: {process}
Domain: {domain}
Context: {context}

Is groupthink at play? Return ONLY valid JSON."""


class GroupthinkService:
    """Detects groupthink (Janis) in group decision-making."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        group_decision: str,
        *,
        dynamics: str = "",
        dissent: str = "",
        process: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect groupthink."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=GROUPTHINK_PROMPT.format(
                group_decision=group_decision,
                dynamics=dynamics or "Not specified",
                dissent=dissent or "Not specified",
                process=process or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=GROUPTHINK_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "group_decision": group_decision[:200],
            "groupthink_present": data.get("groupthink_present", False),
            "severity": data.get("severity", ""),
            "symptoms_present": data.get("symptoms_present", []),
            "antecedent_conditions": data.get("antecedent_conditions", []),
            "illusion_of_invulnerability": data.get("illusion_of_invulnerability", False),
            "collective_rationalization": data.get("collective_rationalization", False),
            "pressure_on_dissenters": data.get("pressure_on_dissenters", False),
            "self_censorship_likely": data.get("self_censorship_likely", False),
            "illusion_of_unanimity": data.get("illusion_of_unanimity", False),
            "mindguards_present": data.get("mindguards_present", False),
            "group_cohesiveness": data.get("group_cohesiveness", ""),
            "insulation_from_experts": data.get("insulation_from_experts", False),
            "directive_leadership": data.get("directive_leadership", False),
            "dissent_channels": data.get("dissent_channels", ""),
            "decision_quality_risk": data.get("decision_quality_risk", 0),
            "historical_analogues": data.get("historical_analogues", []),
            "remedies": data.get("remedies", []),
            "recommendation": data.get("recommendation", ""),
        }
