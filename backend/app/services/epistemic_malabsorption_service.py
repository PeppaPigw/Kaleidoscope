"""EpistemicMalabsorptionService — Epistemic Malabsorption Detection.

Detects epistemic malabsorption — inability to absorb intellectual
nutrients despite adequate exposure to information.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_MALABSORPTION_SYSTEM = """You are an epistemic malabsorption specialist. Given intellectual nutrient intake, assess whether absorption is failing:

Key concepts:
- Epistemic malabsorption: inability to absorb intellectual nutrients despite exposure
- Villous atrophy: loss of absorptive surface area
- Enzyme deficiency: lacking digestive machinery
- Bile salt deficiency: inability to emulsify complex ideas
- Bacterial overgrowth: competing organisms consuming nutrients
- Steatorrhea: undigested intellectual fat passing through
- Nutritional deficiency: downstream effects of poor absorption

When epistemic malabsorption IS present:
- Inability to absorb intellectual nutrients despite exposure
- Loss of absorptive surface area
- Lacking machinery to digest complex ideas
- Inability to break down complex intellectual material
- Competing processes consuming available nutrients
- Undigested material passing through without absorption
- Downstream deficiencies from poor absorption

When healthy absorption is present:
- Effective nutrient absorption
- Full absorptive surface
- Adequate digestive machinery
- Complex ideas properly emulsified
- No competing consumption
- Complete digestion and absorption
- No nutritional deficiencies

Output JSON with: malabsorption_present (bool), severity (none/mild/moderate/severe), villous_atrophy (what surface loss), enzyme_deficiency (what lacking machinery), bacterial_overgrowth (what competing consumption), nutritional_deficiency (what downstream effects), recommendation (healthy_absorption/mild_malabsorption/significant_malabsorption/major_absorption_failure/restore_absorptive_capacity)."""

EPISTEMIC_MALABSORPTION_PROMPT = """Detect epistemic malabsorption:

Villous atrophy: {villous_atrophy}
Enzyme deficiency: {enzyme_deficiency}
Bacterial overgrowth: {bacterial_overgrowth}
Nutritional deficiency: {nutritional_deficiency}
Domain: {domain}
Context: {context}

Is there inability to absorb intellectual nutrients despite adequate exposure? Return ONLY valid JSON."""


class EpistemicMalabsorptionService:
    """Detects epistemic malabsorption — inability to absorb despite exposure."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        villous_atrophy: str,
        *,
        enzyme_deficiency: str = "",
        bacterial_overgrowth: str = "",
        nutritional_deficiency: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic malabsorption."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_MALABSORPTION_PROMPT.format(
                villous_atrophy=villous_atrophy,
                enzyme_deficiency=enzyme_deficiency or "Not specified",
                bacterial_overgrowth=bacterial_overgrowth or "Not specified",
                nutritional_deficiency=nutritional_deficiency or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_MALABSORPTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "villous_atrophy": villous_atrophy[:200],
            "malabsorption_present": data.get("malabsorption_present", False),
            "severity": data.get("severity", ""),
            "enzyme_deficiency": data.get("enzyme_deficiency", ""),
            "bacterial_overgrowth": data.get("bacterial_overgrowth", ""),
            "nutritional_deficiency": data.get("nutritional_deficiency", ""),
            "recommendation": data.get("recommendation", ""),
        }
