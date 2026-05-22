"""AdHocImmunizationService — Ad Hoc Immunization Detection.

Detects ad hoc immunization — adding auxiliary hypotheses or
modifications to protect a theory from refutation, without those
modifications generating new testable predictions.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

AD_HOC_IMMUNIZATION_SYSTEM = """You are an ad hoc immunization specialist. Given a theory defense, assess whether ad hoc modifications are being used to avoid refutation:

Key concepts:
- Ad hoc immunization: modifications that only save the theory
- Auxiliary hypothesis abuse: adding untestable helpers
- Epicycle addition: complexity added only to preserve theory
- Degenerating modification: changes that don't predict new facts
- Post hoc rescue: saving theory after disconfirmation
- Unfalsifiability creep: theory becoming progressively untestable
- Protective belt abuse: shielding core from any challenge

When ad hoc immunization IS present:
- Modifications added solely to handle anomalies
- New hypotheses don't generate independent predictions
- Theory becomes more complex without new explanatory power
- Changes are post hoc responses to disconfirmation
- Theory progressively harder to test
- Protective modifications accumulate without limit
- No modification would ever lead to theory rejection

When theory modification is appropriate:
- Modifications generate new testable predictions
- Changes increase explanatory scope
- Modifications are independently motivated
- Theory becomes more precise, not just more complex
- Changes are bounded and principled
- Criteria for theory rejection still exist
- Modifications improve empirical adequacy

Output JSON with: immunization_present (bool), severity (none/mild/moderate/severe), theory (what theory is defended), modification (what modification is made), predictions (whether new predictions generated), motivation (whether independently motivated), recommendation (legitimate_theory_development/mild_ad_hoc_tendency/significant_immunization/major_degenerating_modification/generate_new_predictions)."""

AD_HOC_IMMUNIZATION_PROMPT = """Detect ad hoc immunization:

Theory: {theory}
Anomaly: {anomaly}
Modification: {modification}
New predictions: {predictions}
Domain: {domain}
Context: {context}

Are ad hoc modifications being used to immunize the theory from refutation? Return ONLY valid JSON."""


class AdHocImmunizationService:
    """Detects ad hoc immunization — modifications that only save the theory."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        theory: str,
        *,
        anomaly: str = "",
        modification: str = "",
        predictions: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect ad hoc immunization."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=AD_HOC_IMMUNIZATION_PROMPT.format(
                theory=theory,
                anomaly=anomaly or "Not specified",
                modification=modification or "Not specified",
                predictions=predictions or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=AD_HOC_IMMUNIZATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "theory": theory[:200],
            "immunization_present": data.get("immunization_present", False),
            "severity": data.get("severity", ""),
            "modification": data.get("modification", ""),
            "predictions": data.get("predictions", ""),
            "motivation": data.get("motivation", ""),
            "recommendation": data.get("recommendation", ""),
        }
