"""EpistemicSelectiveMemoryService — Epistemic Selective Memory Detection.

Detects epistemic selective memory — selectively remembering evidence
that supports preferred conclusions while forgetting contradicting evidence.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SELECTIVE_MEMORY_SYSTEM = """You are an epistemic selective memory specialist. Given selectively remembering supporting evidence, assess selective memory:

Key concepts:
- Epistemic selective memory: selectively remembering evidence supporting conclusions
- Confirmation memory: remembering only confirming evidence
- Disconfirmation amnesia: forgetting disconfirming evidence
- Evidence filtering: filtering memories to support position
- Convenient recall: recalling only what is convenient
- Memory cherry-picking: cherry-picking from memory
- Biased retrieval: biased retrieval from memory stores

When epistemic selective memory IS present:
- Selectively remembering supporting evidence
- Remembering only confirming
- Forgetting disconfirming
- Filtering memories to support
- Recalling only convenient
- Cherry-picking from memory
- Biased retrieval

When no selective memory:
- Balanced memory retrieval
- Remembering confirming and disconfirming
- Retaining all evidence
- Unfiltered memory access
- Comprehensive recall
- Fair memory sampling
- Unbiased retrieval

Output JSON with: selective_memory_detected (bool), severity (none/mild/moderate/severe), confirmation_memory (what confirming evidence selectively remembered), disconfirmation_amnesia (what disconfirming evidence forgotten), evidence_filtering (what filtered to support), convenient_recall (what conveniently recalled), recommendation (no_selective_memory/mild_balance_practice/significant_comprehensive_recall/major_intensive_memory_audit/emergency_complete_selective_memory)."""

EPISTEMIC_SELECTIVE_MEMORY_PROMPT = """Detect epistemic selective memory:

Confirmation memory: {confirmation_memory}
Disconfirmation amnesia: {disconfirmation_amnesia}
Evidence filtering: {evidence_filtering}
Convenient recall: {convenient_recall}
Domain: {domain}
Context: {context}

Is there selectively remembering evidence that supports preferred conclusions? Return ONLY valid JSON."""


class EpistemicSelectiveMemoryService:
    """Detects epistemic selective memory — selectively remembering supporting evidence."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        confirmation_memory: str,
        *,
        disconfirmation_amnesia: str = "",
        evidence_filtering: str = "",
        convenient_recall: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic selective memory."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SELECTIVE_MEMORY_PROMPT.format(
                confirmation_memory=confirmation_memory,
                disconfirmation_amnesia=disconfirmation_amnesia or "Not specified",
                evidence_filtering=evidence_filtering or "Not specified",
                convenient_recall=convenient_recall or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SELECTIVE_MEMORY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "confirmation_memory": confirmation_memory[:200],
            "selective_memory_detected": data.get("selective_memory_detected", False),
            "severity": data.get("severity", ""),
            "disconfirmation_amnesia": data.get("disconfirmation_amnesia", ""),
            "evidence_filtering": data.get("evidence_filtering", ""),
            "convenient_recall": data.get("convenient_recall", ""),
            "recommendation": data.get("recommendation", ""),
        }
