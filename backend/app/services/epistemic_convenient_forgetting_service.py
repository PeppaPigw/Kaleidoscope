"""EpistemicConvenientForgettingService — Epistemic Convenient Forgetting Detection.

Detects epistemic convenient forgetting — conveniently forgetting evidence
that contradicts preferred beliefs.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_CONVENIENT_FORGETTING_SYSTEM = """You are an epistemic convenient forgetting specialist. Given conveniently forgetting contradicting evidence, assess convenient forgetting:

Key concepts:
- Epistemic convenient forgetting: forgetting evidence contradicting beliefs
- Selective amnesia: forgetting inconvenient facts
- Memory editing: unconsciously editing memories to fit narrative
- Evidence erasure: forgetting evidence that was once known
- Convenient gaps: memory gaps precisely where uncomfortable truths were
- Retroactive ignorance: claiming never to have known what was known
- History revision: revising personal intellectual history

When epistemic convenient forgetting IS present:
- Forgetting contradicting evidence
- Forgetting inconvenient facts
- Editing memories to fit narrative
- Forgetting known evidence
- Gaps where uncomfortable truths were
- Claiming never knew what was known
- Revising intellectual history

When no convenient forgetting:
- Remembering all evidence
- Retaining inconvenient facts
- Accurate memories
- Preserving known evidence
- Complete memory
- Honest about what was known
- Accurate history

Output JSON with: convenient_forgetting_detected (bool), severity (none/mild/moderate/severe), selective_amnesia (what forgetting inconveniently), memory_editing (what editing to fit), evidence_erasure (what forgetting was known), retroactive_ignorance (what claiming never knew), recommendation (no_convenient_forgetting/mild_memory_honesty/significant_evidence_preservation/major_intensive_memory_integrity/emergency_complete_convenient_amnesia)."""

EPISTEMIC_CONVENIENT_FORGETTING_PROMPT = """Detect epistemic convenient forgetting:

Selective amnesia: {selective_amnesia}
Memory editing: {memory_editing}
Evidence erasure: {evidence_erasure}
Retroactive ignorance: {retroactive_ignorance}
Domain: {domain}
Context: {context}

Is there conveniently forgetting evidence that contradicts preferred beliefs? Return ONLY valid JSON."""


class EpistemicConvenientForgettingService:
    """Detects epistemic convenient forgetting — forgetting contradicting evidence."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        selective_amnesia: str,
        *,
        memory_editing: str = "",
        evidence_erasure: str = "",
        retroactive_ignorance: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic convenient forgetting."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_CONVENIENT_FORGETTING_PROMPT.format(
                selective_amnesia=selective_amnesia,
                memory_editing=memory_editing or "Not specified",
                evidence_erasure=evidence_erasure or "Not specified",
                retroactive_ignorance=retroactive_ignorance or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_CONVENIENT_FORGETTING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "selective_amnesia": selective_amnesia[:200],
            "convenient_forgetting_detected": data.get("convenient_forgetting_detected", False),
            "severity": data.get("severity", ""),
            "memory_editing": data.get("memory_editing", ""),
            "evidence_erasure": data.get("evidence_erasure", ""),
            "retroactive_ignorance": data.get("retroactive_ignorance", ""),
            "recommendation": data.get("recommendation", ""),
        }
