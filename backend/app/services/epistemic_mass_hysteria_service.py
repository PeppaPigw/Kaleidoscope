"""EpistemicMassHysteriaService — Epistemic Mass Hysteria Detection.

Detects epistemic mass hysteria — rapid spread of irrational intellectual
beliefs through a group driven by anxiety and social contagion.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_MASS_HYSTERIA_SYSTEM = """You are an epistemic mass hysteria specialist. Given rapid irrational belief spread, assess mass hysteria:

Key concepts:
- Epistemic mass hysteria: rapid spread of irrational beliefs
- Social contagion: beliefs spreading through emotional transmission
- Anxiety amplification: fear feeding more fear in group
- Reality distortion: group collectively misperceiving
- Conversion symptoms: stress manifesting as intellectual symptoms
- Trigger event: specific incident sparking cascade
- Self-reinforcing: each believer validates others

When epistemic mass hysteria IS present:
- Rapid irrational spread
- Emotional transmission
- Fear feeding fear
- Collective misperception
- Stress as symptoms
- Specific trigger
- Self-reinforcing belief

When no mass hysteria:
- Rational belief spread
- Evidence-based transmission
- Proportionate concern
- Accurate perception
- Appropriate response
- No trigger cascade
- Independent verification

Output JSON with: mass_hysteria_detected (bool), severity (none/mild/moderate/severe), contagion_pattern (what spreading), anxiety_amplification (what feeding), reality_distortion (what misperceiving), trigger_event (what sparked), recommendation (no_mass_hysteria/mild_reality_grounding/significant_group_intervention/major_intensive_deprogramming/emergency_complete_contagion)."""

EPISTEMIC_MASS_HYSTERIA_PROMPT = """Detect epistemic mass hysteria:

Contagion pattern: {contagion_pattern}
Anxiety amplification: {anxiety_amplification}
Reality distortion: {reality_distortion}
Trigger event: {trigger_event}
Domain: {domain}
Context: {context}

Is there rapid spread of irrational intellectual beliefs through social contagion? Return ONLY valid JSON."""


class EpistemicMassHysteriaService:
    """Detects epistemic mass hysteria — rapid irrational belief spread."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        contagion_pattern: str,
        *,
        anxiety_amplification: str = "",
        reality_distortion: str = "",
        trigger_event: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic mass hysteria."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_MASS_HYSTERIA_PROMPT.format(
                contagion_pattern=contagion_pattern,
                anxiety_amplification=anxiety_amplification or "Not specified",
                reality_distortion=reality_distortion or "Not specified",
                trigger_event=trigger_event or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_MASS_HYSTERIA_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "contagion_pattern": contagion_pattern[:200],
            "mass_hysteria_detected": data.get("mass_hysteria_detected", False),
            "severity": data.get("severity", ""),
            "anxiety_amplification": data.get("anxiety_amplification", ""),
            "reality_distortion": data.get("reality_distortion", ""),
            "trigger_event": data.get("trigger_event", ""),
            "recommendation": data.get("recommendation", ""),
        }
