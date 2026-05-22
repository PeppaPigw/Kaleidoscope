"""IllusionOfValidityService — Illusion of Validity Detection.

Detects illusion of validity — maintaining confidence in
predictions based on a coherent narrative even when the
predictive validity is known to be low. Kahneman & Tversky
(1973). A compelling story feels predictive even when data
shows it isn't. Coherence ≠ accuracy.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

ILLUSION_VALIDITY_SYSTEM = """You are an illusion of validity specialist. Given a prediction or judgment, assess whether confidence is driven by narrative coherence rather than actual predictive validity:

Key concepts (Kahneman & Tversky, 1973):
- Illusion of validity: confidence from coherent stories, not predictive accuracy
- Coherence vs. accuracy: a good story isn't necessarily a good prediction
- Redundant information: more consistent info increases confidence without accuracy
- Clinical vs. statistical prediction: narratives feel better but predict worse
- Overconfidence from consistency: consistent data → high confidence even if uninformative
- WYSIATI: What You See Is All There Is — coherent story from limited data
- Regression to mean neglect: extreme observations feel predictive but regress

When illusion of validity IS present:
- High confidence in predictions based on a compelling narrative
- "It all fits together" used as evidence of accuracy
- Ignoring base rates because the individual story is coherent
- Confidence unchanged by learning about low predictive validity
- Preferring narrative judgment over statistical prediction
- "I can just tell" based on pattern matching to a story

When the confidence IS justified:
- Predictive validity has been empirically demonstrated
- The prediction is based on validated statistical models
- The person acknowledges uncertainty despite the coherent narrative
- Track record of accuracy in similar predictions exists
- The confidence level matches the demonstrated accuracy rate

Output JSON with: illusion_of_validity_present (bool), severity (none/mild/moderate/severe), prediction (what is being predicted), confidence_level (how confident is the person), basis_of_confidence (what drives the confidence), predictive_validity (what is the actual predictive accuracy?), narrative_coherence (how coherent is the story?), base_rates_considered (bool), statistical_alternative (what would a statistical prediction say?), track_record (what is the actual prediction track record?), recommendation (confidence_justified/mild_overconfidence/significant_validity_illusion/major_narrative_driven/use_statistical_prediction)."""

ILLUSION_VALIDITY_PROMPT = """Detect illusion of validity:

Prediction: {prediction}
Confidence: {confidence}
Basis: {basis}
Track record: {track_record}
Domain: {domain}
Context: {context}

Is confidence driven by narrative coherence rather than actual predictive validity? Return ONLY valid JSON."""


class IllusionOfValidityService:
    """Detects illusion of validity — confidence from coherence, not accuracy."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        prediction: str,
        *,
        confidence: str = "",
        basis: str = "",
        track_record: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect illusion of validity."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=ILLUSION_VALIDITY_PROMPT.format(
                prediction=prediction,
                confidence=confidence or "Not specified",
                basis=basis or "Not specified",
                track_record=track_record or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=ILLUSION_VALIDITY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "prediction": prediction[:200],
            "illusion_of_validity_present": data.get("illusion_of_validity_present", False),
            "severity": data.get("severity", ""),
            "confidence_level": data.get("confidence_level", ""),
            "basis_of_confidence": data.get("basis_of_confidence", ""),
            "predictive_validity": data.get("predictive_validity", ""),
            "narrative_coherence": data.get("narrative_coherence", ""),
            "base_rates_considered": data.get("base_rates_considered", True),
            "statistical_alternative": data.get("statistical_alternative", ""),
            "track_record": data.get("track_record", ""),
            "recommendation": data.get("recommendation", ""),
        }
