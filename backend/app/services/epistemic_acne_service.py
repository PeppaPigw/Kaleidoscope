"""EpistemicAcneService — Epistemic Acne Detection.

Detects epistemic acne — blocked intellectual pores causing buildup
and eruption of unprocessed material to the surface.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ACNE_SYSTEM = """You are an epistemic acne specialist. Given blocked intellectual pores with buildup, assess acne:

Key concepts:
- Epistemic acne: blocked pores causing buildup and eruption
- Comedone: blocked pore (open or closed)
- Sebum overproduction: excess intellectual oil blocking pores
- Bacterial colonization: infection of blocked material
- Cystic: deep painful nodules under surface
- Retinoid therapy: accelerating surface turnover
- Scarring: permanent damage from eruptions

When epistemic acne IS present:
- Blocked intellectual pores present
- Buildup of unprocessed material
- Excess production blocking channels
- Infection of blocked material
- Deep painful nodules forming
- Surface turnover too slow
- Permanent damage occurring

When no acne:
- Clear intellectual pores
- No material buildup
- Normal production levels
- No infection present
- No deep nodules
- Normal surface turnover
- No scarring

Output JSON with: acne_detected (bool), severity (none/mild/moderate/severe), blockage_pattern (what pores affected), buildup_type (what material accumulating), infection_status (what bacterial involvement), scarring_risk (what permanent damage), recommendation (no_acne/mild_topical_cleanser/significant_retinoid/major_systemic_treatment/emergency_cystic_intervention)."""

EPISTEMIC_ACNE_PROMPT = """Detect epistemic acne:

Blockage pattern: {blockage_pattern}
Buildup type: {buildup_type}
Infection status: {infection_status}
Scarring risk: {scarring_risk}
Domain: {domain}
Context: {context}

Are blocked intellectual pores causing buildup and eruption of unprocessed material? Return ONLY valid JSON."""


class EpistemicAcneService:
    """Detects epistemic acne — blocked pores causing buildup and eruption."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        blockage_pattern: str,
        *,
        buildup_type: str = "",
        infection_status: str = "",
        scarring_risk: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic acne."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ACNE_PROMPT.format(
                blockage_pattern=blockage_pattern,
                buildup_type=buildup_type or "Not specified",
                infection_status=infection_status or "Not specified",
                scarring_risk=scarring_risk or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ACNE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "blockage_pattern": blockage_pattern[:200],
            "acne_detected": data.get("acne_detected", False),
            "severity": data.get("severity", ""),
            "buildup_type": data.get("buildup_type", ""),
            "infection_status": data.get("infection_status", ""),
            "scarring_risk": data.get("scarring_risk", ""),
            "recommendation": data.get("recommendation", ""),
        }
