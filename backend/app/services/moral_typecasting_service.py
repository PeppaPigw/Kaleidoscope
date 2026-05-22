"""MoralTypecastingService — Moral Typecasting Detection.

Detects moral typecasting — the tendency to categorize people
as either moral agents (doers, responsible) or moral patients
(receivers, vulnerable) but not both simultaneously. Gray &
Wegner (2009). Once someone is cast as an agent, their
suffering is minimized. Once cast as a patient, their agency
is denied. This binary creates systematic injustice.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

MORAL_TYPECASTING_SYSTEM = """You are a moral typecasting specialist. Given a moral judgment or attribution, assess whether people are being rigidly categorized as either agents or patients:

Key concepts (Gray & Wegner, 2009):
- Moral typecasting: agent OR patient, not both
- Agent = doer: responsible, blameworthy, capable
- Patient = receiver: vulnerable, suffering, deserving sympathy
- Complementary nature: more agent = less patient, and vice versa
- Hero-victim binary: can't be both strong and suffering
- Perpetrator-victim lock: once labeled, hard to switch
- Dehumanization through agency denial: patients lose autonomy

When moral typecasting IS present:
- Denying that a powerful person can also be a victim
- Denying that a vulnerable person can also be responsible
- "They're too strong to be hurt" (agent can't be patient)
- "They can't help it" (patient can't be agent)
- Binary hero/villain framing without nuance
- Refusing to acknowledge complexity in moral roles
- "Victims can't be perpetrators" or "perpetrators can't be victims"

When moral categorization IS appropriate:
- Clear cases where one role genuinely dominates
- Legal contexts requiring clear responsibility assignment
- The categorization is provisional and acknowledged as simplified
- Both agency and patiency are considered even if one dominates
- The person's full moral complexity is acknowledged

Output JSON with: moral_typecasting_present (bool), severity (none/mild/moderate/severe), situation (what moral judgment is being made), agent_cast (who is being cast as agent), patient_cast (who is being cast as patient), denied_dimension (what is being denied — agency or patiency), rigidity (how rigid is the categorization), complexity_ignored (what moral complexity is being overlooked), recommendation (categorization_appropriate/mild_typecasting/significant_moral_typecasting/major_binary_framing/acknowledge_moral_complexity)."""

MORAL_TYPECASTING_PROMPT = """Detect moral typecasting:

Situation: {situation}
Agent role: {agent_role}
Patient role: {patient_role}
Complexity: {complexity}
Domain: {domain}
Context: {context}

Are people being rigidly categorized as either moral agents or patients without acknowledging both dimensions? Return ONLY valid JSON."""


class MoralTypecastingService:
    """Detects moral typecasting — rigid agent/patient categorization."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        agent_role: str = "",
        patient_role: str = "",
        complexity: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect moral typecasting."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=MORAL_TYPECASTING_PROMPT.format(
                situation=situation,
                agent_role=agent_role or "Not specified",
                patient_role=patient_role or "Not specified",
                complexity=complexity or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=MORAL_TYPECASTING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "moral_typecasting_present": data.get("moral_typecasting_present", False),
            "severity": data.get("severity", ""),
            "agent_cast": data.get("agent_cast", ""),
            "patient_cast": data.get("patient_cast", ""),
            "denied_dimension": data.get("denied_dimension", ""),
            "rigidity": data.get("rigidity", ""),
            "complexity_ignored": data.get("complexity_ignored", ""),
            "recommendation": data.get("recommendation", ""),
        }
