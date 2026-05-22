"""EpistemicDigitalViralityBiasService — Epistemic Digital Virality Bias Detection.

Detects epistemic digital virality bias — viral content displacing accurate
content as shareability trumps accuracy.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_DIGITAL_VIRALITY_BIAS_SYSTEM = """You are an epistemic digital virality bias specialist. Given virality bias, assess accuracy displacement:

Key concepts:
- Epistemic virality bias: viral content displacing accurate content
- Shareability over accuracy: content optimized for sharing not truth
- Simplification for virality: complex truths simplified for shareability
- Emotional virality: emotional content spreading faster than factual
- Novelty virality: novel claims spreading faster than corrections
- Correction asymmetry: corrections never reaching original audience
- Viral misinformation persistence: misinformation persisting after correction

When epistemic virality bias IS present:
- Viral content displacing accurate
- Shareability over accuracy
- Simplification for virality
- Emotional content spreading faster
- Novel claims outpacing corrections
- Corrections not reaching audience
- Misinformation persisting

When no virality bias:
- Accurate content spreading
- Accuracy prioritized
- Complexity preserved
- Factual content valued
- Corrections reaching audience
- Misinformation corrected
- Truth competitive with falsehood

Output JSON with: virality_bias_detected (bool), severity (none/mild/moderate/severe), shareability_over_accuracy (what shareability over accuracy), simplification_for_virality (what simplified for virality), correction_asymmetry (what correction asymmetry), misinformation_persistence (what misinformation persisting), recommendation (no_virality_bias/mild_accuracy_checking/significant_viral_skepticism/major_intensive_source_verification/emergency_complete_virality_bias)."""

EPISTEMIC_DIGITAL_VIRALITY_BIAS_PROMPT = """Detect epistemic digital virality bias:

Shareability over accuracy: {shareability_over_accuracy}
Simplification for virality: {simplification_for_virality}
Correction asymmetry: {correction_asymmetry}
Misinformation persistence: {misinformation_persistence}
Domain: {domain}
Context: {context}

Is viral content displacing accurate content? Return ONLY valid JSON."""


class EpistemicDigitalViralityBiasService:
    """Detects epistemic virality bias — accuracy displaced by shareability."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        shareability_over_accuracy: str,
        *,
        simplification_for_virality: str = "",
        correction_asymmetry: str = "",
        misinformation_persistence: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic digital virality bias."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_DIGITAL_VIRALITY_BIAS_PROMPT.format(
                shareability_over_accuracy=shareability_over_accuracy,
                simplification_for_virality=simplification_for_virality or "Not specified",
                correction_asymmetry=correction_asymmetry or "Not specified",
                misinformation_persistence=misinformation_persistence or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_DIGITAL_VIRALITY_BIAS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "shareability_over_accuracy": shareability_over_accuracy[:200],
            "virality_bias_detected": data.get("virality_bias_detected", False),
            "severity": data.get("severity", ""),
            "simplification_for_virality": data.get("simplification_for_virality", ""),
            "correction_asymmetry": data.get("correction_asymmetry", ""),
            "misinformation_persistence": data.get("misinformation_persistence", ""),
            "recommendation": data.get("recommendation", ""),
        }
