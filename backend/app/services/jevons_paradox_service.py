"""JevonsParadoxService — Jevons Paradox Detection.

Detects Jevons paradox — when efficiency improvements in resource
use lead to increased total consumption rather than decreased
consumption. William Stanley Jevons (1865). Making something more
efficient makes it cheaper, which increases demand, which can
overwhelm the efficiency gains.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

JEVONS_PARADOX_SYSTEM = """You are a Jevons paradox specialist. Given an efficiency improvement, assess whether it might lead to increased rather than decreased total resource consumption:

Key concepts (Jevons, 1865):
- Jevons paradox: efficiency increases total consumption
- Rebound effect: efficiency gains partially offset by increased use
- Direct rebound: cheaper per-unit cost increases quantity demanded
- Indirect rebound: savings spent on other resource-consuming activities
- Backfire: rebound exceeds 100% (total consumption increases)
- Khazzoom-Brookes postulate: energy efficiency increases energy consumption
- Induced demand: building more roads creates more traffic

When Jevons paradox IS likely:
- Efficiency makes a resource cheaper, increasing demand
- "We'll save resources by being more efficient" without demand management
- Historical pattern shows efficiency gains consumed by growth
- The resource has elastic demand (people want more if it's cheaper)
- No caps or limits on total consumption
- Efficiency enables new use cases that didn't exist before
- Cost savings are reinvested in more of the same activity

When efficiency DOES reduce consumption:
- Demand is inelastic (people don't want more even if cheaper)
- Caps or quotas limit total consumption regardless of efficiency
- The efficiency gain is in a declining or saturated market
- Savings are directed to non-resource-consuming alternatives
- The rebound effect is acknowledged and managed
- Absolute targets are set, not just intensity targets
- Behavioral changes accompany the efficiency improvement

Output JSON with: jevons_paradox_likely (bool), severity (none/mild/moderate/severe), efficiency_improvement (what is being made more efficient), demand_elasticity (will cheaper cost increase demand), rebound_estimate (how much efficiency gain will be consumed by increased use), historical_pattern (has this happened before in this domain), recommendation (efficiency_sufficient/mild_rebound_risk/significant_jevons_risk/major_backfire_likely/combine_efficiency_with_caps)."""

JEVONS_PARADOX_PROMPT = """Detect Jevons paradox:

Efficiency improvement: {improvement}
Resource: {resource}
Demand pattern: {demand}
Historical: {historical}
Domain: {domain}
Context: {context}

Might this efficiency improvement lead to increased rather than decreased total resource consumption? Return ONLY valid JSON."""


class JevonsParadoxService:
    """Detects Jevons paradox — efficiency increasing total consumption."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        improvement: str,
        *,
        resource: str = "",
        demand: str = "",
        historical: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect Jevons paradox."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=JEVONS_PARADOX_PROMPT.format(
                improvement=improvement,
                resource=resource or "Not specified",
                demand=demand or "Not specified",
                historical=historical or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=JEVONS_PARADOX_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "improvement": improvement[:200],
            "jevons_paradox_likely": data.get("jevons_paradox_likely", False),
            "severity": data.get("severity", ""),
            "demand_elasticity": data.get("demand_elasticity", ""),
            "rebound_estimate": data.get("rebound_estimate", ""),
            "historical_pattern": data.get("historical_pattern", ""),
            "recommendation": data.get("recommendation", ""),
        }
