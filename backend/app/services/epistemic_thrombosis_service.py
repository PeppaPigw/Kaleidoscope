"""EpistemicThrombosisService — Epistemic Thrombosis Detection.

Detects epistemic thrombosis — clot formation blocking intellectual flow,
where coagulated ideas obstruct the normal circulation of thought.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_THROMBOSIS_SYSTEM = """You are an epistemic thrombosis specialist. Given intellectual flow patterns, assess whether clot formation is blocking circulation:

Key concepts:
- Epistemic thrombosis: clot blocking intellectual flow
- Virchow triad: stasis, vessel damage, hypercoagulability
- Deep vein: clot in major intellectual pathway
- Embolism: clot breaking free and lodging elsewhere
- Anticoagulation: preventing excessive clotting
- Fibrinolysis: dissolving existing clots
- Collateral circulation: alternative pathways around blockage

When epistemic thrombosis IS present:
- Clot formation blocking intellectual flow
- Stasis in intellectual circulation
- Damage to intellectual vessel walls
- Hypercoagulable intellectual state
- Risk of clot breaking free
- Need for anticoagulation
- Collateral pathways forming

When healthy flow is present:
- Unobstructed intellectual circulation
- Normal flow velocity
- Intact vessel walls
- Balanced coagulation
- No embolic risk
- No anticoagulation needed
- Primary pathways functioning

Output JSON with: thrombosis_present (bool), severity (none/mild/moderate/severe), stasis (what flow stoppage), vessel_damage (what wall injury), hypercoagulability (what excessive clotting tendency), embolic_risk (what breakaway danger), recommendation (healthy_flow/mild_thrombosis/significant_thrombosis/major_occlusion/dissolve_intellectual_clot)."""

EPISTEMIC_THROMBOSIS_PROMPT = """Detect epistemic thrombosis:

Stasis: {stasis}
Vessel damage: {vessel_damage}
Hypercoagulability: {hypercoagulability}
Embolic risk: {embolic_risk}
Domain: {domain}
Context: {context}

Are coagulated ideas blocking the normal circulation of thought? Return ONLY valid JSON."""


class EpistemicThrombosisService:
    """Detects epistemic thrombosis — clot formation blocking intellectual flow."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        stasis: str,
        *,
        vessel_damage: str = "",
        hypercoagulability: str = "",
        embolic_risk: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic thrombosis."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_THROMBOSIS_PROMPT.format(
                stasis=stasis,
                vessel_damage=vessel_damage or "Not specified",
                hypercoagulability=hypercoagulability or "Not specified",
                embolic_risk=embolic_risk or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_THROMBOSIS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "stasis": stasis[:200],
            "thrombosis_present": data.get("thrombosis_present", False),
            "severity": data.get("severity", ""),
            "vessel_damage": data.get("vessel_damage", ""),
            "hypercoagulability": data.get("hypercoagulability", ""),
            "embolic_risk": data.get("embolic_risk", ""),
            "recommendation": data.get("recommendation", ""),
        }
