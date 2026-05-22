"""EpistemicAneurysmService — Epistemic Aneurysm Detection.

Detects epistemic aneurysm — weakened intellectual vessel walls that bulge
under pressure, at risk of catastrophic rupture.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ANEURYSM_SYSTEM = """You are an epistemic aneurysm specialist. Given intellectual vessels, assess whether weakened walls are at risk of rupture:

Key concepts:
- Epistemic aneurysm: weakened intellectual vessel at risk of rupture
- Wall thinning: structural weakness in intellectual channel
- Dilation: abnormal expansion of weakened area
- Rupture risk: probability of catastrophic failure
- Hemodynamic stress: pressure forces on weakened wall
- Dissection: wall layers separating under pressure
- Sentinel leak: small warning bleed before major rupture

When epistemic aneurysm IS present:
- Weakened intellectual vessel walls bulging under pressure
- Structural weakness in intellectual channels
- Abnormal expansion of weakened areas
- Risk of catastrophic failure
- Pressure forces stressing weakened walls
- Wall layers separating under intellectual pressure
- Small warning signs before major failure

When healthy vessels are present:
- Strong vessel walls
- No structural weakness
- Normal vessel diameter
- No rupture risk
- Walls handling pressure well
- Intact wall layers
- No warning signs

Output JSON with: aneurysm_present (bool), severity (none/mild/moderate/severe), wall_thinning (what structural weakness), dilation (what abnormal expansion), rupture_risk (what failure probability), hemodynamic_stress (what pressure forces), recommendation (healthy_vessels/mild_aneurysm/significant_aneurysm/major_rupture_risk/reinforce_intellectual_walls)."""

EPISTEMIC_ANEURYSM_PROMPT = """Detect epistemic aneurysm:

Wall thinning: {wall_thinning}
Dilation: {dilation}
Rupture risk: {rupture_risk}
Hemodynamic stress: {hemodynamic_stress}
Domain: {domain}
Context: {context}

Are weakened intellectual vessel walls bulging under pressure, at risk of catastrophic rupture? Return ONLY valid JSON."""


class EpistemicAneurysmService:
    """Detects epistemic aneurysm — weakened intellectual vessels at risk of rupture."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        wall_thinning: str,
        *,
        dilation: str = "",
        rupture_risk: str = "",
        hemodynamic_stress: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic aneurysm."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ANEURYSM_PROMPT.format(
                wall_thinning=wall_thinning,
                dilation=dilation or "Not specified",
                rupture_risk=rupture_risk or "Not specified",
                hemodynamic_stress=hemodynamic_stress or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ANEURYSM_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "wall_thinning": wall_thinning[:200],
            "aneurysm_present": data.get("aneurysm_present", False),
            "severity": data.get("severity", ""),
            "dilation": data.get("dilation", ""),
            "rupture_risk": data.get("rupture_risk", ""),
            "hemodynamic_stress": data.get("hemodynamic_stress", ""),
            "recommendation": data.get("recommendation", ""),
        }
