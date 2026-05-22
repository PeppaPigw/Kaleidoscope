"""EpistemicIndigestionService — Epistemic Indigestion Detection.

Detects epistemic indigestion — taking in more information than
can be properly processed, leading to confusion rather than understanding.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_INDIGESTION_SYSTEM = """You are an epistemic indigestion specialist. Given an information consumption pattern, assess whether more is being taken in than can be processed:

Key concepts:
- Epistemic indigestion: more information than can be processed
- Information overload: overloaded beyond processing capacity
- Consumption without processing: taking in without understanding
- Cognitive overwhelm: overwhelmed by information volume
- Understanding deficit: gap between consumption and comprehension
- Processing bottleneck: bottleneck in information processing
- Quantity over quality: prioritizing quantity over understanding

When epistemic indigestion IS present:
- More information consumed than can be processed
- Understanding not keeping pace with consumption
- Cognitive capacity overwhelmed
- Gap between intake and comprehension growing
- Processing bottleneck causing confusion
- Quantity prioritized over understanding
- Information consumed but not digested

When healthy information diet is present:
- Information consumed at processable rate
- Understanding keeping pace with intake
- Cognitive capacity respected
- Intake matched to comprehension ability
- Processing adequate for consumption
- Quality prioritized over quantity
- Information properly digested

Output JSON with: indigestion_present (bool), severity (none/mild/moderate/severe), consumption (what is being consumed), processing_capacity (what capacity exists), gap (what gap exists between intake and processing), consequence (what confusion results), recommendation (healthy_diet/mild_overload/significant_epistemic_indigestion/major_processing_failure/reduce_intake_increase_processing)."""

EPISTEMIC_INDIGESTION_PROMPT = """Detect epistemic indigestion:

Consumption: {consumption}
Processing capacity: {capacity}
Understanding gap: {gap}
Consequence: {consequence}
Domain: {domain}
Context: {context}

Is more information being consumed than can be properly processed? Return ONLY valid JSON."""


class EpistemicIndigestionService:
    """Detects epistemic indigestion — more information than can be processed."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        consumption: str,
        *,
        capacity: str = "",
        gap: str = "",
        consequence: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic indigestion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_INDIGESTION_PROMPT.format(
                consumption=consumption,
                capacity=capacity or "Not specified",
                gap=gap or "Not specified",
                consequence=consequence or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_INDIGESTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "consumption": consumption[:200],
            "indigestion_present": data.get("indigestion_present", False),
            "severity": data.get("severity", ""),
            "processing_capacity": data.get("processing_capacity", ""),
            "gap": data.get("gap", ""),
            "consequence": data.get("consequence", ""),
            "recommendation": data.get("recommendation", ""),
        }
