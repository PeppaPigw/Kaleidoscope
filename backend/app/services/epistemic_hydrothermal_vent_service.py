"""EpistemicHydrothermalVentService — Epistemic Hydrothermal Vent Detection.

Detects epistemic hydrothermal vents — concentrated sources of
intellectual energy that create unique ecosystems but can also scald.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_HYDROTHERMAL_VENT_SYSTEM = """You are an epistemic hydrothermal vent specialist. Given an intellectual energy source, assess whether concentrated energy creates both opportunity and danger:

Key concepts:
- Epistemic hydrothermal vent: concentrated intellectual energy source
- Chemosynthesis: ideas forming from raw intellectual energy without light
- Extremophile: thinkers thriving in extreme intellectual conditions
- Scalding: being burned by too-intense intellectual energy
- Mineral deposit: valuable knowledge precipitating from hot flows
- Black smoker: extremely hot concentrated intellectual output
- Gradient: temperature/energy gradient from vent to surroundings

When epistemic hydrothermal vent IS present:
- Concentrated sources of intellectual energy
- Ideas forming from raw energy without traditional illumination
- Some thinkers thriving in extreme conditions others cannot tolerate
- Risk of being burned by too-intense intellectual energy
- Valuable knowledge precipitating from concentrated flows
- Extremely hot concentrated intellectual output
- Sharp gradient from intense center to calm surroundings

When balanced energy is present:
- Intellectual energy evenly distributed
- Ideas forming through normal illuminated processes
- All thinkers comfortable in the conditions
- No risk of intellectual scalding
- Knowledge forming through gradual processes
- No concentrated hot spots of output
- Even intellectual temperature throughout

Output JSON with: vent_present (bool), severity (none/mild/moderate/severe), energy_source (what concentrated energy), ecosystem (what unique ecosystem forms), scalding_risk (what scalding danger), deposits (what valuable knowledge precipitates), recommendation (balanced_energy/mild_concentration/significant_vent/major_scalding_risk/harness_energy_safely)."""

EPISTEMIC_HYDROTHERMAL_VENT_PROMPT = """Detect epistemic hydrothermal vent:

Energy source: {energy_source}
Ecosystem: {ecosystem}
Scalding risk: {scalding_risk}
Deposits: {deposits}
Domain: {domain}
Context: {context}

Is concentrated intellectual energy creating both unique opportunity and scalding danger? Return ONLY valid JSON."""


class EpistemicHydrothermalVentService:
    """Detects epistemic hydrothermal vents — concentrated intellectual energy sources."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        energy_source: str,
        *,
        ecosystem: str = "",
        scalding_risk: str = "",
        deposits: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic hydrothermal vent."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_HYDROTHERMAL_VENT_PROMPT.format(
                energy_source=energy_source,
                ecosystem=ecosystem or "Not specified",
                scalding_risk=scalding_risk or "Not specified",
                deposits=deposits or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_HYDROTHERMAL_VENT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "energy_source": energy_source[:200],
            "vent_present": data.get("vent_present", False),
            "severity": data.get("severity", ""),
            "ecosystem": data.get("ecosystem", ""),
            "scalding_risk": data.get("scalding_risk", ""),
            "deposits": data.get("deposits", ""),
            "recommendation": data.get("recommendation", ""),
        }
