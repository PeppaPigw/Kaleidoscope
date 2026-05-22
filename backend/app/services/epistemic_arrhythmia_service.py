"""EpistemicArrhythmiaService — Epistemic Arrhythmia Detection.

Detects epistemic arrhythmia — irregular rhythm of idea flow where
intellectual output becomes unpredictable, too fast, or too slow.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ARRHYTHMIA_SYSTEM = """You are an epistemic arrhythmia specialist. Given an intellectual rhythm, assess whether idea flow has become irregular:

Key concepts:
- Epistemic arrhythmia: irregular rhythm of idea flow
- Tachycardia: abnormally fast intellectual output
- Bradycardia: abnormally slow intellectual output
- Fibrillation: chaotic uncoordinated rapid activity
- Heart block: signal not conducting through levels
- Ectopic beat: premature or misplaced intellectual output
- Pacemaker failure: loss of natural rhythm generator

When epistemic arrhythmia IS present:
- Irregular rhythm of idea flow
- Abnormally fast intellectual output without quality
- Abnormally slow intellectual output despite need
- Chaotic uncoordinated rapid activity
- Signals not conducting through organizational levels
- Premature or misplaced intellectual outputs
- Loss of natural rhythm generation

When healthy rhythm is present:
- Regular predictable idea flow
- Appropriate speed of output
- Responsive to demand
- Coordinated activity
- Smooth signal conduction
- Well-timed outputs
- Strong natural rhythm

Output JSON with: arrhythmia_present (bool), severity (none/mild/moderate/severe), tachycardia (what abnormal speed), bradycardia (what abnormal slowness), fibrillation (what chaotic activity), heart_block (what conduction failure), recommendation (healthy_rhythm/mild_arrhythmia/significant_arrhythmia/major_rhythm_disorder/restore_regular_rhythm)."""

EPISTEMIC_ARRHYTHMIA_PROMPT = """Detect epistemic arrhythmia:

Tachycardia: {tachycardia}
Bradycardia: {bradycardia}
Fibrillation: {fibrillation}
Heart block: {heart_block}
Domain: {domain}
Context: {context}

Has the rhythm of idea flow become irregular, too fast, too slow, or chaotic? Return ONLY valid JSON."""


class EpistemicArrhythmiaService:
    """Detects epistemic arrhythmia — irregular rhythm of idea flow."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        tachycardia: str,
        *,
        bradycardia: str = "",
        fibrillation: str = "",
        heart_block: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic arrhythmia."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ARRHYTHMIA_PROMPT.format(
                tachycardia=tachycardia,
                bradycardia=bradycardia or "Not specified",
                fibrillation=fibrillation or "Not specified",
                heart_block=heart_block or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ARRHYTHMIA_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "tachycardia": tachycardia[:200],
            "arrhythmia_present": data.get("arrhythmia_present", False),
            "severity": data.get("severity", ""),
            "bradycardia": data.get("bradycardia", ""),
            "fibrillation": data.get("fibrillation", ""),
            "heart_block": data.get("heart_block", ""),
            "recommendation": data.get("recommendation", ""),
        }
