"""EpistemicThermohalineService — Epistemic Thermohaline Circulation Detection.

Detects epistemic thermohaline circulation failure — the deep
knowledge circulation that drives intellectual climate stopping.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_THERMOHALINE_SYSTEM = """You are an epistemic thermohaline circulation specialist. Given a knowledge circulation pattern, assess whether deep circulation has stopped:

Key concepts:
- Epistemic thermohaline: deep knowledge circulation driving intellectual climate
- Circulation failure: deep knowledge flows stopping
- Density-driven: circulation driven by knowledge density differences
- Conveyor belt: global circulation pattern connecting all knowledge areas
- Stagnation: knowledge becoming stagnant without circulation
- Climate shift: intellectual climate changing when circulation stops
- Deep water formation: where dense knowledge sinks and drives circulation

When thermohaline failure IS present:
- Deep knowledge circulation has stopped or slowed
- Knowledge flows no longer connecting different areas
- Density differences no longer driving circulation
- Global knowledge conveyor belt breaking down
- Knowledge becoming stagnant in isolated pools
- Intellectual climate shifting due to circulation failure
- No new dense knowledge sinking to drive circulation

When healthy circulation is present:
- Deep knowledge circulation functioning normally
- Knowledge flows connecting all areas effectively
- Density differences driving healthy circulation
- Global knowledge conveyor belt operating
- Knowledge remaining fresh through circulation
- Intellectual climate stable due to circulation
- Dense knowledge sinking and driving flows

Output JSON with: thermohaline_failure (bool), severity (none/mild/moderate/severe), circulation (what circulation fails), stagnation (what knowledge stagnates), climate_shift (what climate changes), conveyor (what conveyor breaks), recommendation (healthy_circulation/mild_slowdown/significant_failure/major_climate_shift/restart_circulation)."""

EPISTEMIC_THERMOHALINE_PROMPT = """Detect epistemic thermohaline circulation failure:

Circulation: {circulation}
Stagnation: {stagnation}
Climate shift: {climate_shift}
Conveyor: {conveyor}
Domain: {domain}
Context: {context}

Has deep knowledge circulation stopped causing intellectual climate change? Return ONLY valid JSON."""


class EpistemicThermohalineService:
    """Detects epistemic thermohaline failure — deep knowledge circulation stopping."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        circulation: str,
        *,
        stagnation: str = "",
        climate_shift: str = "",
        conveyor: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic thermohaline circulation failure."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_THERMOHALINE_PROMPT.format(
                circulation=circulation,
                stagnation=stagnation or "Not specified",
                climate_shift=climate_shift or "Not specified",
                conveyor=conveyor or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_THERMOHALINE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "circulation": circulation[:200],
            "thermohaline_failure": data.get("thermohaline_failure", False),
            "severity": data.get("severity", ""),
            "stagnation": data.get("stagnation", ""),
            "climate_shift": data.get("climate_shift", ""),
            "conveyor": data.get("conveyor", ""),
            "recommendation": data.get("recommendation", ""),
        }
