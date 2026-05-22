"""EpistemicBorderDisputeService — Epistemic Border Dispute Detection.

Detects epistemic border disputes — contested boundaries between
knowledge domains creating confusion about jurisdiction.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_BORDER_DISPUTE_SYSTEM = """You are an epistemic border dispute specialist. Given a knowledge domain conflict, assess whether contested boundaries create confusion:

Key concepts:
- Epistemic border dispute: contested boundaries between knowledge domains
- Jurisdiction confusion: unclear which domain owns a question
- Overlapping claims: multiple domains claiming same territory
- No man's land: areas claimed by no domain
- Boundary warfare: domains fighting over territory
- Demarcation failure: failure to clearly mark boundaries
- Interdisciplinary gap: gaps between domains where questions fall

When border dispute IS present:
- Contested boundaries between knowledge domains
- Unclear which domain has jurisdiction over questions
- Multiple domains claiming same intellectual territory
- Areas claimed by no domain falling through cracks
- Domains fighting over intellectual territory
- Failure to clearly mark domain boundaries
- Questions falling into gaps between domains

When clear boundaries are present:
- Clear boundaries between knowledge domains
- Jurisdiction over questions well-defined
- No overlapping claims on territory
- All areas claimed by appropriate domains
- Domains cooperating at boundaries
- Boundaries clearly marked and respected
- Questions directed to appropriate domains

Output JSON with: border_dispute (bool), severity (none/mild/moderate/severe), domains (what domains are in dispute), territory (what territory is contested), confusion (what confusion results), gap (what falls through cracks), recommendation (clear_boundaries/mild_overlap/significant_dispute/major_jurisdiction_failure/establish_demarcation)."""

EPISTEMIC_BORDER_DISPUTE_PROMPT = """Detect epistemic border dispute:

Domains: {domains}
Territory: {territory}
Confusion: {confusion}
Gap: {gap}
Domain: {domain}
Context: {context}

Are contested boundaries between knowledge domains creating confusion? Return ONLY valid JSON."""


class EpistemicBorderDisputeService:
    """Detects epistemic border disputes — contested domain boundaries."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        domains: str,
        *,
        territory: str = "",
        confusion: str = "",
        gap: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic border dispute."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_BORDER_DISPUTE_PROMPT.format(
                domains=domains,
                territory=territory or "Not specified",
                confusion=confusion or "Not specified",
                gap=gap or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_BORDER_DISPUTE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "domains": domains[:200],
            "border_dispute": data.get("border_dispute", False),
            "severity": data.get("severity", ""),
            "territory": data.get("territory", ""),
            "confusion": data.get("confusion", ""),
            "gap": data.get("gap", ""),
            "recommendation": data.get("recommendation", ""),
        }
