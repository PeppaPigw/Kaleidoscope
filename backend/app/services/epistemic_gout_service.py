"""EpistemicGoutService — Epistemic Gout Detection.

Detects epistemic gout — crystal deposits in intellectual joints from
excess metabolic waste causing acute inflammatory attacks.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_GOUT_SYSTEM = """You are an epistemic gout specialist. Given crystal deposits in intellectual joints, assess gout:

Key concepts:
- Epistemic gout: crystal deposits from excess metabolic waste
- Urate crystals: sharp deposits triggering inflammation
- Acute attack: sudden severe joint inflammation
- Tophi: chronic crystal deposits forming lumps
- Hyperuricemia: excess waste in intellectual bloodstream
- Colchicine: anti-inflammatory for acute attacks
- Urate-lowering: reducing waste production or increasing clearance

When epistemic gout IS present:
- Crystal deposits in intellectual joints
- Sharp deposits triggering inflammation
- Sudden severe attacks occurring
- Chronic deposits forming lumps
- Excess waste in intellectual system
- Anti-inflammatory intervention needed
- Waste reduction required

When no gout:
- No crystal deposits
- No sharp inflammatory triggers
- No sudden attacks
- No chronic lumps
- Normal waste levels
- No anti-inflammatory needed
- Normal waste clearance

Output JSON with: gout_detected (bool), severity (none/mild/moderate/severe), crystal_burden (what deposits), attack_frequency (what acute episodes), tophi_status (what chronic lumps), urate_level (what waste concentration), recommendation (no_gout/mild_lifestyle/significant_urate_lowering/major_combination_therapy/emergency_polyarticular_attack)."""

EPISTEMIC_GOUT_PROMPT = """Detect epistemic gout:

Crystal burden: {crystal_burden}
Attack frequency: {attack_frequency}
Tophi status: {tophi_status}
Urate level: {urate_level}
Domain: {domain}
Context: {context}

Are crystal deposits from excess metabolic waste causing acute inflammatory attacks? Return ONLY valid JSON."""


class EpistemicGoutService:
    """Detects epistemic gout — crystal deposits causing inflammatory attacks."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        crystal_burden: str,
        *,
        attack_frequency: str = "",
        tophi_status: str = "",
        urate_level: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic gout."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_GOUT_PROMPT.format(
                crystal_burden=crystal_burden,
                attack_frequency=attack_frequency or "Not specified",
                tophi_status=tophi_status or "Not specified",
                urate_level=urate_level or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_GOUT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "crystal_burden": crystal_burden[:200],
            "gout_detected": data.get("gout_detected", False),
            "severity": data.get("severity", ""),
            "attack_frequency": data.get("attack_frequency", ""),
            "tophi_status": data.get("tophi_status", ""),
            "urate_level": data.get("urate_level", ""),
            "recommendation": data.get("recommendation", ""),
        }
