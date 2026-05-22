"""StrategicFramingService — Strategic Framing Detection.

Detects strategic framing — when information is presented in a
way designed to manipulate perception rather than inform. This
includes choosing reference points, comparison sets, and
presentation formats to lead to predetermined conclusions.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

STRATEGIC_FRAMING_SYSTEM = """You are a strategic framing specialist. Given a presentation of information, assess whether framing is manipulative:

Key concepts:
- Strategic framing: presenting info to lead to predetermined conclusions
- Reference point manipulation: choosing baselines that favor one interpretation
- Comparison set selection: cherry-picking what to compare against
- Gain/loss framing: same info presented as gain or loss
- Anchoring through framing: setting expectations through presentation
- Selective context: providing context that favors one interpretation
- Format effects: choosing charts, percentages, or absolutes strategically

When strategic framing IS present:
- Reference points chosen to make something look better/worse
- Comparison set selected to favor a conclusion
- Same data could be framed very differently with different impression
- Context provided selectively to support one interpretation
- Format chosen to emphasize or hide certain aspects
- Framing designed to lead rather than inform
- Alternative framings would give very different impressions

When strategic framing is NOT present:
- Information presented with neutral framing
- Multiple reference points provided
- Comparison sets are natural and comprehensive
- Context is balanced and complete
- Format chosen for clarity, not persuasion
- Alternative framings acknowledged
- Presentation designed to inform, not lead

Output JSON with: strategic_framing (bool), severity (none/mild/moderate/severe), frame_used (how info is presented), alternative_frame (how else it could be presented), manipulation_technique (what framing technique is used), impression_shift (how framing changes perception), recommendation (neutral_framing/mild_slant/significant_manipulation/major_strategic_framing/present_multiple_frames)."""

STRATEGIC_FRAMING_PROMPT = """Detect strategic framing:

Presentation: {presentation}
Information: {information}
Reference point: {reference}
Comparison: {comparison}
Domain: {domain}
Context: {context}

Is this information framed to manipulate rather than inform? Return ONLY valid JSON."""


class StrategicFramingService:
    """Detects strategic framing — manipulative information presentation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        presentation: str,
        *,
        information: str = "",
        reference: str = "",
        comparison: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect strategic framing."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=STRATEGIC_FRAMING_PROMPT.format(
                presentation=presentation,
                information=information or "Not specified",
                reference=reference or "Not specified",
                comparison=comparison or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=STRATEGIC_FRAMING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "presentation": presentation[:200],
            "strategic_framing": data.get("strategic_framing", False),
            "severity": data.get("severity", ""),
            "frame_used": data.get("frame_used", ""),
            "alternative_frame": data.get("alternative_frame", ""),
            "manipulation_technique": data.get("manipulation_technique", ""),
            "recommendation": data.get("recommendation", ""),
        }
