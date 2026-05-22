"""EpistemicBurialService — Epistemic Burial Detection.

Detects epistemic burial — deliberate or accidental burial of
important knowledge making it inaccessible.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_BURIAL_SYSTEM = """You are an epistemic burial specialist. Given a knowledge accessibility pattern, assess whether important knowledge has been buried:

Key concepts:
- Epistemic burial: important knowledge made inaccessible
- Deliberate suppression: deliberately burying knowledge
- Accidental loss: accidentally losing access to knowledge
- Depth of burial: how deeply buried the knowledge is
- Recovery difficulty: how difficult recovery would be
- Knowledge archaeology: need to excavate buried knowledge
- Institutional forgetting: institutions forgetting important knowledge

When epistemic burial IS present:
- Important knowledge made inaccessible
- Knowledge deliberately suppressed or hidden
- Access to important knowledge accidentally lost
- Knowledge buried deeply and hard to find
- Recovery would be difficult or impossible
- Need for archaeological excavation of knowledge
- Institutions forgetting important knowledge

When accessible knowledge is present:
- Important knowledge readily accessible
- Knowledge openly available
- Access to knowledge maintained
- Knowledge easy to find and use
- Knowledge readily recoverable
- No excavation needed
- Institutions maintaining knowledge access

Output JSON with: burial_present (bool), severity (none/mild/moderate/severe), knowledge (what knowledge is buried), method (how it was buried), depth (how deeply buried), recovery (how difficult to recover), recommendation (accessible_knowledge/mild_obscurity/significant_burial/major_suppression/excavate_and_restore)."""

EPISTEMIC_BURIAL_PROMPT = """Detect epistemic burial:

Knowledge: {knowledge}
Method: {method}
Depth: {depth}
Recovery: {recovery}
Domain: {domain}
Context: {context}

Has important knowledge been buried making it inaccessible? Return ONLY valid JSON."""


class EpistemicBurialService:
    """Detects epistemic burial — important knowledge made inaccessible."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        knowledge: str,
        *,
        method: str = "",
        depth: str = "",
        recovery: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic burial."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_BURIAL_PROMPT.format(
                knowledge=knowledge,
                method=method or "Not specified",
                depth=depth or "Not specified",
                recovery=recovery or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_BURIAL_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "knowledge": knowledge[:200],
            "burial_present": data.get("burial_present", False),
            "severity": data.get("severity", ""),
            "method": data.get("method", ""),
            "depth": data.get("depth", ""),
            "recovery": data.get("recovery", ""),
            "recommendation": data.get("recommendation", ""),
        }
