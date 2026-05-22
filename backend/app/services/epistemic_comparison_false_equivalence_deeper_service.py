"""EpistemicComparisonFalseEquivalenceDeeperService — Epistemic False Equivalence Detection (Deeper).

Detects epistemic false equivalence — treating fundamentally different
things as equivalent, obscuring important differences.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_COMPARISON_FALSE_EQUIVALENCE_DEEPER_SYSTEM = """You are an epistemic false equivalence specialist. Given false equivalences, assess false equivalence:

Key concepts:
- Epistemic false equivalence: treating fundamentally different things as equivalent
- Scale blindness: ignoring differences in scale or magnitude
- Quality-quantity conflation: treating different qualities as same quantity
- Context stripping: stripping context that makes things different
- Both-sides-ism: false balance treating unequal things as equal
- Degree blindness: ignoring differences of degree
- Category conflation: conflating different categories as equivalent

When epistemic false equivalence IS present:
- Fundamentally different treated as equivalent
- Scale differences ignored
- Quality-quantity conflated
- Context stripped
- False balance imposed
- Degree differences ignored
- Categories conflated

When no false equivalence:
- Differences acknowledged
- Scale considered
- Quality and quantity distinguished
- Context preserved
- Balance proportional
- Degrees recognized
- Categories distinguished

Output JSON with: false_equivalence_deeper_detected (bool), severity (none/mild/moderate/severe), scale_blindness (what scale differences ignored), both_sides_ism (what false balance), degree_blindness (what degree differences ignored), category_conflation (what categories conflated), recommendation (no_false_equivalence/mild_difference_awareness/significant_proportionality_restoration/major_intensive_equivalence_testing/emergency_complete_false_equivalence)."""

EPISTEMIC_COMPARISON_FALSE_EQUIVALENCE_DEEPER_PROMPT = """Detect epistemic false equivalence:

Scale blindness: {scale_blindness}
Both-sides-ism: {both_sides_ism}
Degree blindness: {degree_blindness}
Category conflation: {category_conflation}
Domain: {domain}
Context: {context}

Are fundamentally different things being treated as equivalent? Return ONLY valid JSON."""


class EpistemicComparisonFalseEquivalenceDeeperService:
    """Detects epistemic false equivalence — different as same."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        scale_blindness: str,
        *,
        both_sides_ism: str = "",
        degree_blindness: str = "",
        category_conflation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic false equivalence."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_COMPARISON_FALSE_EQUIVALENCE_DEEPER_PROMPT.format(
                scale_blindness=scale_blindness,
                both_sides_ism=both_sides_ism or "Not specified",
                degree_blindness=degree_blindness or "Not specified",
                category_conflation=category_conflation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_COMPARISON_FALSE_EQUIVALENCE_DEEPER_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "scale_blindness": scale_blindness[:200],
            "false_equivalence_deeper_detected": data.get("false_equivalence_deeper_detected", False),
            "severity": data.get("severity", ""),
            "both_sides_ism": data.get("both_sides_ism", ""),
            "degree_blindness": data.get("degree_blindness", ""),
            "category_conflation": data.get("category_conflation", ""),
            "recommendation": data.get("recommendation", ""),
        }
