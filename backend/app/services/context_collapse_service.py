"""ContextCollapseService — Context Collapse Detection.

Detects context collapse — when communication designed for one
context is received in another, changing its meaning, or when
multiple audiences with different norms receive the same message.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

CONTEXT_COLLAPSE_SYSTEM = """You are a context collapse specialist. Given a communication situation, assess whether context collapse is affecting meaning:

Key concepts:
- Context collapse: multiple contexts receiving same message
- Audience mismatch: message designed for one audience, received by another
- Decontextualization: meaning changed by removing context
- Platform flattening: social media collapsing distinct audiences
- Register mismatch: formal/informal confusion across contexts
- Norm conflict: different contexts have different norms
- Recontextualization: meaning transformed in new context

When context collapse IS present:
- Message designed for one context received in another
- Multiple audiences with different norms see same message
- Meaning changes when context is removed or changed
- Communication norms from one context applied in another
- Decontextualized message misinterpreted
- Platform collapses distinct social contexts
- Register inappropriate for receiving context

When context awareness is appropriate:
- Communication designed for its actual audience
- Context explicitly provided with message
- Multiple audiences acknowledged in design
- Norms of receiving context respected
- Decontextualization risk managed
- Register appropriate for context
- Meaning stable across likely contexts

Output JSON with: collapse_present (bool), severity (none/mild/moderate/severe), communication (what is communicated), intended_context (original context), received_context (receiving context), meaning_shift (how meaning changes), recommendation (appropriate_context_management/mild_context_mismatch/significant_context_collapse/major_decontextualization/provide_context)."""

CONTEXT_COLLAPSE_PROMPT = """Detect context collapse:

Communication: {communication}
Intended context: {intended}
Received context: {received}
Meaning shift: {shift}
Domain: {domain}
Context: {context}

Is communication being received in a different context than intended, changing its meaning? Return ONLY valid JSON."""


class ContextCollapseService:
    """Detects context collapse — meaning changed by context mismatch."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        communication: str,
        *,
        intended: str = "",
        received: str = "",
        shift: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect context collapse."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=CONTEXT_COLLAPSE_PROMPT.format(
                communication=communication,
                intended=intended or "Not specified",
                received=received or "Not specified",
                shift=shift or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=CONTEXT_COLLAPSE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "communication": communication[:200],
            "collapse_present": data.get("collapse_present", False),
            "severity": data.get("severity", ""),
            "intended_context": data.get("intended_context", ""),
            "received_context": data.get("received_context", ""),
            "meaning_shift": data.get("meaning_shift", ""),
            "recommendation": data.get("recommendation", ""),
        }
