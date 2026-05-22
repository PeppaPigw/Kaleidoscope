"""EpistemicCauterizationService — Epistemic Cauterization Detection.

Detects need for epistemic cauterization — burning intellectual tissue
to stop bleeding, remove abnormal growth, or prevent infection spread.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_CAUTERIZATION_SYSTEM = """You are an epistemic cauterization specialist. Given intellectual bleeding or abnormal growth, assess cauterization need:

Key concepts:
- Epistemic cauterization: burning to stop bleeding or remove growth
- Hemostasis: stopping intellectual bleeding through heat
- Ablation: destroying abnormal intellectual tissue
- Electrocautery: using electrical current to burn
- Chemical cautery: using agents to destroy tissue
- Coagulation: forming clot through heat application
- Eschar: burned tissue forming protective layer

When epistemic cauterization IS needed:
- Intellectual bleeding not stopping naturally
- Abnormal growth requiring destruction
- Electrical destruction appropriate
- Chemical destruction needed
- Clot formation required
- Protective layer needed
- Infection spread prevention

When no cauterization needed:
- No active bleeding
- No abnormal growth
- Natural hemostasis working
- No destruction needed
- Normal clotting
- No protection needed
- No infection spread

Output JSON with: cauterization_needed (bool), severity (none/mild/moderate/severe), bleeding_source (what hemorrhage), growth_type (what abnormality), cautery_method (what burning approach), hemostasis_status (what clotting state), recommendation (no_cauterization_needed/mild_chemical/significant_electrocautery/major_ablation/emergency_hemorrhage_control)."""

EPISTEMIC_CAUTERIZATION_PROMPT = """Detect epistemic cauterization need:

Bleeding source: {bleeding_source}
Growth type: {growth_type}
Cautery method: {cautery_method}
Hemostasis status: {hemostasis_status}
Domain: {domain}
Context: {context}

Is intellectual bleeding or abnormal growth requiring cauterization? Return ONLY valid JSON."""


class EpistemicCauterizationService:
    """Detects epistemic cauterization need — burning to stop bleeding or remove growth."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        bleeding_source: str,
        *,
        growth_type: str = "",
        cautery_method: str = "",
        hemostasis_status: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic cauterization need."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_CAUTERIZATION_PROMPT.format(
                bleeding_source=bleeding_source,
                growth_type=growth_type or "Not specified",
                cautery_method=cautery_method or "Not specified",
                hemostasis_status=hemostasis_status or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_CAUTERIZATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "bleeding_source": bleeding_source[:200],
            "cauterization_needed": data.get("cauterization_needed", False),
            "severity": data.get("severity", ""),
            "growth_type": data.get("growth_type", ""),
            "cautery_method": data.get("cautery_method", ""),
            "hemostasis_status": data.get("hemostasis_status", ""),
            "recommendation": data.get("recommendation", ""),
        }
