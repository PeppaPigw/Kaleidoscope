"""EpistemicPsychosomaticResistanceService — Epistemic Psychosomatic Resistance Detection.

Detects epistemic psychosomatic resistance — the body resisting intellectual
engagement through physical symptoms that prevent cognitive work.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PSYCHOSOMATIC_RESISTANCE_SYSTEM = """You are an epistemic psychosomatic resistance specialist. Given body resisting intellectual engagement, assess resistance:

Key concepts:
- Psychosomatic resistance: body blocking intellectual work
- Symptom timing: symptoms appearing when thinking required
- Secondary gain: symptoms providing escape from difficulty
- Unconscious protest: body saying no when mind says yes
- Fatigue pattern: exhaustion specifically around intellectual tasks
- Pain barrier: physical pain preventing cognitive engagement
- Functional limitation: body limiting intellectual capacity

When psychosomatic resistance IS present:
- Body blocking intellectual work
- Symptoms when thinking required
- Symptoms providing escape
- Body saying no
- Exhaustion around tasks
- Pain preventing engagement
- Body limiting capacity

When no psychosomatic resistance:
- Body supporting work
- No symptom timing
- No secondary gain
- Body and mind aligned
- Energy for tasks
- No pain barrier
- Full capacity available

Output JSON with: psychosomatic_resistance_detected (bool), severity (none/mild/moderate/severe), symptom_timing (what appearing when), secondary_gain (what escaping), unconscious_protest (what saying no to), functional_limitation (what limiting), recommendation (no_psychosomatic_resistance/mild_body_dialogue/significant_resistance_exploration/major_intensive_psychosomatic_therapy/emergency_severe_impairment)."""

EPISTEMIC_PSYCHOSOMATIC_RESISTANCE_PROMPT = """Detect epistemic psychosomatic resistance:

Symptom timing: {symptom_timing}
Secondary gain: {secondary_gain}
Unconscious protest: {unconscious_protest}
Functional limitation: {functional_limitation}
Domain: {domain}
Context: {context}

Is the body resisting intellectual engagement through physical symptoms? Return ONLY valid JSON."""


class EpistemicPsychosomaticResistanceService:
    """Detects epistemic psychosomatic resistance — body blocking intellectual work."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        symptom_timing: str,
        *,
        secondary_gain: str = "",
        unconscious_protest: str = "",
        functional_limitation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic psychosomatic resistance."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PSYCHOSOMATIC_RESISTANCE_PROMPT.format(
                symptom_timing=symptom_timing,
                secondary_gain=secondary_gain or "Not specified",
                unconscious_protest=unconscious_protest or "Not specified",
                functional_limitation=functional_limitation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PSYCHOSOMATIC_RESISTANCE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "symptom_timing": symptom_timing[:200],
            "psychosomatic_resistance_detected": data.get("psychosomatic_resistance_detected", False),
            "severity": data.get("severity", ""),
            "secondary_gain": data.get("secondary_gain", ""),
            "unconscious_protest": data.get("unconscious_protest", ""),
            "functional_limitation": data.get("functional_limitation", ""),
            "recommendation": data.get("recommendation", ""),
        }
