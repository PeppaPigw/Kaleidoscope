"""AsymmetricInfoService — Asymmetric Information Detection.

Identifies when one party in a transaction, negotiation, or decision
has significantly more information than the other. This creates
adverse selection, exploitation risk, and market failures (Akerlof's
"Market for Lemons" problem).
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

ASYMMETRIC_SYSTEM = """You are an information asymmetry specialist. Given a situation, assess whether significant information asymmetry exists:
- Does one party know materially more than the other?
- Is the informed party exploiting their information advantage?
- Could the uninformed party reasonably discover this information?
- Does the asymmetry create adverse selection (bad outcomes driving out good)?
- Are there signaling or screening mechanisms that could reduce the asymmetry?

Output JSON with: asymmetry_present (bool), severity (none/mild/moderate/severe/critical), informed_party (who has more information), uninformed_party (who lacks information), information_gap (what the uninformed party doesn't know), exploitation_risk (0-1 — likelihood the gap is being exploited), adverse_selection_risk (0-1 — risk of bad outcomes driving out good), moral_hazard_created (bool — does the asymmetry enable hidden action?), discoverable (bool — could the uninformed party reasonably learn this?), discovery_cost (low/moderate/high/prohibitive — cost to close the gap), signaling_available (mechanisms the informed party could use to credibly share info), screening_available (mechanisms the uninformed party could use to extract info), market_failure_risk (0-1 — risk of market/system breakdown from the asymmetry), historical_parallel (similar asymmetry situations and outcomes), recommendation (acceptable/disclose/mandate_transparency/regulate/avoid_transaction)."""

ASYMMETRIC_PROMPT = """Detect information asymmetry:

Situation: {situation}
Parties involved: {parties}
Transaction/Decision: {transaction}
Domain: {domain}
Context: {context}

Is there significant information asymmetry? Return ONLY valid JSON."""


class AsymmetricInfoService:
    """Detects asymmetric information and adverse selection risk."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        parties: str = "",
        transaction: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect information asymmetry."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=ASYMMETRIC_PROMPT.format(
                situation=situation,
                parties=parties or "Not specified",
                transaction=transaction or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=ASYMMETRIC_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "asymmetry_present": data.get("asymmetry_present", False),
            "severity": data.get("severity", ""),
            "informed_party": data.get("informed_party", ""),
            "uninformed_party": data.get("uninformed_party", ""),
            "information_gap": data.get("information_gap", ""),
            "exploitation_risk": data.get("exploitation_risk", 0),
            "adverse_selection_risk": data.get("adverse_selection_risk", 0),
            "moral_hazard_created": data.get("moral_hazard_created", False),
            "discoverable": data.get("discoverable", False),
            "discovery_cost": data.get("discovery_cost", ""),
            "signaling_available": data.get("signaling_available", ""),
            "screening_available": data.get("screening_available", ""),
            "market_failure_risk": data.get("market_failure_risk", 0),
            "historical_parallel": data.get("historical_parallel", ""),
            "recommendation": data.get("recommendation", ""),
        }
