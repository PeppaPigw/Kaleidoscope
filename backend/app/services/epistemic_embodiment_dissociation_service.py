"""EpistemicEmbodimentDissociationService — Epistemic Embodiment Dissociation Detection.

Detects epistemic embodiment dissociation — dissociating from body during
epistemic activity, losing grounding and embodied perspective.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_EMBODIMENT_DISSOCIATION_SYSTEM = """You are an epistemic embodiment dissociation specialist. Given dissociating from body during epistemic activity, assess embodiment dissociation:

Key concepts:
- Epistemic embodiment dissociation: dissociating from body during epistemic activity
- Disembodied thinking: thinking as if without a body
- Floating intellect: intellect floating free of bodily grounding
- Physical disconnection: disconnected from physical experience
- Abstract escape: escaping into abstraction away from body
- Groundlessness: losing grounding in physical reality
- Depersonalized knowing: knowing without personal embodied presence

When epistemic embodiment dissociation IS present:
- Dissociated from body during thinking
- Thinking disembodied
- Intellect floating free
- Physically disconnected
- Escaped into abstraction
- Groundless
- Knowing depersonalized

When no embodiment dissociation:
- Present in body during thinking
- Thinking embodied
- Intellect grounded
- Physically connected
- Abstraction grounded
- Grounded
- Knowing personally embodied

Output JSON with: embodiment_dissociation_detected (bool), severity (none/mild/moderate/severe), disembodied_thinking (what thinking disembodied about), floating_intellect (what intellect floating about), physical_disconnection (what disconnected from), abstract_escape (what escaping into abstraction from), recommendation (no_embodiment_dissociation/mild_grounding_practice/significant_embodiment_recovery/major_intensive_reconnection/emergency_complete_embodiment_dissociation)."""

EPISTEMIC_EMBODIMENT_DISSOCIATION_PROMPT = """Detect epistemic embodiment dissociation:

Disembodied thinking: {disembodied_thinking}
Floating intellect: {floating_intellect}
Physical disconnection: {physical_disconnection}
Abstract escape: {abstract_escape}
Domain: {domain}
Context: {context}

Is there dissociation from body during epistemic activity? Return ONLY valid JSON."""


class EpistemicEmbodimentDissociationService:
    """Detects epistemic embodiment dissociation — dissociating from body."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        disembodied_thinking: str,
        *,
        floating_intellect: str = "",
        physical_disconnection: str = "",
        abstract_escape: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic embodiment dissociation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_EMBODIMENT_DISSOCIATION_PROMPT.format(
                disembodied_thinking=disembodied_thinking,
                floating_intellect=floating_intellect or "Not specified",
                physical_disconnection=physical_disconnection or "Not specified",
                abstract_escape=abstract_escape or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_EMBODIMENT_DISSOCIATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "disembodied_thinking": disembodied_thinking[:200],
            "embodiment_dissociation_detected": data.get("embodiment_dissociation_detected", False),
            "severity": data.get("severity", ""),
            "floating_intellect": data.get("floating_intellect", ""),
            "physical_disconnection": data.get("physical_disconnection", ""),
            "abstract_escape": data.get("abstract_escape", ""),
            "recommendation": data.get("recommendation", ""),
        }
