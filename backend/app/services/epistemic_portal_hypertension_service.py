"""EpistemicPortalHypertensionService — Epistemic Portal Hypertension Detection.

Detects epistemic portal hypertension — pressure buildup from blocked
intellectual processing, forcing ideas through dangerous alternative routes.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PORTAL_HYPERTENSION_SYSTEM = """You are an epistemic portal hypertension specialist. Given intellectual processing pressure, assess whether blockage forces dangerous alternative routing:

Key concepts:
- Epistemic portal hypertension: pressure buildup from blocked processing
- Varices: dilated alternative routes under pressure
- Collateral circulation: bypass routes around blockage
- Ascites: fluid accumulation from pressure
- Splenomegaly: upstream organ enlargement from backup
- Shunting: blood/ideas bypassing processing entirely
- Decompression: reducing the dangerous pressure

When epistemic portal hypertension IS present:
- Pressure building from blocked intellectual processing
- Dilated alternative routes under dangerous pressure
- Bypass routes developing around blockages
- Fluid/ideas accumulating from pressure
- Upstream systems enlarging from backup
- Ideas bypassing processing entirely
- Need for pressure reduction

When healthy processing is present:
- Normal processing pressure
- No dilated alternatives
- No bypass routes needed
- No fluid accumulation
- Normal upstream size
- All ideas properly processed
- No decompression needed

Output JSON with: portal_hypertension_present (bool), severity (none/mild/moderate/severe), varices (what dilated alternatives), collateral_circulation (what bypass routes), ascites (what accumulation), shunting (what processing bypass), recommendation (healthy_processing/mild_hypertension/significant_portal_hypertension/major_pressure_buildup/decompress_intellectual_system)."""

EPISTEMIC_PORTAL_HYPERTENSION_PROMPT = """Detect epistemic portal hypertension:

Varices: {varices}
Collateral circulation: {collateral_circulation}
Ascites: {ascites}
Shunting: {shunting}
Domain: {domain}
Context: {context}

Is pressure building from blocked intellectual processing, forcing ideas through dangerous alternative routes? Return ONLY valid JSON."""


class EpistemicPortalHypertensionService:
    """Detects epistemic portal hypertension — pressure from blocked processing."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        varices: str,
        *,
        collateral_circulation: str = "",
        ascites: str = "",
        shunting: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic portal hypertension."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PORTAL_HYPERTENSION_PROMPT.format(
                varices=varices,
                collateral_circulation=collateral_circulation or "Not specified",
                ascites=ascites or "Not specified",
                shunting=shunting or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PORTAL_HYPERTENSION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "varices": varices[:200],
            "portal_hypertension_present": data.get("portal_hypertension_present", False),
            "severity": data.get("severity", ""),
            "collateral_circulation": data.get("collateral_circulation", ""),
            "ascites": data.get("ascites", ""),
            "shunting": data.get("shunting", ""),
            "recommendation": data.get("recommendation", ""),
        }
