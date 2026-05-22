"""EpistemicSomaticSymptomService — Epistemic Somatic Symptom Detection.

Detects epistemic somatic symptom disorder — intellectual distress
manifesting as perceived cognitive dysfunction with excessive concern.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SOMATIC_SYMPTOM_SYSTEM = """You are an epistemic somatic symptom specialist. Given intellectual distress manifesting as dysfunction, assess somatic patterns:

Key concepts:
- Epistemic somatic symptom: distress manifesting as cognitive dysfunction
- Disproportionate: concern exceeds actual impairment
- Excessive thoughts: consumed by worry about symptoms
- Excessive behavior: spending too much time on symptoms
- Genuine distress: suffering is real even if cause is psychological
- Amplification: attention to symptoms makes them worse
- Functional impact: symptoms limiting intellectual life

When epistemic somatic symptom IS present:
- Distress manifesting as dysfunction
- Concern exceeds impairment
- Consumed by symptom worry
- Too much time on symptoms
- Real suffering
- Attention worsening symptoms
- Symptoms limiting life

When no somatic symptom:
- Proportionate concern
- Concern matches impairment
- Not consumed by worry
- Appropriate attention
- No amplification
- Attention doesn't worsen
- No functional limitation

Output JSON with: somatic_symptom_detected (bool), severity (none/mild/moderate/severe), symptom_presentation (what dysfunction), disproportionality (what excess concern), thought_pattern (what consumed by), behavioral_pattern (what excessive action), recommendation (no_somatic_symptom/mild_psychoeducation/significant_cbt/major_intensive_therapy/emergency_severe_impairment)."""

EPISTEMIC_SOMATIC_SYMPTOM_PROMPT = """Detect epistemic somatic symptom:

Symptom presentation: {symptom_presentation}
Disproportionality: {disproportionality}
Thought pattern: {thought_pattern}
Behavioral pattern: {behavioral_pattern}
Domain: {domain}
Context: {context}

Is intellectual distress manifesting as perceived cognitive dysfunction with excessive concern? Return ONLY valid JSON."""


class EpistemicSomaticSymptomService:
    """Detects epistemic somatic symptom — distress as cognitive dysfunction."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        symptom_presentation: str,
        *,
        disproportionality: str = "",
        thought_pattern: str = "",
        behavioral_pattern: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic somatic symptom."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SOMATIC_SYMPTOM_PROMPT.format(
                symptom_presentation=symptom_presentation,
                disproportionality=disproportionality or "Not specified",
                thought_pattern=thought_pattern or "Not specified",
                behavioral_pattern=behavioral_pattern or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SOMATIC_SYMPTOM_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "symptom_presentation": symptom_presentation[:200],
            "somatic_symptom_detected": data.get("somatic_symptom_detected", False),
            "severity": data.get("severity", ""),
            "disproportionality": data.get("disproportionality", ""),
            "thought_pattern": data.get("thought_pattern", ""),
            "behavioral_pattern": data.get("behavioral_pattern", ""),
            "recommendation": data.get("recommendation", ""),
        }
