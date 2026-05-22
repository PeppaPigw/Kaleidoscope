"""EpistemicEmbodiedCognitionFailureService — Epistemic Embodied Cognition Failure Detection.

Detects epistemic embodied cognition failure — disconnection between bodily
knowing and intellectual knowing, where felt sense is ignored or overridden.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_EMBODIED_COGNITION_FAILURE_SYSTEM = """You are an epistemic embodied cognition failure specialist. Given disconnection between body and mind knowing, assess failure:

Key concepts:
- Embodied cognition failure: body knowing disconnected from mind
- Felt sense ignored: gut feelings overridden by intellect
- Disembodied thinking: pure abstraction without bodily grounding
- Intuition suppression: silencing non-verbal knowing
- Head-body split: thinking divorced from feeling
- Somatic wisdom lost: body's intelligence not accessed
- Over-intellectualization: everything processed only cognitively

When embodied cognition failure IS present:
- Body knowing disconnected
- Gut feelings overridden
- Pure abstraction without grounding
- Non-verbal knowing silenced
- Thinking divorced from feeling
- Body intelligence not accessed
- Everything only cognitive

When no embodied cognition failure:
- Body and mind integrated
- Gut feelings honored
- Grounded abstraction
- Intuition valued
- Thinking and feeling connected
- Body intelligence accessed
- Multi-channel processing

Output JSON with: embodied_cognition_failure_detected (bool), severity (none/mild/moderate/severe), felt_sense_ignored (what overriding), disembodied_pattern (what ungrounded), intuition_suppression (what silencing), head_body_split (what divorced), recommendation (no_embodied_failure/mild_body_reconnection/significant_somatic_integration/major_intensive_embodiment_work/emergency_severe_disconnection)."""

EPISTEMIC_EMBODIED_COGNITION_FAILURE_PROMPT = """Detect epistemic embodied cognition failure:

Felt sense ignored: {felt_sense_ignored}
Disembodied pattern: {disembodied_pattern}
Intuition suppression: {intuition_suppression}
Head body split: {head_body_split}
Domain: {domain}
Context: {context}

Is there disconnection between bodily knowing and intellectual knowing? Return ONLY valid JSON."""


class EpistemicEmbodiedCognitionFailureService:
    """Detects epistemic embodied cognition failure — body-mind disconnection."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        felt_sense_ignored: str,
        *,
        disembodied_pattern: str = "",
        intuition_suppression: str = "",
        head_body_split: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic embodied cognition failure."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_EMBODIED_COGNITION_FAILURE_PROMPT.format(
                felt_sense_ignored=felt_sense_ignored,
                disembodied_pattern=disembodied_pattern or "Not specified",
                intuition_suppression=intuition_suppression or "Not specified",
                head_body_split=head_body_split or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_EMBODIED_COGNITION_FAILURE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "felt_sense_ignored": felt_sense_ignored[:200],
            "embodied_cognition_failure_detected": data.get("embodied_cognition_failure_detected", False),
            "severity": data.get("severity", ""),
            "disembodied_pattern": data.get("disembodied_pattern", ""),
            "intuition_suppression": data.get("intuition_suppression", ""),
            "head_body_split": data.get("head_body_split", ""),
            "recommendation": data.get("recommendation", ""),
        }
