"""FailureAmnesiaService — Failure Amnesia Detection.

Detects failure amnesia — systematically forgetting past failures
while remembering successes, where organizational or personal memory
selectively retains positive outcomes.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

FAILURE_AMNESIA_SYSTEM = """You are a failure amnesia specialist. Given a decision-making context, assess whether past failures are being systematically forgotten:

Key concepts:
- Failure amnesia: forgetting past failures systematically
- Success-only memory: only successes retained in memory
- Survivorship memory: remembering what survived, forgetting what failed
- Institutional forgetting: organizations losing failure knowledge
- Optimistic reconstruction: past reconstructed as more successful
- Lesson loss: failure lessons not retained
- Repeat failure risk: same failures recurring due to amnesia

When failure amnesia IS present:
- Past failures not remembered or referenced
- Same mistakes being repeated
- Success stories dominating institutional memory
- Failure lessons not retained or transmitted
- Optimistic reconstruction of past performance
- Warning signs from past failures not recognized
- Institutional memory selectively positive

When selective focus on success is appropriate:
- Failures acknowledged and lessons extracted
- Past mistakes inform current decisions
- Both successes and failures in institutional memory
- Failure patterns recognized and avoided
- Lessons from failure actively transmitted
- Past performance assessed realistically
- Warning signs from history recognized

Output JSON with: amnesia_present (bool), severity (none/mild/moderate/severe), context (decision context), forgotten_failures (what failures are forgotten), remembered_successes (what successes dominate), repeat_risk (what failures might recur), recommendation (balanced_memory/mild_success_preference/significant_failure_amnesia/major_institutional_forgetting/systematically_document_and_review_failures)."""

FAILURE_AMNESIA_PROMPT = """Detect failure amnesia:

Decision context: {decision_context}
Past failures: {failures}
Past successes: {successes}
Current approach: {approach}
Domain: {domain}
Context: {context}

Are past failures being systematically forgotten while successes are remembered? Return ONLY valid JSON."""


class FailureAmnesiaService:
    """Detects failure amnesia — systematically forgetting past failures."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        decision_context: str,
        *,
        failures: str = "",
        successes: str = "",
        approach: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect failure amnesia."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=FAILURE_AMNESIA_PROMPT.format(
                decision_context=decision_context,
                failures=failures or "Not specified",
                successes=successes or "Not specified",
                approach=approach or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=FAILURE_AMNESIA_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "decision_context": decision_context[:200],
            "amnesia_present": data.get("amnesia_present", False),
            "severity": data.get("severity", ""),
            "forgotten_failures": data.get("forgotten_failures", ""),
            "remembered_successes": data.get("remembered_successes", ""),
            "repeat_risk": data.get("repeat_risk", ""),
            "recommendation": data.get("recommendation", ""),
        }
