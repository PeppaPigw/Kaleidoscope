"""EpistemicDigitalFilterBubbleService — Epistemic Digital Filter Bubble Detection.

Detects epistemic digital filter bubble — algorithmic filtering creating
epistemic isolation by showing only confirming information.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_DIGITAL_FILTER_BUBBLE_SYSTEM = """You are an epistemic digital filter bubble specialist. Given filter bubble effects, assess epistemic isolation:

Key concepts:
- Epistemic digital filter bubble: algorithmic filtering creating isolation
- Personalization trap: personalized feeds reinforcing existing beliefs
- Algorithmic confirmation bias: algorithms showing confirming content
- Exposure narrowing: decreasing exposure to diverse viewpoints
- Echo chamber amplification: echo chambers amplified by algorithms
- Serendipity elimination: eliminating chance encounters with different views
- Invisible filtering: users unaware of what is filtered out

When epistemic digital filter bubble IS present:
- Algorithmic filtering creating isolation
- Personalization reinforcing beliefs
- Confirmation bias amplified
- Exposure narrowing
- Echo chambers amplified
- Serendipity eliminated
- Filtering invisible

When no filter bubble:
- Diverse content exposed
- Personalization balanced
- Challenging views included
- Exposure broad
- Echo chambers broken
- Serendipity preserved
- Filtering transparent

Output JSON with: filter_bubble_detected (bool), severity (none/mild/moderate/severe), personalization_trap (what personalization trapping), algorithmic_confirmation (what algorithmic confirmation), exposure_narrowing (what exposure narrowing), invisible_filtering (what invisible filtering), recommendation (no_filter_bubble/mild_diversity_seeking/significant_algorithm_awareness/major_intensive_bubble_breaking/emergency_complete_filter_bubble)."""

EPISTEMIC_DIGITAL_FILTER_BUBBLE_PROMPT = """Detect epistemic digital filter bubble:

Personalization trap: {personalization_trap}
Algorithmic confirmation: {algorithmic_confirmation}
Exposure narrowing: {exposure_narrowing}
Invisible filtering: {invisible_filtering}
Domain: {domain}
Context: {context}

Is algorithmic filtering creating epistemic isolation? Return ONLY valid JSON."""


class EpistemicDigitalFilterBubbleService:
    """Detects epistemic digital filter bubble — algorithmic isolation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        personalization_trap: str,
        *,
        algorithmic_confirmation: str = "",
        exposure_narrowing: str = "",
        invisible_filtering: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic digital filter bubble."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_DIGITAL_FILTER_BUBBLE_PROMPT.format(
                personalization_trap=personalization_trap,
                algorithmic_confirmation=algorithmic_confirmation or "Not specified",
                exposure_narrowing=exposure_narrowing or "Not specified",
                invisible_filtering=invisible_filtering or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_DIGITAL_FILTER_BUBBLE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "personalization_trap": personalization_trap[:200],
            "filter_bubble_detected": data.get("filter_bubble_detected", False),
            "severity": data.get("severity", ""),
            "algorithmic_confirmation": data.get("algorithmic_confirmation", ""),
            "exposure_narrowing": data.get("exposure_narrowing", ""),
            "invisible_filtering": data.get("invisible_filtering", ""),
            "recommendation": data.get("recommendation", ""),
        }
