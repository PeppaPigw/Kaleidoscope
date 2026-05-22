"""EpistemicGestationalDiabetesService — Epistemic Gestational Diabetes Detection.

Detects epistemic gestational diabetes — metabolic dysfunction during
intellectual gestation causing excessive growth or complications.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_GESTATIONAL_DIABETES_SYSTEM = """You are an epistemic gestational diabetes specialist. Given metabolic dysfunction during intellectual gestation, assess:

Key concepts:
- Epistemic gestational diabetes: metabolic dysfunction during creation
- Macrosomia: creation growing excessively large
- Glucose intolerance: inability to process intellectual fuel properly
- Insulin resistance: reduced response to regulatory signals
- Polyhydramnios: excessive intellectual fluid accumulation
- Shoulder dystocia: large creation stuck during delivery
- Postpartum resolution: whether dysfunction resolves after delivery

When epistemic gestational diabetes IS present:
- Metabolic dysfunction during creation process
- Creation growing excessively large
- Inability to process fuel properly
- Reduced response to regulation
- Excessive fluid accumulation
- Delivery complications from size
- Uncertain post-delivery resolution

When no gestational diabetes:
- Normal metabolism during creation
- Appropriate creation size
- Normal fuel processing
- Normal regulatory response
- Normal fluid levels
- No size-related complications
- Normal metabolic function

Output JSON with: gestational_diabetes (bool), severity (none/mild/moderate/severe), macrosomia_risk (what excessive growth), glucose_status (what fuel processing), insulin_response (what regulation), delivery_risk (what size complications), recommendation (no_gestational_diabetes/mild_diet_control/significant_monitoring/major_insulin_required/emergency_metabolic_crisis)."""

EPISTEMIC_GESTATIONAL_DIABETES_PROMPT = """Detect epistemic gestational diabetes:

Macrosomia risk: {macrosomia_risk}
Glucose status: {glucose_status}
Insulin response: {insulin_response}
Delivery risk: {delivery_risk}
Domain: {domain}
Context: {context}

Is there metabolic dysfunction during intellectual gestation? Return ONLY valid JSON."""


class EpistemicGestationalDiabetesService:
    """Detects epistemic gestational diabetes — metabolic dysfunction during creation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        macrosomia_risk: str,
        *,
        glucose_status: str = "",
        insulin_response: str = "",
        delivery_risk: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic gestational diabetes."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_GESTATIONAL_DIABETES_PROMPT.format(
                macrosomia_risk=macrosomia_risk,
                glucose_status=glucose_status or "Not specified",
                insulin_response=insulin_response or "Not specified",
                delivery_risk=delivery_risk or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_GESTATIONAL_DIABETES_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "macrosomia_risk": macrosomia_risk[:200],
            "gestational_diabetes": data.get("gestational_diabetes", False),
            "severity": data.get("severity", ""),
            "glucose_status": data.get("glucose_status", ""),
            "insulin_response": data.get("insulin_response", ""),
            "delivery_risk": data.get("delivery_risk", ""),
            "recommendation": data.get("recommendation", ""),
        }
