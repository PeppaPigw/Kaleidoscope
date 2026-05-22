"""EpistemicDeliriumService — Epistemic Delirium Detection.

Detects epistemic delirium — acute confusion and disorientation in
intellectual systems, often triggered by illness or intervention.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_DELIRIUM_SYSTEM = """You are an epistemic delirium specialist. Given acute intellectual confusion, assess delirium:

Key concepts:
- Epistemic delirium: acute confusion and disorientation
- Fluctuating consciousness: awareness varying over time
- Inattention: inability to focus intellectual resources
- Disorganized thinking: incoherent intellectual processing
- Hyperactive: agitated confused state
- Hypoactive: withdrawn confused state
- Precipitating factor: what triggered the confusion

When epistemic delirium IS present:
- Acute confusion onset
- Awareness varying over time
- Cannot focus resources
- Incoherent processing
- Agitated confused state
- Withdrawn confused state
- Identifiable trigger present

When no delirium:
- Clear orientation
- Stable awareness
- Normal focus
- Coherent processing
- Calm and oriented
- Engaged and present
- No confusion triggers

Output JSON with: delirium_detected (bool), severity (none/mild/moderate/severe), consciousness_level (what awareness), attention_status (what focus), thinking_organization (what coherence), precipitating_factor (what trigger), recommendation (no_delirium/mild_subsyndromal/significant_delirium/major_severe_delirium/emergency_delirium_crisis)."""

EPISTEMIC_DELIRIUM_PROMPT = """Detect epistemic delirium:

Consciousness level: {consciousness_level}
Attention status: {attention_status}
Thinking organization: {thinking_organization}
Precipitating factor: {precipitating_factor}
Domain: {domain}
Context: {context}

Is there acute confusion and disorientation in the intellectual system? Return ONLY valid JSON."""


class EpistemicDeliriumService:
    """Detects epistemic delirium — acute confusion and disorientation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        consciousness_level: str,
        *,
        attention_status: str = "",
        thinking_organization: str = "",
        precipitating_factor: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic delirium."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_DELIRIUM_PROMPT.format(
                consciousness_level=consciousness_level,
                attention_status=attention_status or "Not specified",
                thinking_organization=thinking_organization or "Not specified",
                precipitating_factor=precipitating_factor or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_DELIRIUM_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "consciousness_level": consciousness_level[:200],
            "delirium_detected": data.get("delirium_detected", False),
            "severity": data.get("severity", ""),
            "attention_status": data.get("attention_status", ""),
            "thinking_organization": data.get("thinking_organization", ""),
            "precipitating_factor": data.get("precipitating_factor", ""),
            "recommendation": data.get("recommendation", ""),
        }
