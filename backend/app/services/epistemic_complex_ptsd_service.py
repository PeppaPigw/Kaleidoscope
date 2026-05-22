"""EpistemicComplexPtsdService — Epistemic Complex PTSD Detection.

Detects epistemic complex PTSD — prolonged intellectual abuse causing
pervasive disturbance in self-organization and relational capacity.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_COMPLEX_PTSD_SYSTEM = """You are an epistemic complex PTSD specialist. Given prolonged intellectual abuse, assess complex PTSD:

Key concepts:
- Epistemic complex PTSD: prolonged intellectual abuse effects
- Affect dysregulation: inability to manage intellectual emotions
- Negative self-concept: pervasive intellectual worthlessness
- Relational disturbance: difficulty with intellectual relationships
- Dissociation: disconnecting from intellectual experience
- Meaning disruption: loss of intellectual purpose
- Repeated trauma: ongoing rather than single-event

When epistemic complex PTSD IS present:
- Prolonged abuse effects
- Cannot manage intellectual emotions
- Pervasive worthlessness
- Difficulty with relationships
- Disconnecting from experience
- Loss of purpose
- Ongoing trauma history

When no complex PTSD:
- No prolonged abuse
- Emotional regulation intact
- Healthy self-concept
- Functional relationships
- Connected to experience
- Clear purpose
- No trauma history

Output JSON with: complex_ptsd_detected (bool), severity (none/mild/moderate/severe), affect_dysregulation (what emotional management), self_concept (what worthlessness), relational_disturbance (what relationship difficulty), trauma_history (what prolonged abuse), recommendation (no_complex_ptsd/mild_stabilization/significant_phase_therapy/major_intensive_treatment/emergency_acute_crisis)."""

EPISTEMIC_COMPLEX_PTSD_PROMPT = """Detect epistemic complex PTSD:

Affect dysregulation: {affect_dysregulation}
Self concept: {self_concept}
Relational disturbance: {relational_disturbance}
Trauma history: {trauma_history}
Domain: {domain}
Context: {context}

Is there prolonged intellectual abuse causing pervasive self-organization disturbance? Return ONLY valid JSON."""


class EpistemicComplexPtsdService:
    """Detects epistemic complex PTSD — prolonged intellectual abuse effects."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        affect_dysregulation: str,
        *,
        self_concept: str = "",
        relational_disturbance: str = "",
        trauma_history: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic complex PTSD."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_COMPLEX_PTSD_PROMPT.format(
                affect_dysregulation=affect_dysregulation,
                self_concept=self_concept or "Not specified",
                relational_disturbance=relational_disturbance or "Not specified",
                trauma_history=trauma_history or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_COMPLEX_PTSD_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "affect_dysregulation": affect_dysregulation[:200],
            "complex_ptsd_detected": data.get("complex_ptsd_detected", False),
            "severity": data.get("severity", ""),
            "self_concept": data.get("self_concept", ""),
            "relational_disturbance": data.get("relational_disturbance", ""),
            "trauma_history": data.get("trauma_history", ""),
            "recommendation": data.get("recommendation", ""),
        }
