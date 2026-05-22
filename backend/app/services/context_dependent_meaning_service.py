"""ContextDependentMeaningService — Context Dependent Meaning Detection.

Detects context dependent meaning errors — meaning that changes with
context being treated as context-independent, where situated claims
are treated as universal.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

CONTEXT_DEPENDENT_MEANING_SYSTEM = """You are a context dependent meaning specialist. Given a claim being applied across contexts, assess whether context-dependent meaning is being treated as universal:

Key concepts:
- Context dependent meaning: meaning changes with context
- Decontextualization error: removing context changes meaning
- Universal treatment: situated claims treated as universal
- Context sensitivity ignored: meaning varies but treated as fixed
- Indexical blindness: context-pointing terms treated as absolute
- Situatedness denial: all meaning treated as context-free
- Portability assumption: meaning assumed to travel across contexts

When context dependent meaning error IS present:
- Context-dependent claim treated as context-independent
- Meaning that varies with context treated as fixed
- Situated claims applied universally without justification
- Context sensitivity of terms ignored
- Claims moved between contexts without adjustment
- Meaning assumed to be portable across situations
- Context-specific truth treated as universal truth

When context independence is appropriate:
- Claim genuinely context-independent
- Meaning stable across relevant contexts
- Universal application justified by evidence
- Context sensitivity acknowledged and managed
- Claims appropriately bounded to valid contexts
- Portability of meaning verified not assumed
- Context-specific and universal claims distinguished

Output JSON with: context_error_present (bool), severity (none/mild/moderate/severe), claim (what claim is made), original_context (where meaning originated), applied_context (where it's being applied), meaning_shift (how meaning changes), recommendation (appropriate_universality/mild_context_sensitivity/significant_context_dependent_meaning/major_decontextualization_error/bound_claims_to_valid_contexts)."""

CONTEXT_DEPENDENT_MEANING_PROMPT = """Detect context dependent meaning error:

Claim: {claim}
Original context: {original}
Applied context: {applied}
Meaning variation: {variation}
Domain: {domain}
Context: {context}

Is context-dependent meaning being treated as context-independent? Return ONLY valid JSON."""


class ContextDependentMeaningService:
    """Detects context dependent meaning errors — situated claims treated as universal."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        claim: str,
        *,
        original: str = "",
        applied: str = "",
        variation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect context dependent meaning error."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=CONTEXT_DEPENDENT_MEANING_PROMPT.format(
                claim=claim,
                original=original or "Not specified",
                applied=applied or "Not specified",
                variation=variation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=CONTEXT_DEPENDENT_MEANING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "claim": claim[:200],
            "context_error_present": data.get("context_error_present", False),
            "severity": data.get("severity", ""),
            "original_context": data.get("original_context", ""),
            "applied_context": data.get("applied_context", ""),
            "meaning_shift": data.get("meaning_shift", ""),
            "recommendation": data.get("recommendation", ""),
        }
