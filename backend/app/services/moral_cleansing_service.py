"""MoralCleansingService — Moral Cleansing Detection.

Detects moral cleansing — the tendency to engage in compensatory
moral behavior after feeling morally tainted. The inverse of moral
licensing: where licensing permits bad behavior after good, cleansing
drives good behavior after bad. Zhong & Liljenquist (2006).
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

MORAL_CLEANSING_SYSTEM = """You are a moral cleansing specialist. Given a behavioral pattern, assess whether compensatory moral behavior is occurring after perceived moral failure:

Key concepts (Zhong & Liljenquist, 2006):
- Moral cleansing: compensatory good behavior after feeling tainted
- Macbeth effect: physical cleansing after moral transgression
- Moral compensation: doing good to offset perceived bad
- Guilt-driven behavior: actions motivated by guilt rather than values
- Moral accounting: treating morality as a balance sheet
- Performative virtue: visible good deeds to offset private bad ones
- Absolution seeking: behavior aimed at feeling clean rather than being good

When moral cleansing IS present:
- Good behavior immediately follows perceived moral failure
- The compensatory behavior is disproportionate or performative
- The person is seeking absolution rather than genuine change
- Moral accounting: "I did X bad, so I'll do Y good to balance"
- The underlying behavior doesn't change, only the compensation
- Visible virtue signals after private transgressions
- Charity or kindness used as moral offset rather than genuine care

When compensatory behavior IS appropriate:
- The person genuinely changes the underlying behavior
- Compensation is directed at those actually harmed
- The response is proportional and sincere
- It reflects genuine moral growth, not just guilt management
- The person acknowledges the harm rather than just offsetting it
- Restitution is part of a broader pattern of change
- The motivation is repair rather than self-image management

Output JSON with: moral_cleansing_present (bool), severity (none/mild/moderate/severe), transgression (what moral failure is perceived), compensation (what compensatory behavior occurs), proportionality (is compensation proportional), genuine_change (does underlying behavior change), motivation (guilt management vs genuine repair), recommendation (genuine_repair/mild_compensation/significant_moral_cleansing/major_absolution_seeking/address_underlying_behavior)."""

MORAL_CLEANSING_PROMPT = """Detect moral cleansing:

Pattern: {pattern}
Transgression: {transgression}
Compensation: {compensation}
Change: {change}
Domain: {domain}
Context: {context}

Is compensatory moral behavior occurring after perceived moral failure without genuine change? Return ONLY valid JSON."""


class MoralCleansingService:
    """Detects moral cleansing — compensatory virtue after perceived transgression."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        pattern: str,
        *,
        transgression: str = "",
        compensation: str = "",
        change: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect moral cleansing."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=MORAL_CLEANSING_PROMPT.format(
                pattern=pattern,
                transgression=transgression or "Not specified",
                compensation=compensation or "Not specified",
                change=change or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=MORAL_CLEANSING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "pattern": pattern[:200],
            "moral_cleansing_present": data.get("moral_cleansing_present", False),
            "severity": data.get("severity", ""),
            "transgression": data.get("transgression", ""),
            "compensation": data.get("compensation", ""),
            "genuine_change": data.get("genuine_change", ""),
            "motivation": data.get("motivation", ""),
            "recommendation": data.get("recommendation", ""),
        }
