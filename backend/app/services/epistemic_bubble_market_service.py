"""EpistemicBubbleMarketService — Epistemic Bubble Market Detection.

Detects epistemic bubble markets — belief valuations disconnected
from underlying evidence, prone to sudden collapse.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_BUBBLE_MARKET_SYSTEM = """You are an epistemic bubble market specialist. Given a belief valuation pattern, assess whether valuations are disconnected from evidence:

Key concepts:
- Epistemic bubble market: belief valuations disconnected from evidence
- Overvaluation: beliefs valued far beyond evidential support
- Speculation: belief adoption based on speculation not evidence
- Herd behavior: following others rather than evaluating evidence
- Disconnect from fundamentals: disconnected from evidential base
- Collapse risk: risk of sudden valuation collapse
- Irrational exuberance: excessive enthusiasm without evidence

When epistemic bubble market IS present:
- Belief valuations disconnected from underlying evidence
- Beliefs valued far beyond what evidence supports
- Belief adoption based on speculation not evidence
- Following others rather than evaluating evidence independently
- Disconnected from evidential fundamentals
- Risk of sudden collapse when reality intrudes
- Excessive enthusiasm without evidential support

When evidence-based valuation is present:
- Belief valuations proportionate to evidence
- Beliefs valued based on evidential support
- Belief adoption based on evidence evaluation
- Independent evaluation rather than herd following
- Connected to evidential fundamentals
- Stable valuations based on evidence
- Enthusiasm proportionate to evidence

Output JSON with: bubble_present (bool), severity (none/mild/moderate/severe), belief (what belief is in a bubble), overvaluation (how overvalued), disconnect (disconnect from evidence), collapse_risk (risk of collapse), recommendation (evidence_based_valuation/mild_overvaluation/significant_bubble/major_disconnect/correct_to_evidence)."""

EPISTEMIC_BUBBLE_MARKET_PROMPT = """Detect epistemic bubble market:

Belief: {belief}
Overvaluation: {overvaluation}
Disconnect: {disconnect}
Collapse risk: {collapse_risk}
Domain: {domain}
Context: {context}

Are belief valuations disconnected from underlying evidence? Return ONLY valid JSON."""


class EpistemicBubbleMarketService:
    """Detects epistemic bubble markets — belief valuations disconnected from evidence."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        belief: str,
        *,
        overvaluation: str = "",
        disconnect: str = "",
        collapse_risk: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic bubble market."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_BUBBLE_MARKET_PROMPT.format(
                belief=belief,
                overvaluation=overvaluation or "Not specified",
                disconnect=disconnect or "Not specified",
                collapse_risk=collapse_risk or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_BUBBLE_MARKET_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "belief": belief[:200],
            "bubble_present": data.get("bubble_present", False),
            "severity": data.get("severity", ""),
            "overvaluation": data.get("overvaluation", ""),
            "disconnect": data.get("disconnect", ""),
            "collapse_risk": data.get("collapse_risk", ""),
            "recommendation": data.get("recommendation", ""),
        }
