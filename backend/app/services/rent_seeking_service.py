"""RentSeekingService — Rent-Seeking Detection.

Detects rent-seeking behavior — when effort goes toward capturing
existing value rather than creating new value. Tullock (1967).
Resources spent on redistribution rather than production.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

RENT_SEEKING_SYSTEM = """You are a rent-seeking specialist. Given an economic or organizational behavior, assess whether it represents rent-seeking — capturing value rather than creating it:

Key concepts (Tullock, 1967):
- Rent-seeking: spending resources to capture existing value
- Value creation vs value capture: producing vs redistributing
- Deadweight loss: resources consumed in the seeking process
- Regulatory rent: using regulation to create artificial scarcity
- Lobbying: spending to influence rules rather than compete
- Zero-sum vs positive-sum: redistribution vs growth
- Productive vs unproductive entrepreneurship

When rent-seeking IS present:
- Resources spent on lobbying rather than innovation
- Creating artificial barriers to competition
- Using regulation to protect incumbents from competition
- Litigation as a business strategy rather than rights protection
- Patent trolling: acquiring patents to extract fees, not to innovate
- Spending on influence rather than product improvement
- Capturing value through rule manipulation rather than value creation

When value capture IS legitimate:
- Protecting genuine intellectual property
- Advocating for fair rules that benefit all participants
- Competitive strategy that also creates consumer value
- Regulatory compliance that serves public interest
- Defending against unfair competition
- Market positioning through genuine differentiation
- Investment in brand that reflects real quality

Output JSON with: rent_seeking_present (bool), severity (none/mild/moderate/severe), behavior (what behavior is observed), value_created (what value is created), value_captured (what value is captured), mechanism (how value is captured), deadweight_loss (resources wasted in seeking), recommendation (behavior_productive/mild_rent_seeking/significant_value_capture/major_rent_seeking/redirect_to_value_creation)."""

RENT_SEEKING_PROMPT = """Detect rent-seeking:

Behavior: {behavior}
Value creation: {value_creation}
Value capture: {value_capture}
Mechanism: {mechanism}
Domain: {domain}
Context: {context}

Is this behavior focused on capturing existing value rather than creating new value? Return ONLY valid JSON."""


class RentSeekingService:
    """Detects rent-seeking — capturing value rather than creating it."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        behavior: str,
        *,
        value_creation: str = "",
        value_capture: str = "",
        mechanism: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect rent-seeking."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=RENT_SEEKING_PROMPT.format(
                behavior=behavior,
                value_creation=value_creation or "Not specified",
                value_capture=value_capture or "Not specified",
                mechanism=mechanism or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=RENT_SEEKING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "behavior": behavior[:200],
            "rent_seeking_present": data.get("rent_seeking_present", False),
            "severity": data.get("severity", ""),
            "value_created": data.get("value_created", ""),
            "value_captured": data.get("value_captured", ""),
            "mechanism": data.get("mechanism", ""),
            "deadweight_loss": data.get("deadweight_loss", ""),
            "recommendation": data.get("recommendation", ""),
        }
