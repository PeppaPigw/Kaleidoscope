"""EpistemicGrowthHormoneDeficitService — Epistemic Growth Hormone Deficit Detection.

Detects epistemic growth hormone deficit — insufficient growth signaling
preventing intellectual development and renewal.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_GROWTH_HORMONE_DEFICIT_SYSTEM = """You are an epistemic growth hormone deficit specialist. Given insufficient intellectual growth signaling, assess:

Key concepts:
- Epistemic growth hormone deficit: insufficient growth signaling
- Stunted development: intellectual growth arrested
- Delayed maturation: milestones not reached on time
- Body composition: ratio of active to inactive intellectual mass
- IGF-1 deficiency: downstream growth factor missing
- Replacement therapy: supplementing growth signals
- Catch-up growth: accelerated development after treatment

When epistemic growth hormone deficit IS present:
- Insufficient growth signaling
- Intellectual growth arrested
- Milestones not reached on time
- Poor ratio of active to inactive mass
- Downstream growth factors missing
- Growth signal supplementation needed
- No catch-up growth occurring

When no growth hormone deficit:
- Adequate growth signaling
- Normal intellectual growth
- Milestones reached on time
- Healthy active/inactive ratio
- Growth factors present
- No supplementation needed
- Normal development trajectory

Output JSON with: growth_deficit_detected (bool), severity (none/mild/moderate/severe), growth_rate (what development speed), maturation_status (what milestone progress), composition (what active/inactive ratio), igf1_level (what downstream signaling), recommendation (no_deficit/mild_monitoring/significant_stimulation/major_replacement_therapy/emergency_pituitary_crisis)."""

EPISTEMIC_GROWTH_HORMONE_DEFICIT_PROMPT = """Detect epistemic growth hormone deficit:

Growth rate: {growth_rate}
Maturation status: {maturation_status}
Composition: {composition}
IGF-1 level: {igf1_level}
Domain: {domain}
Context: {context}

Is there insufficient growth signaling preventing intellectual development and renewal? Return ONLY valid JSON."""


class EpistemicGrowthHormoneDeficitService:
    """Detects epistemic growth hormone deficit — insufficient growth signaling."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        growth_rate: str,
        *,
        maturation_status: str = "",
        composition: str = "",
        igf1_level: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic growth hormone deficit."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_GROWTH_HORMONE_DEFICIT_PROMPT.format(
                growth_rate=growth_rate,
                maturation_status=maturation_status or "Not specified",
                composition=composition or "Not specified",
                igf1_level=igf1_level or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_GROWTH_HORMONE_DEFICIT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "growth_rate": growth_rate[:200],
            "growth_deficit_detected": data.get("growth_deficit_detected", False),
            "severity": data.get("severity", ""),
            "maturation_status": data.get("maturation_status", ""),
            "composition": data.get("composition", ""),
            "igf1_level": data.get("igf1_level", ""),
            "recommendation": data.get("recommendation", ""),
        }
