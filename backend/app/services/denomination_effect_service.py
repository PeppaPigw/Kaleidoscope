"""DenominationEffectService — Denomination Effect Detection.

Detects the denomination effect — tendency to spend more money
when it's in smaller denominations than larger ones. Raghubir
& Srivastava (2009). A $100 bill feels harder to break than
spending five $20 bills. Digital payments feel less "real" than
cash. The form of money affects spending behavior independent
of the amount.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

DENOMINATION_SYSTEM = """You are a denomination effect specialist. Given a spending or resource allocation decision, assess whether the form/denomination of the resource is influencing behavior independent of the amount:

Key concepts (Raghubir & Srivastava, 2009):
- Denomination effect: spending more when money is in smaller units
- Pain of paying: larger denominations create more psychological friction
- Mental accounting: different forms of money feel different
- Digital payment effect: electronic spending feels less real than cash
- Windfall spending: "found money" or bonuses spent more freely
- Fungibility violation: treating equivalent amounts differently based on form

When the denomination effect IS present:
- Spending more freely with small bills than large ones
- Digital/card spending exceeding what would be spent in cash
- Breaking a large bill triggers spending the change
- Gift cards spent more freely than equivalent cash
- Points/miles valued differently than their cash equivalent
- "It's just $5" repeated many times exceeding what a single $50 would

When form-based behavior IS rational:
- Transaction costs genuinely differ by payment method
- Liquidity constraints make form relevant
- The person is deliberately using form as a commitment device
- Different accounts serve genuine budgeting purposes
- The denomination difference reflects real convenience value

Output JSON with: denomination_effect_present (bool), severity (none/mild/moderate/severe), resource_form (what form is the resource in), spending_behavior (how is spending being affected), equivalent_amount (what's the actual value regardless of form), pain_of_paying (how much friction does this form create?), digital_vs_physical (is digital spending feeling less real?), mental_accounting (bool — are equivalent amounts being treated differently?), fungibility_violation (bool — is money being treated as non-fungible?), commitment_device (bool — is the form being used deliberately for control?), total_impact (how much more is being spent due to form?), recommendation (behavior_rational/mild_denomination_effect/significant_overspending/major_denomination_effect/treat_all_forms_equally)."""

DENOMINATION_PROMPT = """Detect denomination effect:

Spending situation: {situation}
Resource form: {form}
Behavior observed: {behavior}
Equivalent in other form: {equivalent}
Domain: {domain}
Context: {context}

Is the form/denomination of the resource influencing behavior beyond the amount? Return ONLY valid JSON."""


class DenominationEffectService:
    """Detects denomination effect — form of resource influencing spending behavior."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        form: str = "",
        behavior: str = "",
        equivalent: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect denomination effect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=DENOMINATION_PROMPT.format(
                situation=situation,
                form=form or "Not specified",
                behavior=behavior or "Not specified",
                equivalent=equivalent or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=DENOMINATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "denomination_effect_present": data.get("denomination_effect_present", False),
            "severity": data.get("severity", ""),
            "resource_form": data.get("resource_form", ""),
            "spending_behavior": data.get("spending_behavior", ""),
            "equivalent_amount": data.get("equivalent_amount", ""),
            "pain_of_paying": data.get("pain_of_paying", ""),
            "digital_vs_physical": data.get("digital_vs_physical", ""),
            "mental_accounting": data.get("mental_accounting", False),
            "fungibility_violation": data.get("fungibility_violation", False),
            "commitment_device": data.get("commitment_device", False),
            "total_impact": data.get("total_impact", ""),
            "recommendation": data.get("recommendation", ""),
        }
