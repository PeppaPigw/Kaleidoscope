"""EpistemicPrematureDeliveryService — Epistemic Premature Delivery Detection.

Detects epistemic premature delivery — intellectual creation born too early,
before full development, requiring special support.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PREMATURE_DELIVERY_SYSTEM = """You are an epistemic premature delivery specialist. Given intellectual creations born too early, assess prematurity:

Key concepts:
- Epistemic premature delivery: creation born before full development
- Gestational age: how developed the creation is
- NICU: intensive care for premature creations
- Surfactant: substance needed for intellectual breathing
- Retinopathy: vision problems from prematurity
- Necrotizing enterocolitis: gut damage in premature
- Developmental delay: falling behind expected milestones

When epistemic premature delivery IS occurring:
- Creation delivered before full development
- Low gestational age at delivery
- Intensive care needed for survival
- Missing substances for function
- Vision/perception problems from early delivery
- Gut/processing damage from immaturity
- Falling behind expected milestones

When no premature delivery:
- Full-term delivery
- Complete development at birth
- No intensive care needed
- All substances present
- Normal perception
- Normal processing
- Meeting milestones

Output JSON with: premature_delivery (bool), severity (none/mild/moderate/severe), gestational_age (what development level), nicu_needs (what intensive support), surfactant_status (what substance availability), developmental_outlook (what milestone expectation), recommendation (no_prematurity/mild_late_preterm/significant_moderate_preterm/major_very_preterm/emergency_extreme_preterm)."""

EPISTEMIC_PREMATURE_DELIVERY_PROMPT = """Detect epistemic premature delivery:

Gestational age: {gestational_age}
NICU needs: {nicu_needs}
Surfactant status: {surfactant_status}
Developmental outlook: {developmental_outlook}
Domain: {domain}
Context: {context}

Was the intellectual creation delivered before full development? Return ONLY valid JSON."""


class EpistemicPrematureDeliveryService:
    """Detects epistemic premature delivery — creation born before full development."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        gestational_age: str,
        *,
        nicu_needs: str = "",
        surfactant_status: str = "",
        developmental_outlook: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic premature delivery."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PREMATURE_DELIVERY_PROMPT.format(
                gestational_age=gestational_age,
                nicu_needs=nicu_needs or "Not specified",
                surfactant_status=surfactant_status or "Not specified",
                developmental_outlook=developmental_outlook or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PREMATURE_DELIVERY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "gestational_age": gestational_age[:200],
            "premature_delivery": data.get("premature_delivery", False),
            "severity": data.get("severity", ""),
            "nicu_needs": data.get("nicu_needs", ""),
            "surfactant_status": data.get("surfactant_status", ""),
            "developmental_outlook": data.get("developmental_outlook", ""),
            "recommendation": data.get("recommendation", ""),
        }
