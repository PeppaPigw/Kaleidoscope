"""TabooTradeoffService — Sacred Value & Taboo Trade-off Detection.

Identifies when a decision involves trading sacred/protected values
against secular ones. These trade-offs create moral outrage regardless
of utilitarian calculus and require different framing to navigate.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

TABOO_SYSTEM = """You are a taboo trade-off specialist. Given a decision or proposal, assess whether it involves trading sacred values against secular ones:
- Does it put a price on something people consider priceless?
- Does it trade human life/dignity/rights against money/efficiency?
- Would even discussing this trade-off cause moral outrage?
- Is the framing making a taboo trade-off seem like a routine cost-benefit analysis?
- What sacred values are being violated?

Output JSON with: taboo_tradeoff_present (bool), severity (none/mild/moderate/severe/explosive), sacred_value (what protected value is being traded), secular_value (what it's being traded against), outrage_potential (0-1), who_would_be_outraged (groups that would find this offensive), why_its_taboo (what norm or value is being violated), utilitarian_case (the rational argument for the trade-off), deontological_objection (why it's wrong regardless of consequences), framing_matters (bool — could different framing make this acceptable?), acceptable_framing (how to discuss this without triggering outrage), historical_examples (similar taboo trade-offs and how they were handled), cultural_variation (does this vary across cultures?), recommendation (avoid/reframe/acknowledge_sacred_value/proceed_with_care)."""

TABOO_PROMPT = """Detect taboo trade-offs:

Decision/Proposal: {proposal}
Stakeholders: {stakeholders}
Domain: {domain}
Context: {context}

Does this involve trading sacred values? Return ONLY valid JSON."""


class TabooTradeoffService:
    """Detects taboo trade-offs involving sacred values."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        proposal: str,
        *,
        stakeholders: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect taboo trade-offs."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=TABOO_PROMPT.format(
                proposal=proposal,
                stakeholders=stakeholders or "General public",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=TABOO_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "proposal": proposal[:200],
            "taboo_tradeoff_present": data.get("taboo_tradeoff_present", False),
            "severity": data.get("severity", ""),
            "sacred_value": data.get("sacred_value", ""),
            "secular_value": data.get("secular_value", ""),
            "outrage_potential": data.get("outrage_potential", 0),
            "who_would_be_outraged": data.get("who_would_be_outraged", ""),
            "why_its_taboo": data.get("why_its_taboo", ""),
            "utilitarian_case": data.get("utilitarian_case", ""),
            "deontological_objection": data.get("deontological_objection", ""),
            "framing_matters": data.get("framing_matters", False),
            "acceptable_framing": data.get("acceptable_framing", ""),
            "historical_examples": data.get("historical_examples", []),
            "cultural_variation": data.get("cultural_variation", ""),
            "recommendation": data.get("recommendation", ""),
        }
