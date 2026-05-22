"""EpistemicNutritionSupportService — Epistemic Nutrition Support Detection.

Detects epistemic nutrition support need — intellectual systems unable to
feed themselves, requiring parenteral or enteral intellectual nourishment.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_NUTRITION_SYSTEM = """You are an epistemic nutrition support specialist. Given intellectual feeding failure, assess nutrition support need:

Key concepts:
- Epistemic nutrition: intellectual nourishment delivery
- TPN: total parenteral nutrition bypassing normal intake
- Enteral feeding: delivery through intellectual gut
- Malnutrition: inadequate intellectual nourishment
- Refeeding syndrome: dangerous response to resuming nutrition
- Caloric deficit: insufficient intellectual energy intake
- Micronutrient deficiency: missing specific intellectual elements

When epistemic nutrition support IS needed:
- Cannot feed intellectually through normal means
- Need to bypass normal intake pathway
- Delivery through alternative routes needed
- Inadequate intellectual nourishment present
- Risk of dangerous refeeding response
- Insufficient intellectual energy intake
- Missing specific intellectual elements

When no nutrition support needed:
- Normal intellectual feeding
- Standard intake pathway working
- No alternative routes needed
- Adequate nourishment present
- No refeeding risk
- Sufficient energy intake
- All elements present

Output JSON with: nutrition_support_needed (bool), severity (none/mild/moderate/severe), malnutrition_type (what deficiency), feeding_route (what delivery method), refeeding_risk (what resumption danger), caloric_status (what energy state), recommendation (no_nutrition_support_needed/mild_supplementation/significant_enteral/major_tpn/emergency_severe_malnutrition)."""

EPISTEMIC_NUTRITION_PROMPT = """Detect epistemic nutrition support need:

Malnutrition type: {malnutrition_type}
Feeding route: {feeding_route}
Refeeding risk: {refeeding_risk}
Caloric status: {caloric_status}
Domain: {domain}
Context: {context}

Is the intellectual system unable to nourish itself through normal means? Return ONLY valid JSON."""


class EpistemicNutritionSupportService:
    """Detects epistemic nutrition support need — intellectual feeding failure."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        malnutrition_type: str,
        *,
        feeding_route: str = "",
        refeeding_risk: str = "",
        caloric_status: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic nutrition support need."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_NUTRITION_PROMPT.format(
                malnutrition_type=malnutrition_type,
                feeding_route=feeding_route or "Not specified",
                refeeding_risk=refeeding_risk or "Not specified",
                caloric_status=caloric_status or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_NUTRITION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "malnutrition_type": malnutrition_type[:200],
            "nutrition_support_needed": data.get("nutrition_support_needed", False),
            "severity": data.get("severity", ""),
            "feeding_route": data.get("feeding_route", ""),
            "refeeding_risk": data.get("refeeding_risk", ""),
            "caloric_status": data.get("caloric_status", ""),
            "recommendation": data.get("recommendation", ""),
        }
