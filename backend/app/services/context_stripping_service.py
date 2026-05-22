"""ContextStrippingService — Context Stripping Detection.

Detects context stripping — removing context that changes the meaning
of claims, where decontextualization distorts understanding by
presenting claims without the conditions that give them meaning.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

CONTEXT_STRIPPING_SYSTEM = """You are a context stripping specialist. Given a claim presentation, assess whether essential context has been removed:

Key concepts:
- Context stripping: removing meaning-changing context
- Decontextualization: presenting claims without conditions
- Quote mining: selecting quotes without surrounding context
- Condition removal: removing conditions that bound claims
- Qualification stripping: removing qualifications
- Nuance erasure: removing nuance that changes meaning
- Selective presentation: presenting part as if it were whole

When context stripping IS present:
- Essential context removed from claims
- Meaning changed by decontextualization
- Quotes presented without surrounding context
- Conditions that bound claims removed
- Qualifications stripped from qualified claims
- Nuance erased changing the meaning
- Part presented as if it represented the whole

When summarization is appropriate:
- Core meaning preserved in summary
- Essential qualifications retained
- Context available if needed
- Summarization acknowledged
- Meaning not distorted by brevity
- Key conditions preserved
- Audience can access full context

Output JSON with: stripping_present (bool), severity (none/mild/moderate/severe), claim_presented (what is presented), context_removed (what context is missing), meaning_change (how meaning changes without context), original_meaning (what original meaning was), recommendation (appropriate_summarization/mild_context_loss/significant_context_stripping/major_meaning_distortion/preserve_essential_context)."""

CONTEXT_STRIPPING_PROMPT = """Detect context stripping:

Claim as presented: {claim}
Original context: {original}
Context removed: {removed}
Effect on meaning: {effect}
Domain: {domain}
Context: {context}

Has essential context been removed, changing the meaning? Return ONLY valid JSON."""


class ContextStrippingService:
    """Detects context stripping — removing meaning-changing context."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        claim: str,
        *,
        original: str = "",
        removed: str = "",
        effect: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect context stripping."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=CONTEXT_STRIPPING_PROMPT.format(
                claim=claim,
                original=original or "Not specified",
                removed=removed or "Not specified",
                effect=effect or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=CONTEXT_STRIPPING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "claim": claim[:200],
            "stripping_present": data.get("stripping_present", False),
            "severity": data.get("severity", ""),
            "context_removed": data.get("context_removed", ""),
            "meaning_change": data.get("meaning_change", ""),
            "original_meaning": data.get("original_meaning", ""),
            "recommendation": data.get("recommendation", ""),
        }
