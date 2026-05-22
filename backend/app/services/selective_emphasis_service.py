"""SelectiveEmphasisService — Selective Emphasis Detection.

Detects selective emphasis — when emphasis patterns in
communication distort the overall picture by highlighting
certain facts while downplaying others of equal or greater
importance.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

SELECTIVE_EMPHASIS_SYSTEM = """You are a selective emphasis specialist. Given a communication, assess whether emphasis patterns distort the overall picture:

Key concepts:
- Selective emphasis: highlighting some facts while downplaying others
- Prominence bias: what gets attention shapes perception
- Burial: hiding important information in less prominent positions
- Headline vs body: emphasis in headlines vs details in body
- Frequency emphasis: repeating certain points while mentioning others once
- Visual emphasis: using formatting, size, or position to highlight
- Omission by de-emphasis: technically including but effectively hiding

When selective emphasis IS present:
- Important facts buried or de-emphasized
- Less important but favorable facts prominently featured
- Emphasis pattern creates misleading overall impression
- Repetition of certain points while others mentioned once
- Headlines/summaries don't reflect the full picture
- Formatting or positioning used to hide unfavorable info
- Reader would get different impression from emphasis vs full content

When selective emphasis is NOT present:
- Emphasis proportional to importance
- Key facts prominently featured regardless of favorability
- Overall impression matches the full picture
- Important caveats given appropriate prominence
- Headlines/summaries accurately reflect content
- Formatting serves clarity, not persuasion
- Reader gets accurate impression from any level of engagement

Output JSON with: selective_emphasis (bool), severity (none/mild/moderate/severe), emphasized (what is highlighted), de_emphasized (what is buried or downplayed), distortion (how the overall picture is skewed), balanced_version (what proportional emphasis would look like), recommendation (balanced_emphasis/mild_skew/significant_selective_emphasis/major_distortion/rebalance_prominence)."""

SELECTIVE_EMPHASIS_PROMPT = """Detect selective emphasis:

Communication: {communication}
Key facts: {facts}
Emphasis pattern: {emphasis}
Overall impression: {impression}
Domain: {domain}
Context: {context}

Are emphasis patterns distorting the overall picture? Return ONLY valid JSON."""


class SelectiveEmphasisService:
    """Detects selective emphasis — emphasis patterns distorting the picture."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        communication: str,
        *,
        facts: str = "",
        emphasis: str = "",
        impression: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect selective emphasis."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=SELECTIVE_EMPHASIS_PROMPT.format(
                communication=communication,
                facts=facts or "Not specified",
                emphasis=emphasis or "Not specified",
                impression=impression or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=SELECTIVE_EMPHASIS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "communication": communication[:200],
            "selective_emphasis": data.get("selective_emphasis", False),
            "severity": data.get("severity", ""),
            "emphasized": data.get("emphasized", ""),
            "de_emphasized": data.get("de_emphasized", ""),
            "distortion": data.get("distortion", ""),
            "recommendation": data.get("recommendation", ""),
        }
