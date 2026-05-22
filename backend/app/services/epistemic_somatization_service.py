"""EpistemicSomatizationService — Epistemic Somatization Detection.

Detects epistemic somatization — converting intellectual distress into
physical or somatic symptoms rather than processing cognitively.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SOMATIZATION_SYSTEM = """You are an epistemic somatization specialist. Given conversion of intellectual distress to physical symptoms, assess somatization:

Key concepts:
- Epistemic somatization: intellectual distress becoming physical
- Body expression: what mind can't process, body expresses
- Symptom language: physical symptoms communicating intellectual pain
- Cognitive avoidance: body taking over to avoid thinking
- Stress conversion: intellectual pressure becoming bodily tension
- Psychosomatic loop: mind-body feedback amplifying distress
- Symbolic expression: symptoms symbolizing intellectual conflict

When epistemic somatization IS present:
- Intellectual distress becoming physical
- Body expressing what mind can't
- Physical symptoms communicating
- Body taking over to avoid thinking
- Pressure becoming tension
- Mind-body feedback loop
- Symptoms symbolizing conflict

When no somatization:
- Distress processed cognitively
- Mind handling its own material
- Direct communication
- Thinking through difficulty
- Appropriate stress response
- Regulated mind-body
- Direct expression

Output JSON with: somatization_detected (bool), severity (none/mild/moderate/severe), body_expression (what body expressing), symptom_language (what communicating), cognitive_avoidance (what avoiding thinking), stress_conversion (what becoming physical), recommendation (no_somatization/mild_body_awareness/significant_somatic_therapy/major_intensive_psychosomatic_work/emergency_severe_conversion)."""

EPISTEMIC_SOMATIZATION_PROMPT = """Detect epistemic somatization:

Body expression: {body_expression}
Symptom language: {symptom_language}
Cognitive avoidance: {cognitive_avoidance}
Stress conversion: {stress_conversion}
Domain: {domain}
Context: {context}

Is intellectual distress being converted into physical symptoms? Return ONLY valid JSON."""


class EpistemicSomatizationService:
    """Detects epistemic somatization — intellectual distress becoming physical."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        body_expression: str,
        *,
        symptom_language: str = "",
        cognitive_avoidance: str = "",
        stress_conversion: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic somatization."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SOMATIZATION_PROMPT.format(
                body_expression=body_expression,
                symptom_language=symptom_language or "Not specified",
                cognitive_avoidance=cognitive_avoidance or "Not specified",
                stress_conversion=stress_conversion or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SOMATIZATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "body_expression": body_expression[:200],
            "somatization_detected": data.get("somatization_detected", False),
            "severity": data.get("severity", ""),
            "symptom_language": data.get("symptom_language", ""),
            "cognitive_avoidance": data.get("cognitive_avoidance", ""),
            "stress_conversion": data.get("stress_conversion", ""),
            "recommendation": data.get("recommendation", ""),
        }
