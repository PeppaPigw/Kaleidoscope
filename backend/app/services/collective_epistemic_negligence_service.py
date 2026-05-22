"""CollectiveEpistemicNegligenceService — Collective Epistemic Negligence Detection.

Detects collective epistemic negligence — when groups fail to
investigate what they should know, where no individual is negligent
but the collective fails its epistemic responsibilities.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

COLLECTIVE_EPISTEMIC_NEGLIGENCE_SYSTEM = """You are a collective epistemic negligence specialist. Given a group knowledge situation, assess whether collective negligence exists:

Key concepts:
- Collective epistemic negligence: group fails to know what it should
- Distributed responsibility failure: no one responsible so no one acts
- Bystander epistemology: everyone assumes someone else will investigate
- Institutional ignorance: organizations not knowing what they should
- Systemic knowledge gaps: gaps no individual is responsible for
- Collective duty to know: group obligations to investigate
- Negligent ignorance: culpable failure to inquire

When collective epistemic negligence IS present:
- Group fails to investigate what it should know
- No individual responsible for collective knowledge gap
- Everyone assumes someone else will investigate
- Institution doesn't know what it should
- Systemic gaps exist that no one addresses
- Collective duty to know is unmet
- Ignorance is culpable at group level

When knowledge limitation is appropriate:
- Group has investigated proportionally to stakes
- Knowledge gaps acknowledged and tracked
- Responsibility for investigation assigned
- Institutional knowledge proportional to capacity
- Gaps addressed when discovered
- Collective duties met within constraints
- Limitations honest not negligent

Output JSON with: negligence_present (bool), severity (none/mild/moderate/severe), group (what group is negligent), should_know (what they should know), failure (how investigation failed), responsibility (how responsibility is distributed), recommendation (appropriate_knowledge_limitation/mild_investigation_gap/significant_collective_negligence/major_institutional_ignorance/assign_epistemic_responsibility)."""

COLLECTIVE_EPISTEMIC_NEGLIGENCE_PROMPT = """Detect collective epistemic negligence:

Group: {group}
What should be known: {should_know}
Investigation status: {investigation}
Responsibility assignment: {responsibility}
Domain: {domain}
Context: {context}

Is the group failing to investigate what it collectively should know? Return ONLY valid JSON."""


class CollectiveEpistemicNegligenceService:
    """Detects collective epistemic negligence — groups failing to know what they should."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        group: str,
        *,
        should_know: str = "",
        investigation: str = "",
        responsibility: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect collective epistemic negligence."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=COLLECTIVE_EPISTEMIC_NEGLIGENCE_PROMPT.format(
                group=group,
                should_know=should_know or "Not specified",
                investigation=investigation or "Not specified",
                responsibility=responsibility or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=COLLECTIVE_EPISTEMIC_NEGLIGENCE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "group": group[:200],
            "negligence_present": data.get("negligence_present", False),
            "severity": data.get("severity", ""),
            "should_know": data.get("should_know", ""),
            "failure": data.get("failure", ""),
            "responsibility": data.get("responsibility", ""),
            "recommendation": data.get("recommendation", ""),
        }
