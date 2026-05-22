"""EpistemicCollectiveGroupthinkService — Epistemic Collective Groupthink Detection.

Detects epistemic collective groupthink — group conformity suppressing
dissent, independent judgment, and critical evaluation.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_COLLECTIVE_GROUPTHINK_SYSTEM = """You are an epistemic collective groupthink specialist. Given group decision dynamics, assess whether conformity pressure is suppressing dissent and critical evaluation:

Key concepts:
- Epistemic groupthink: group conformity overriding independent evaluation
- Conformity pressure: pressure to align with the group position
- Dissent suppression: disagreement discouraged or punished
- Illusion of unanimity: silence or compliance mistaken for agreement
- Self-censorship: members withholding doubts
- Critical evaluation collapse: alternatives and risks not examined
- Loyalty over truth: agreement treated as commitment to the group

When epistemic groupthink IS present:
- Conformity pressure overrides judgment
- Dissent suppressed or punished
- Silence treated as consensus
- Members censor doubts
- Alternatives not critically evaluated
- Loyalty valued over accuracy
- Risks minimized to preserve agreement

When no groupthink:
- Independent judgment protected
- Dissent invited and examined
- Agreement distinguished from silence
- Doubts shared safely
- Alternatives critically evaluated
- Accuracy valued over loyalty
- Risks assessed openly

Output JSON with: groupthink_detected (bool), severity (none/mild/moderate/severe), dissent_suppression (what dissent is suppressed), illusion_of_unanimity (what false consensus appears), self_censorship (what doubts are withheld), recommendation (no_groupthink/mild_dissent_protection/significant_critical_review/major_independent_red_team/emergency_break_conformity_pressure)."""

EPISTEMIC_COLLECTIVE_GROUPTHINK_PROMPT = """Detect epistemic collective groupthink:

Conformity pressure: {conformity_pressure}
Dissent suppression: {dissent_suppression}
Illusion of unanimity: {illusion_of_unanimity}
Self-censorship: {self_censorship}
Domain: {domain}
Context: {context}

Is group conformity suppressing dissent and critical evaluation? Return ONLY valid JSON."""


class EpistemicCollectiveGroupthinkService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        conformity_pressure: str,
        *,
        dissent_suppression: str = "",
        illusion_of_unanimity: str = "",
        self_censorship: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_COLLECTIVE_GROUPTHINK_PROMPT.format(
                conformity_pressure=conformity_pressure,
                dissent_suppression=dissent_suppression or "Not specified",
                illusion_of_unanimity=illusion_of_unanimity or "Not specified",
                self_censorship=self_censorship or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_COLLECTIVE_GROUPTHINK_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "conformity_pressure": conformity_pressure[:200],
            "groupthink_detected": data.get("groupthink_detected", False),
            "severity": data.get("severity", ""),
            "dissent_suppression": data.get("dissent_suppression", ""),
            "illusion_of_unanimity": data.get("illusion_of_unanimity", ""),
            "self_censorship": data.get("self_censorship", ""),
            "recommendation": data.get("recommendation", ""),
        }
