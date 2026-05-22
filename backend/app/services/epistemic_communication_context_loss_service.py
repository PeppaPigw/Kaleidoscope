"""EpistemicCommunicationContextLossService — Epistemic Communication Context Loss Detection.

Detects epistemic communication context loss — losing crucial context
as information passes through communication chains.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_COMMUNICATION_CONTEXT_LOSS_SYSTEM = """You are an epistemic communication context loss specialist. Given context lost in communication, assess context loss:

Key concepts:
- Epistemic communication context loss: crucial context lost in transmission
- Scope context loss: losing scope limitations of original claim
- Temporal context loss: losing temporal context (when claim was made)
- Methodological context loss: losing methodological context (how finding was produced)
- Population context loss: losing population context (who was studied)
- Conditional context loss: losing conditions under which claim holds
- Motivation context loss: losing why claim was made (purpose/audience)

When epistemic communication context loss IS present:
- Crucial context lost
- Scope limitations lost
- Temporal context lost
- Methodological context lost
- Population context lost
- Conditions lost
- Motivation lost

When no context loss:
- Context preserved
- Scope maintained
- Temporal context kept
- Methodology noted
- Population specified
- Conditions stated
- Motivation clear

Output JSON with: context_loss_detected (bool), severity (none/mild/moderate/severe), scope_context_loss (what scope lost), temporal_context_loss (what temporal context lost), methodological_context_loss (what methodology lost), conditional_context_loss (what conditions lost), recommendation (no_context_loss/mild_context_preservation/significant_context_recovery/major_intensive_context_reconstruction/emergency_complete_context_loss)."""

EPISTEMIC_COMMUNICATION_CONTEXT_LOSS_PROMPT = """Detect epistemic communication context loss:

Scope context loss: {scope_context_loss}
Temporal context loss: {temporal_context_loss}
Methodological context loss: {methodological_context_loss}
Conditional context loss: {conditional_context_loss}
Domain: {domain}
Context: {context}

Is crucial context being lost as information passes through communication? Return ONLY valid JSON."""


class EpistemicCommunicationContextLossService:
    """Detects epistemic communication context loss — context stripped."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        scope_context_loss: str,
        *,
        temporal_context_loss: str = "",
        methodological_context_loss: str = "",
        conditional_context_loss: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic communication context loss."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_COMMUNICATION_CONTEXT_LOSS_PROMPT.format(
                scope_context_loss=scope_context_loss,
                temporal_context_loss=temporal_context_loss or "Not specified",
                methodological_context_loss=methodological_context_loss or "Not specified",
                conditional_context_loss=conditional_context_loss or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_COMMUNICATION_CONTEXT_LOSS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "scope_context_loss": scope_context_loss[:200],
            "context_loss_detected": data.get("context_loss_detected", False),
            "severity": data.get("severity", ""),
            "temporal_context_loss": data.get("temporal_context_loss", ""),
            "methodological_context_loss": data.get("methodological_context_loss", ""),
            "conditional_context_loss": data.get("conditional_context_loss", ""),
            "recommendation": data.get("recommendation", ""),
        }
