"""EpistemicCarnotCycleService — Epistemic Carnot Cycle Detection.

Detects epistemic Carnot cycle — intellectual processes operating between
hot and cold reservoirs with maximum theoretical efficiency.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_CARNOT_CYCLE_SYSTEM = """You are an epistemic Carnot cycle specialist. Given an intellectual process, assess whether it operates between reservoirs at maximum efficiency:

Key concepts:
- Epistemic Carnot cycle: maximum efficiency between reservoirs
- Hot reservoir: source of intellectual energy
- Cold reservoir: sink for intellectual waste
- Efficiency limit: maximum possible conversion
- Reversibility: ideal frictionless operation
- Isothermal: constant temperature exchange
- Adiabatic: no heat exchange with environment

When epistemic Carnot cycle IS present:
- Process operating between intellectual reservoirs
- Source of high-energy intellectual input
- Sink absorbing intellectual waste
- Approaching maximum possible efficiency
- Idealized frictionless intellectual operation
- Constant-temperature intellectual exchanges
- Isolated steps with no external exchange

When irreversible process is present:
- Process not operating between reservoirs
- No clear energy source
- No clear waste sink
- Far below maximum efficiency
- Significant intellectual friction
- Variable temperature exchanges
- Constant external exchange

Output JSON with: carnot_cycle_present (bool), severity (none/mild/moderate/severe), hot_reservoir (what energy source), cold_reservoir (what waste sink), efficiency (what conversion limit), reversibility (what frictionlessness), recommendation (irreversible_process/mild_carnot/significant_carnot_cycle/major_efficiency_limit/accept_efficiency_bound)."""

EPISTEMIC_CARNOT_CYCLE_PROMPT = """Detect epistemic Carnot cycle:

Hot reservoir: {hot_reservoir}
Cold reservoir: {cold_reservoir}
Efficiency: {efficiency}
Reversibility: {reversibility}
Domain: {domain}
Context: {context}

Is this intellectual process operating between hot and cold reservoirs with maximum theoretical efficiency? Return ONLY valid JSON."""


class EpistemicCarnotCycleService:
    """Detects epistemic Carnot cycle — maximum efficiency between reservoirs."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        hot_reservoir: str,
        *,
        cold_reservoir: str = "",
        efficiency: str = "",
        reversibility: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic Carnot cycle."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_CARNOT_CYCLE_PROMPT.format(
                hot_reservoir=hot_reservoir,
                cold_reservoir=cold_reservoir or "Not specified",
                efficiency=efficiency or "Not specified",
                reversibility=reversibility or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_CARNOT_CYCLE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "hot_reservoir": hot_reservoir[:200],
            "carnot_cycle_present": data.get("carnot_cycle_present", False),
            "severity": data.get("severity", ""),
            "cold_reservoir": data.get("cold_reservoir", ""),
            "efficiency": data.get("efficiency", ""),
            "reversibility": data.get("reversibility", ""),
            "recommendation": data.get("recommendation", ""),
        }
