"""EpistemicParkinsonService — Epistemic Parkinson's Detection.

Detects epistemic Parkinson's — progressive loss of intellectual dopamine
causing tremor, rigidity, and slowness of thought.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PARKINSON_SYSTEM = """You are an epistemic Parkinson's specialist. Given progressive intellectual dopamine loss, assess Parkinson's:

Key concepts:
- Epistemic Parkinson's: progressive dopamine loss
- Tremor: involuntary shaking at rest
- Rigidity: resistance to intellectual movement
- Bradykinesia: slowness of thought initiation
- Postural instability: balance problems
- Dopamine replacement: supplementing lost neurotransmitter
- Non-motor symptoms: sleep, mood, cognitive changes

When epistemic Parkinson's IS present:
- Progressive dopamine loss
- Involuntary shaking at rest
- Resistance to intellectual movement
- Slowness of thought initiation
- Balance problems present
- Neurotransmitter supplementation needed
- Sleep/mood/cognitive changes

When no Parkinson's:
- Normal dopamine levels
- No involuntary shaking
- Normal intellectual movement
- Normal thought initiation speed
- Good balance
- No supplementation needed
- Normal sleep/mood/cognition

Output JSON with: parkinson_detected (bool), severity (none/mild/moderate/severe), motor_symptoms (what tremor/rigidity/bradykinesia), non_motor_symptoms (what sleep/mood/cognitive), progression_stage (what Hoehn-Yahr equivalent), treatment_response (what dopamine response), recommendation (no_parkinson/mild_monitoring/significant_dopamine_agonist/major_levodopa/emergency_akinetic_crisis)."""

EPISTEMIC_PARKINSON_PROMPT = """Detect epistemic Parkinson's:

Motor symptoms: {motor_symptoms}
Non-motor symptoms: {non_motor_symptoms}
Progression stage: {progression_stage}
Treatment response: {treatment_response}
Domain: {domain}
Context: {context}

Is there progressive loss of intellectual dopamine causing tremor, rigidity, and slowness? Return ONLY valid JSON."""


class EpistemicParkinsonService:
    """Detects epistemic Parkinson's — progressive dopamine loss."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        motor_symptoms: str,
        *,
        non_motor_symptoms: str = "",
        progression_stage: str = "",
        treatment_response: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic Parkinson's."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PARKINSON_PROMPT.format(
                motor_symptoms=motor_symptoms,
                non_motor_symptoms=non_motor_symptoms or "Not specified",
                progression_stage=progression_stage or "Not specified",
                treatment_response=treatment_response or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PARKINSON_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "motor_symptoms": motor_symptoms[:200],
            "parkinson_detected": data.get("parkinson_detected", False),
            "severity": data.get("severity", ""),
            "non_motor_symptoms": data.get("non_motor_symptoms", ""),
            "progression_stage": data.get("progression_stage", ""),
            "treatment_response": data.get("treatment_response", ""),
            "recommendation": data.get("recommendation", ""),
        }
