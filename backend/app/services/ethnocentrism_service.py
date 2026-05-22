"""EthnocentrismService — Ethnocentrism Detection.

Detects ethnocentrism — evaluating other cultures, groups, or
perspectives solely by the standards of one's own, treating
one's own perspective as universal or normative.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

ETHNOCENTRISM_SYSTEM = """You are an ethnocentrism specialist. Given an evaluation or claim, assess whether one cultural perspective is being treated as universal:

Key concepts:
- Ethnocentrism: judging others by one's own cultural standards
- Cultural universalism: treating local norms as universal
- WEIRD bias: assuming Western, Educated, Industrialized, Rich, Democratic norms
- Normative imperialism: imposing one group's standards on others
- Cultural blindness: inability to see own cultural assumptions
- Default perspective: treating one viewpoint as neutral/objective
- Othering: defining groups by deviation from one's own norms

When ethnocentrism IS present:
- One cultural perspective treated as universal standard
- Other cultures evaluated by standards they don't share
- Own cultural assumptions invisible/unexamined
- Deviation from own norms treated as deficiency
- Local standards presented as objective truth
- Other perspectives described as lacking rather than different
- WEIRD assumptions treated as human universals

When cultural evaluation is appropriate:
- Standards applied are genuinely universal (human rights)
- Own cultural position acknowledged
- Multiple perspectives considered
- Evaluation criteria justified independently
- Cultural context of standards acknowledged
- Difference described as difference, not deficiency
- Cross-cultural comparison done with awareness

Output JSON with: ethnocentrism_present (bool), severity (none/mild/moderate/severe), evaluation (what is evaluated), assumed_standard (what standard is assumed universal), cultural_position (evaluator's cultural position), alternative_standards (what other standards exist), recommendation (appropriate_evaluation/mild_cultural_assumption/significant_ethnocentrism/major_normative_imperialism/acknowledge_cultural_position)."""

ETHNOCENTRISM_PROMPT = """Detect ethnocentrism:

Evaluation: {evaluation}
Standard applied: {standard}
Cultural position: {position}
Subject evaluated: {subject}
Domain: {domain}
Context: {context}

Is one cultural perspective being treated as universal or normative? Return ONLY valid JSON."""


class EthnocentrismService:
    """Detects ethnocentrism — treating one cultural perspective as universal."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        evaluation: str,
        *,
        standard: str = "",
        position: str = "",
        subject: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect ethnocentrism."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=ETHNOCENTRISM_PROMPT.format(
                evaluation=evaluation,
                standard=standard or "Not specified",
                position=position or "Not specified",
                subject=subject or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=ETHNOCENTRISM_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "evaluation": evaluation[:200],
            "ethnocentrism_present": data.get("ethnocentrism_present", False),
            "severity": data.get("severity", ""),
            "assumed_standard": data.get("assumed_standard", ""),
            "cultural_position": data.get("cultural_position", ""),
            "alternative_standards": data.get("alternative_standards", ""),
            "recommendation": data.get("recommendation", ""),
        }
