"""EpistemicNeuropathyService — Epistemic Neuropathy Detection.

Detects epistemic neuropathy — damage to peripheral intellectual nerves
causing numbness, tingling, and loss of sensation in intellectual extremities.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_NEUROPATHY_SYSTEM = """You are an epistemic neuropathy specialist. Given peripheral intellectual nerve damage, assess neuropathy:

Key concepts:
- Epistemic neuropathy: peripheral nerve damage
- Numbness: loss of intellectual sensation
- Tingling: abnormal sensation (paresthesia)
- Stocking-glove: distal-to-proximal progression
- Axonal: nerve fiber damage
- Demyelinating: nerve sheath damage
- Neuropathic pain: pain from nerve damage itself

When epistemic neuropathy IS present:
- Peripheral nerve damage present
- Loss of intellectual sensation
- Abnormal sensations occurring
- Distal-to-proximal progression
- Nerve fiber damage
- Nerve sheath damage
- Pain from nerve damage itself

When no neuropathy:
- No peripheral nerve damage
- Full sensation intact
- Normal sensations only
- No progression pattern
- Nerve fibers healthy
- Nerve sheaths intact
- No neuropathic pain

Output JSON with: neuropathy_detected (bool), severity (none/mild/moderate/severe), distribution_pattern (what areas affected), sensation_loss (what numbness), nerve_type (what axonal/demyelinating), pain_component (what neuropathic pain), recommendation (no_neuropathy/mild_monitoring/significant_neuroprotective/major_pain_management/emergency_acute_motor_loss)."""

EPISTEMIC_NEUROPATHY_PROMPT = """Detect epistemic neuropathy:

Distribution pattern: {distribution_pattern}
Sensation loss: {sensation_loss}
Nerve type: {nerve_type}
Pain component: {pain_component}
Domain: {domain}
Context: {context}

Is there damage to peripheral intellectual nerves causing numbness and loss of sensation? Return ONLY valid JSON."""


class EpistemicNeuropathyService:
    """Detects epistemic neuropathy — peripheral intellectual nerve damage."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        distribution_pattern: str,
        *,
        sensation_loss: str = "",
        nerve_type: str = "",
        pain_component: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic neuropathy."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_NEUROPATHY_PROMPT.format(
                distribution_pattern=distribution_pattern,
                sensation_loss=sensation_loss or "Not specified",
                nerve_type=nerve_type or "Not specified",
                pain_component=pain_component or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_NEUROPATHY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "distribution_pattern": distribution_pattern[:200],
            "neuropathy_detected": data.get("neuropathy_detected", False),
            "severity": data.get("severity", ""),
            "sensation_loss": data.get("sensation_loss", ""),
            "nerve_type": data.get("nerve_type", ""),
            "pain_component": data.get("pain_component", ""),
            "recommendation": data.get("recommendation", ""),
        }
