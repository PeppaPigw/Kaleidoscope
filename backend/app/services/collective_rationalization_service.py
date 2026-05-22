"""CollectiveRationalizationService — Collective Rationalization Detection.

Detects collective rationalization — groups collectively constructing
justifications for predetermined conclusions, creating shared
narratives that resist individual dissent.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

COLLECTIVE_RATIONALIZATION_SYSTEM = """You are a collective rationalization specialist. Given a group conclusion, assess whether the group is collectively constructing justifications for a predetermined outcome:

Key concepts:
- Collective rationalization: group co-constructing justification
- Predetermined conclusion: outcome decided before reasoning
- Shared narrative: story that resists individual challenge
- Social reinforcement: members rewarding conforming reasons
- Dissent suppression: challenges to narrative discouraged
- Motivated collective reasoning: group reasoning toward desired end
- Collaborative confabulation: jointly creating post-hoc explanations

When collective rationalization IS present:
- Conclusion appears predetermined before evidence examined
- Group members reinforce each other's justifications
- Dissenting reasons suppressed or ignored
- Narrative becomes more elaborate over time without new evidence
- Individual members wouldn't reach same conclusion alone
- Social pressure to accept group narrative
- Evidence selectively cited to support predetermined conclusion

When group reasoning is genuine:
- Conclusion emerges from evidence examination
- Dissent welcomed and engaged with
- Members change positions based on evidence
- Reasoning precedes conclusion
- Individual members reach similar conclusions independently
- Counter-evidence genuinely considered
- Narrative simplifies over time as understanding improves

Output JSON with: rationalization_present (bool), severity (none/mild/moderate/severe), conclusion (what group concluded), predetermined (whether conclusion was predetermined), dissent_handling (how dissent is treated), reinforcement (how members reinforce narrative), recommendation (genuine_reasoning/mild_rationalization/significant_collective_confabulation/major_predetermined_narrative/encourage_dissent)."""

COLLECTIVE_RATIONALIZATION_PROMPT = """Detect collective rationalization:

Conclusion: {conclusion}
Process: {process}
Dissent: {dissent}
Evidence handling: {evidence_handling}
Domain: {domain}
Context: {context}

Is this group collectively rationalizing a predetermined conclusion? Return ONLY valid JSON."""


class CollectiveRationalizationService:
    """Detects collective rationalization — group justification of predetermined conclusions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        conclusion: str,
        *,
        process: str = "",
        dissent: str = "",
        evidence_handling: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect collective rationalization."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=COLLECTIVE_RATIONALIZATION_PROMPT.format(
                conclusion=conclusion,
                process=process or "Not specified",
                dissent=dissent or "Not specified",
                evidence_handling=evidence_handling or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=COLLECTIVE_RATIONALIZATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "conclusion": conclusion[:200],
            "rationalization_present": data.get("rationalization_present", False),
            "severity": data.get("severity", ""),
            "predetermined": data.get("predetermined", ""),
            "dissent_handling": data.get("dissent_handling", ""),
            "reinforcement": data.get("reinforcement", ""),
            "recommendation": data.get("recommendation", ""),
        }
