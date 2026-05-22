"""EpistemicDissociationService — Epistemic Dissociation Detection.

Detects epistemic dissociation — disconnection from intellectual experience
as if observing from outside, detachment from own thinking.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_DISSOCIATION_SYSTEM = """You are an epistemic dissociation specialist. Given intellectual disconnection, assess dissociation:

Key concepts:
- Epistemic dissociation: disconnection from intellectual experience
- Depersonalization: feeling detached from own thinking
- Derealization: intellectual world feeling unreal
- Amnesia: gaps in intellectual memory
- Identity fragmentation: multiple intellectual selves
- Grounding: techniques to reconnect with experience
- Trauma response: dissociation as protective mechanism

When epistemic dissociation IS present:
- Disconnection from intellectual experience
- Feeling detached from own thinking
- Intellectual world feeling unreal
- Gaps in intellectual memory
- Multiple intellectual selves present
- Grounding techniques needed
- Protective mechanism active

When no dissociation:
- Connected to intellectual experience
- Ownership of own thinking
- Intellectual world feels real
- Continuous intellectual memory
- Unified intellectual self
- No grounding needed
- No protective disconnection

Output JSON with: dissociation_detected (bool), severity (none/mild/moderate/severe), disconnection_type (what detachment), trigger_context (what activates), duration_pattern (what episodes), grounding_effectiveness (what reconnection), recommendation (no_dissociation/mild_grounding/significant_trauma_therapy/major_intensive_integration/emergency_identity_crisis)."""

EPISTEMIC_DISSOCIATION_PROMPT = """Detect epistemic dissociation:

Disconnection type: {disconnection_type}
Trigger context: {trigger_context}
Duration pattern: {duration_pattern}
Grounding effectiveness: {grounding_effectiveness}
Domain: {domain}
Context: {context}

Is there disconnection from intellectual experience as if observing from outside? Return ONLY valid JSON."""


class EpistemicDissociationService:
    """Detects epistemic dissociation — disconnection from intellectual experience."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        disconnection_type: str,
        *,
        trigger_context: str = "",
        duration_pattern: str = "",
        grounding_effectiveness: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic dissociation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_DISSOCIATION_PROMPT.format(
                disconnection_type=disconnection_type,
                trigger_context=trigger_context or "Not specified",
                duration_pattern=duration_pattern or "Not specified",
                grounding_effectiveness=grounding_effectiveness or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_DISSOCIATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "disconnection_type": disconnection_type[:200],
            "dissociation_detected": data.get("dissociation_detected", False),
            "severity": data.get("severity", ""),
            "trigger_context": data.get("trigger_context", ""),
            "duration_pattern": data.get("duration_pattern", ""),
            "grounding_effectiveness": data.get("grounding_effectiveness", ""),
            "recommendation": data.get("recommendation", ""),
        }
