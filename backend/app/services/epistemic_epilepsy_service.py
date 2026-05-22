"""EpistemicEpilepsyService — Epistemic Epilepsy Detection.

Detects epistemic epilepsy — recurrent seizures of uncontrolled intellectual
electrical activity disrupting normal function.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_EPILEPSY_SYSTEM = """You are an epistemic epilepsy specialist. Given recurrent intellectual seizures, assess epilepsy:

Key concepts:
- Epistemic epilepsy: recurrent uncontrolled electrical activity
- Seizure: sudden burst of uncontrolled intellectual activity
- Focal: originating from one intellectual area
- Generalized: affecting entire intellectual system
- Postictal: confusion/exhaustion after seizure
- Anticonvulsant: medication preventing seizures
- Seizure threshold: how easily seizures are triggered

When epistemic epilepsy IS present:
- Recurrent uncontrolled activity bursts
- Sudden intellectual disruption
- Originating from specific area or generalized
- Affecting entire system
- Post-event confusion/exhaustion
- Prevention medication needed
- Low seizure threshold

When no epilepsy:
- No uncontrolled activity bursts
- No sudden disruption
- No focal or generalized events
- System functioning normally
- No post-event confusion
- No prevention needed
- Normal threshold

Output JSON with: epilepsy_detected (bool), severity (none/mild/moderate/severe), seizure_type (what activity pattern), frequency (what recurrence), threshold_status (what trigger sensitivity), postictal_impact (what recovery), recommendation (no_epilepsy/mild_monitoring/significant_monotherapy/major_polytherapy/emergency_status_epilepticus)."""

EPISTEMIC_EPILEPSY_PROMPT = """Detect epistemic epilepsy:

Seizure type: {seizure_type}
Frequency: {frequency}
Threshold status: {threshold_status}
Postictal impact: {postictal_impact}
Domain: {domain}
Context: {context}

Are there recurrent seizures of uncontrolled intellectual electrical activity? Return ONLY valid JSON."""


class EpistemicEpilepsyService:
    """Detects epistemic epilepsy — recurrent uncontrolled intellectual activity."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        seizure_type: str,
        *,
        frequency: str = "",
        threshold_status: str = "",
        postictal_impact: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic epilepsy."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_EPILEPSY_PROMPT.format(
                seizure_type=seizure_type,
                frequency=frequency or "Not specified",
                threshold_status=threshold_status or "Not specified",
                postictal_impact=postictal_impact or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_EPILEPSY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "seizure_type": seizure_type[:200],
            "epilepsy_detected": data.get("epilepsy_detected", False),
            "severity": data.get("severity", ""),
            "frequency": data.get("frequency", ""),
            "threshold_status": data.get("threshold_status", ""),
            "postictal_impact": data.get("postictal_impact", ""),
            "recommendation": data.get("recommendation", ""),
        }
