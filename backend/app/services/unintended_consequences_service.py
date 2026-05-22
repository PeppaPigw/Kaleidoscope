"""UnintendedConsequencesService — Unintended Consequences Detection.

Detects unintended consequences — actions producing unforeseen negative
effects that were not anticipated by the decision-makers. Merton (1936).
Includes both direct unintended effects and systemic ripple effects.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

UNINTENDED_CONSEQUENCES_SYSTEM = """You are an unintended consequences specialist. Given an action or policy, assess whether it is likely to produce or has produced significant unintended consequences:

Key concepts (Merton, 1936):
- Unintended consequences: effects not anticipated by the actor
- Perverse results: outcomes opposite to intention
- Unanticipated benefits: positive unintended effects
- System complexity: interconnected systems produce surprises
- Second-order effects: consequences of consequences
- Feedback loops: effects that amplify or dampen over time
- Merton's five causes: ignorance, error, imperious immediacy, values, self-defeating prophecy

When unintended consequences ARE likely:
- The system is complex with many interconnections
- Similar interventions have produced surprises historically
- The analysis considers only first-order effects
- Stakeholders who will be affected haven't been consulted
- The intervention changes incentives in ways not fully analyzed
- There's no monitoring for unexpected effects
- The action is irreversible or hard to reverse

When consequences ARE well-anticipated:
- Thorough systems analysis has been conducted
- Historical precedents have been studied
- Multiple stakeholder perspectives are considered
- Monitoring and feedback mechanisms are in place
- The intervention is reversible or can be adjusted
- Second and third-order effects have been mapped
- Scenario planning has explored failure modes

Output JSON with: unintended_consequences_likely (bool), severity (none/mild/moderate/severe), action (what action is taken), intended_effect (what was intended), unintended_effects (what unintended effects), mechanism (how unintended effects arise), reversibility (can effects be reversed), recommendation (well_anticipated/mild_oversight/significant_unintended_consequences/major_systemic_surprise/map_second_order_effects)."""

UNINTENDED_CONSEQUENCES_PROMPT = """Detect unintended consequences:

Action: {action}
Intended effect: {intended}
System complexity: {complexity}
Historical precedent: {precedent}
Domain: {domain}
Context: {context}

Is this action likely to produce significant unintended consequences? Return ONLY valid JSON."""


class UnintendedConsequencesService:
    """Detects unintended consequences — unforeseen negative effects of actions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        action: str,
        *,
        intended: str = "",
        complexity: str = "",
        precedent: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect unintended consequences."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=UNINTENDED_CONSEQUENCES_PROMPT.format(
                action=action,
                intended=intended or "Not specified",
                complexity=complexity or "Not specified",
                precedent=precedent or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=UNINTENDED_CONSEQUENCES_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "action": action[:200],
            "unintended_consequences_likely": data.get("unintended_consequences_likely", False),
            "severity": data.get("severity", ""),
            "unintended_effects": data.get("unintended_effects", ""),
            "mechanism": data.get("mechanism", ""),
            "reversibility": data.get("reversibility", ""),
            "recommendation": data.get("recommendation", ""),
        }
