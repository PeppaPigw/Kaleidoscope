"""EpistemicCollectiveDelusionService — Epistemic Collective Delusion Detection.

Detects epistemic collective delusion — shared false beliefs maintained by
a group despite clear contradicting evidence available to all members.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_COLLECTIVE_DELUSION_SYSTEM = """You are an epistemic collective delusion specialist. Given shared false beliefs, assess collective delusion:

Key concepts:
- Epistemic collective delusion: shared false beliefs despite evidence
- Mutual reinforcement: members confirm each other's false beliefs
- Evidence immunity: contradicting evidence dismissed collectively
- Shared narrative: agreed-upon false story
- Social pressure: dissent punished
- Reality substitution: group reality replaces actual reality
- Consensus as proof: agreement treated as evidence

When epistemic collective delusion IS present:
- Shared false beliefs
- Members confirm each other
- Evidence dismissed collectively
- Agreed false story
- Dissent punished
- Group reality substituted
- Agreement as evidence

When no collective delusion:
- Shared true beliefs
- Independent verification
- Evidence considered
- Accurate narrative
- Dissent welcomed
- Actual reality accepted
- Evidence as proof

Output JSON with: collective_delusion_detected (bool), severity (none/mild/moderate/severe), mutual_reinforcement (what confirming), evidence_immunity (what dismissing), social_pressure (what punishing), reality_substitution (what replacing), recommendation (no_collective_delusion/mild_reality_testing/significant_group_therapy/major_intensive_intervention/emergency_complete_substitution)."""

EPISTEMIC_COLLECTIVE_DELUSION_PROMPT = """Detect epistemic collective delusion:

Mutual reinforcement: {mutual_reinforcement}
Evidence immunity: {evidence_immunity}
Social pressure: {social_pressure}
Reality substitution: {reality_substitution}
Domain: {domain}
Context: {context}

Are there shared false beliefs maintained despite clear contradicting evidence? Return ONLY valid JSON."""


class EpistemicCollectiveDelusionService:
    """Detects epistemic collective delusion — shared false beliefs."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        mutual_reinforcement: str,
        *,
        evidence_immunity: str = "",
        social_pressure: str = "",
        reality_substitution: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic collective delusion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_COLLECTIVE_DELUSION_PROMPT.format(
                mutual_reinforcement=mutual_reinforcement,
                evidence_immunity=evidence_immunity or "Not specified",
                social_pressure=social_pressure or "Not specified",
                reality_substitution=reality_substitution or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_COLLECTIVE_DELUSION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "mutual_reinforcement": mutual_reinforcement[:200],
            "collective_delusion_detected": data.get("collective_delusion_detected", False),
            "severity": data.get("severity", ""),
            "evidence_immunity": data.get("evidence_immunity", ""),
            "social_pressure": data.get("social_pressure", ""),
            "reality_substitution": data.get("reality_substitution", ""),
            "recommendation": data.get("recommendation", ""),
        }
