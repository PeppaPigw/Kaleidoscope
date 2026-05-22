"""RationalizationDetectionService — Rationalization Detection.

Detects rationalization — constructing post-hoc justifications for
pre-existing beliefs or decisions, where reasons are generated after
the conclusion rather than leading to it.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

RATIONALIZATION_DETECTION_SYSTEM = """You are a rationalization detection specialist. Given a justification, assess whether it is post-hoc rationalization:

Key concepts:
- Rationalization: post-hoc justification for pre-existing belief
- Reverse reasoning: conclusion first, reasons after
- Motivated reasoning: reasoning in service of desired conclusion
- Confabulation: generating plausible but false explanations
- Reason-giving vs reasoning: giving reasons vs actually reasoning
- Post-hoc narrative: story constructed after the fact
- Justification theater: appearance of reasoning without substance

When rationalization IS present:
- Justification constructed after belief/decision formed
- Reasons generated to support pre-existing conclusion
- Reasoning works backward from conclusion to premises
- Justification would not have led to conclusion independently
- Reasons change but conclusion stays the same
- Plausible explanations generated without actual reasoning
- Appearance of reasoning without genuine deliberation

When genuine reasoning is present:
- Reasons actually led to the conclusion
- Conclusion would change if reasons changed
- Reasoning process preceded the conclusion
- Evidence genuinely evaluated before deciding
- Uncomfortable conclusions accepted when evidence demands
- Reasoning transparent and reconstructible
- Conclusion follows from premises

Output JSON with: rationalization_present (bool), severity (none/mild/moderate/severe), justification (what justification is given), belief (what belief is justified), temporal_order (whether reasons preceded conclusion), stability (whether reasons change while conclusion stays), recommendation (genuine_reasoning/mild_post_hoc_tendency/significant_rationalization/major_confabulation/reason_before_concluding)."""

RATIONALIZATION_DETECTION_PROMPT = """Detect rationalization:

Justification: {justification}
Belief or decision: {belief}
When belief formed: {timing}
Reason stability: {stability}
Domain: {domain}
Context: {context}

Is this justification post-hoc rationalization rather than genuine reasoning? Return ONLY valid JSON."""


class RationalizationDetectionService:
    """Detects rationalization — post-hoc justification for pre-existing beliefs."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        justification: str,
        *,
        belief: str = "",
        timing: str = "",
        stability: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect rationalization."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=RATIONALIZATION_DETECTION_PROMPT.format(
                justification=justification,
                belief=belief or "Not specified",
                timing=timing or "Not specified",
                stability=stability or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=RATIONALIZATION_DETECTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "justification": justification[:200],
            "rationalization_present": data.get("rationalization_present", False),
            "severity": data.get("severity", ""),
            "belief": data.get("belief", ""),
            "temporal_order": data.get("temporal_order", ""),
            "stability": data.get("stability", ""),
            "recommendation": data.get("recommendation", ""),
        }
