"""CachedThinkingService — Cached Thinking Detection.

Detects cached thinking — using pre-formed conclusions without
re-evaluating them for the current context. Mental shortcuts
that were once derived through careful thought but are now
applied automatically without checking whether the original
reasoning still applies. The conclusion is remembered but the
derivation is forgotten.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

CACHED_THINKING_SYSTEM = """You are a cached thinking specialist. Given a conclusion or decision, assess whether it's being applied from cache without re-evaluation for current context:

Key concepts:
- Cached thinking: using stored conclusions without re-derivation
- Stale cache: conclusion was valid once but context has changed
- Context-free application: applying conclusion without checking fit
- Thought termination: cached answer prevents fresh thinking
- Intellectual laziness: using old conclusions to avoid new thinking
- Belief inertia: continuing to hold beliefs past their expiration
- Zombie arguments: arguments that persist after being refuted

When cached thinking IS problematic:
- Applying old conclusions to new situations without checking fit
- "I already thought about this" without re-examining changed context
- Using conclusions from different domains without adaptation
- Repeating positions without remembering the reasoning behind them
- "Everyone knows that..." for claims that need re-examination
- Applying rules of thumb beyond their valid range
- Using yesterday's answer for today's different question

When cached conclusions ARE appropriate:
- The context genuinely hasn't changed
- The original reasoning has been recently validated
- The conclusion is robust to context changes
- Re-derivation would reach the same conclusion
- The cache is acknowledged and periodically refreshed
- The domain is stable enough for cached answers

Output JSON with: cached_thinking_present (bool), severity (none/mild/moderate/severe), conclusion (what cached conclusion is being used), original_context (when/where was this conclusion formed), current_context (what is the current situation), context_change (how has context changed), derivation_remembered (is the original reasoning remembered), validity_check (has validity been checked for current context), recommendation (cache_valid/mild_staleness/significant_cached_thinking/major_stale_conclusion/re_derive_from_current_context)."""

CACHED_THINKING_PROMPT = """Detect cached thinking:

Conclusion: {conclusion}
Origin: {origin}
Current situation: {current}
Context change: {change}
Domain: {domain}
Context: {context}

Is a pre-formed conclusion being applied without re-evaluation for the current context? Return ONLY valid JSON."""


class CachedThinkingService:
    """Detects cached thinking — using stored conclusions without re-evaluation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        conclusion: str,
        *,
        origin: str = "",
        current: str = "",
        change: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect cached thinking."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=CACHED_THINKING_PROMPT.format(
                conclusion=conclusion,
                origin=origin or "Not specified",
                current=current or "Not specified",
                change=change or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=CACHED_THINKING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "conclusion": conclusion[:200],
            "cached_thinking_present": data.get("cached_thinking_present", False),
            "severity": data.get("severity", ""),
            "original_context": data.get("original_context", ""),
            "current_context": data.get("current_context", ""),
            "context_change": data.get("context_change", ""),
            "derivation_remembered": data.get("derivation_remembered", ""),
            "validity_check": data.get("validity_check", ""),
            "recommendation": data.get("recommendation", ""),
        }
