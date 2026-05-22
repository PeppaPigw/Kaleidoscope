"""EpistemicTendinopathyService — Epistemic Tendinopathy Detection.

Detects epistemic tendinopathy — chronic overuse injury to intellectual
connective tissue linking concepts to action.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_TENDINOPATHY_SYSTEM = """You are an epistemic tendinopathy specialist. Given chronic intellectual overuse injury, assess tendinopathy:

Key concepts:
- Epistemic tendinopathy: chronic overuse of intellectual connectors
- Tendinosis: degenerative changes without inflammation
- Tendinitis: acute inflammatory response
- Load management: adjusting demands on connector
- Eccentric loading: strengthening through controlled stress
- Neovascularization: abnormal vessel growth in damaged tissue
- Rupture risk: complete failure of connector

When epistemic tendinopathy IS present:
- Chronic overuse of intellectual connectors
- Degenerative changes present
- Acute inflammatory response
- Demands exceeding connector capacity
- Controlled stress not applied
- Abnormal growth in damaged area
- Risk of complete failure

When no tendinopathy:
- Normal connector use
- No degenerative changes
- No inflammation
- Demands within capacity
- Appropriate stress applied
- Normal tissue structure
- No failure risk

Output JSON with: tendinopathy_detected (bool), severity (none/mild/moderate/severe), degeneration_stage (what tissue state), load_status (what demand level), inflammation_signs (what acute response), rupture_risk (what failure danger), recommendation (no_tendinopathy/mild_load_modification/significant_rehabilitation/major_extended_rest/emergency_rupture_prevention)."""

EPISTEMIC_TENDINOPATHY_PROMPT = """Detect epistemic tendinopathy:

Degeneration stage: {degeneration_stage}
Load status: {load_status}
Inflammation signs: {inflammation_signs}
Rupture risk: {rupture_risk}
Domain: {domain}
Context: {context}

Is there chronic overuse injury to intellectual connective tissue? Return ONLY valid JSON."""


class EpistemicTendinopathyService:
    """Detects epistemic tendinopathy — chronic overuse of intellectual connectors."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        degeneration_stage: str,
        *,
        load_status: str = "",
        inflammation_signs: str = "",
        rupture_risk: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic tendinopathy."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_TENDINOPATHY_PROMPT.format(
                degeneration_stage=degeneration_stage,
                load_status=load_status or "Not specified",
                inflammation_signs=inflammation_signs or "Not specified",
                rupture_risk=rupture_risk or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_TENDINOPATHY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "degeneration_stage": degeneration_stage[:200],
            "tendinopathy_detected": data.get("tendinopathy_detected", False),
            "severity": data.get("severity", ""),
            "load_status": data.get("load_status", ""),
            "inflammation_signs": data.get("inflammation_signs", ""),
            "rupture_risk": data.get("rupture_risk", ""),
            "recommendation": data.get("recommendation", ""),
        }
