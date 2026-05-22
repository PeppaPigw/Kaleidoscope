"""EpistemicIntellectualInheritanceService — Epistemic Intellectual Inheritance Detection.

Detects epistemic intellectual inheritance — uncritically inheriting
intellectual positions from mentors or authority figures.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_INTELLECTUAL_INHERITANCE_SYSTEM = """You are an epistemic intellectual inheritance specialist. Given uncritically inheriting positions, assess intellectual inheritance:

Key concepts:
- Epistemic intellectual inheritance: uncritically inheriting positions from mentors
- Unexamined adoption: adopting views without examining them
- Mentor worship: treating mentor's views as sacred
- Intellectual lineage pressure: pressure to maintain intellectual lineage
- Tradition over truth: valuing tradition over independent truth-seeking
- Loyalty over accuracy: being loyal to inherited views over being accurate
- Intellectual ancestor worship: worshipping intellectual ancestors uncritically

When epistemic intellectual inheritance IS present:
- Uncritically inheriting positions
- Adopting views without examining
- Treating mentor views as sacred
- Pressure to maintain lineage
- Valuing tradition over truth
- Loyal to inherited views over accuracy
- Worshipping intellectual ancestors

When no intellectual inheritance:
- Critically examining inherited views
- Adopting only after examination
- Treating mentor views as input
- Free from lineage pressure
- Valuing truth over tradition
- Accuracy over loyalty
- Respecting but questioning ancestors

Output JSON with: intellectual_inheritance_detected (bool), severity (none/mild/moderate/severe), unexamined_adoption (what adopted without examining), mentor_worship (whose views treated as sacred), lineage_pressure (what pressure to maintain), tradition_over_truth (what tradition valued over truth), recommendation (no_intellectual_inheritance/mild_examination_practice/significant_critical_review/major_intensive_independence_building/emergency_complete_uncritical_inheritance)."""

EPISTEMIC_INTELLECTUAL_INHERITANCE_PROMPT = """Detect epistemic intellectual inheritance:

Unexamined adoption: {unexamined_adoption}
Mentor worship: {mentor_worship}
Lineage pressure: {lineage_pressure}
Tradition over truth: {tradition_over_truth}
Domain: {domain}
Context: {context}

Is there uncritically inheriting intellectual positions from mentors? Return ONLY valid JSON."""


class EpistemicIntellectualInheritanceService:
    """Detects epistemic intellectual inheritance — uncritically inheriting positions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        unexamined_adoption: str,
        *,
        mentor_worship: str = "",
        lineage_pressure: str = "",
        tradition_over_truth: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic intellectual inheritance."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_INTELLECTUAL_INHERITANCE_PROMPT.format(
                unexamined_adoption=unexamined_adoption,
                mentor_worship=mentor_worship or "Not specified",
                lineage_pressure=lineage_pressure or "Not specified",
                tradition_over_truth=tradition_over_truth or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_INTELLECTUAL_INHERITANCE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "unexamined_adoption": unexamined_adoption[:200],
            "intellectual_inheritance_detected": data.get("intellectual_inheritance_detected", False),
            "severity": data.get("severity", ""),
            "mentor_worship": data.get("mentor_worship", ""),
            "lineage_pressure": data.get("lineage_pressure", ""),
            "tradition_over_truth": data.get("tradition_over_truth", ""),
            "recommendation": data.get("recommendation", ""),
        }
