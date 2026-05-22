"""SubadditivityService — Subadditivity Effect Detection.

Detects subadditivity — when the sum of probability judgments
for sub-events exceeds the probability of the inclusive event.
Tversky & Koehler (1994). Unpacking a category into specific
instances inflates total judged probability. "Death from
heart disease, cancer, or other causes" sums to more than
"death from any cause."
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

SUBADDITIVITY_SYSTEM = """You are a subadditivity specialist. Given probability judgments for events and sub-events, assess whether unpacking is inflating total probability:

Key concepts (Tversky & Koehler, 1994):
- Subadditivity: sum of parts > whole in probability judgment
- Support theory: evidence for hypothesis depends on its description
- Unpacking effect: explicit sub-events get more total probability
- Implicit disjunction: packed categories get less weight
- Description dependence: same event, different probability based on description
- Binary complementarity violation: P(A) + P(not-A) > 1
- Partition inequality: finer partitions sum to more than 1

When subadditivity IS present:
- Sub-event probabilities sum to more than the parent event
- More detailed breakdowns yield higher total probability
- "What's the chance of X, Y, or Z?" > "What's the chance of any problem?"
- Risk assessments that inflate when risks are listed individually
- Budget estimates that grow when broken into line items
- Time estimates that expand when tasks are listed separately

When the judgment IS appropriate:
- The sub-events are genuinely not exhaustive
- The person is aware of and correcting for subadditivity
- The detailed estimates are more accurate than the packed estimate
- The sum constraint is being explicitly maintained
- The unpacking reveals genuinely overlooked components

Output JSON with: subadditivity_present (bool), severity (none/mild/moderate/severe), judgment (what probability judgment is being made), packed_estimate (probability of the inclusive event), unpacked_estimates (probabilities of sub-events), sum_of_parts (what do sub-events sum to), excess (how much does the sum exceed the whole), unpacking_level (how finely are events broken down), recommendation (judgment_appropriate/mild_subadditivity/significant_inflation/major_subadditivity/normalize_to_sum_constraint)."""

SUBADDITIVITY_PROMPT = """Detect subadditivity:

Judgment: {judgment}
Whole estimate: {whole}
Parts: {parts}
Sum: {total}
Domain: {domain}
Context: {context}

Are sub-event probabilities summing to more than the inclusive event? Return ONLY valid JSON."""


class SubadditivityService:
    """Detects subadditivity — unpacking inflating total probability judgments."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        judgment: str,
        *,
        whole: str = "",
        parts: str = "",
        total: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect subadditivity."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=SUBADDITIVITY_PROMPT.format(
                judgment=judgment,
                whole=whole or "Not specified",
                parts=parts or "Not specified",
                total=total or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=SUBADDITIVITY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "judgment": judgment[:200],
            "subadditivity_present": data.get("subadditivity_present", False),
            "severity": data.get("severity", ""),
            "packed_estimate": data.get("packed_estimate", ""),
            "unpacked_estimates": data.get("unpacked_estimates", ""),
            "sum_of_parts": data.get("sum_of_parts", ""),
            "excess": data.get("excess", ""),
            "unpacking_level": data.get("unpacking_level", ""),
            "recommendation": data.get("recommendation", ""),
        }
