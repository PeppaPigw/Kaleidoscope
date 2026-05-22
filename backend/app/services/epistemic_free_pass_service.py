"""EpistemicFreePassService — Epistemic Free Pass Detection.

Detects epistemic free pass — giving certain actors a free pass on
epistemic standards, where some are held to lower standards of
evidence or reasoning based on status or identity.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_FREE_PASS_SYSTEM = """You are an epistemic free pass specialist. Given an epistemic standards situation, assess whether certain actors are given a free pass:

Key concepts:
- Epistemic free pass: some actors held to lower standards
- Standards asymmetry: different standards for different actors
- Status-based exemption: high-status actors exempt from rigor
- Identity-based pass: standards relaxed based on identity
- Accountability exemption: some not held accountable for claims
- Double standard epistemic: different evidence required from different sources
- Privilege of assertion: some can assert without evidence

When epistemic free pass IS present:
- Certain actors held to lower epistemic standards
- Status granting exemption from evidence requirements
- Identity determining what standards apply
- Some actors not held accountable for claims
- Double standards in evidence requirements
- Privilege of assertion without evidence for some
- Standards asymmetry based on who is speaking

When differential standards are appropriate:
- Standards proportionate to expertise and role
- Accountability proportionate to authority
- Standards based on claim type not claimant identity
- Evidence requirements consistent across actors
- Expertise acknowledged without exempting from standards
- Authority carrying more not less accountability
- Standards applied to claims not persons

Output JSON with: free_pass_present (bool), severity (none/mild/moderate/severe), situation (what situation exists), exempted (who gets the free pass), standard_applied (what standard others face), basis (what basis for exemption), recommendation (consistent_standards/mild_status_preference/significant_epistemic_free_pass/major_accountability_exemption/apply_standards_consistently)."""

EPISTEMIC_FREE_PASS_PROMPT = """Detect epistemic free pass:

Situation: {situation}
Actor exempted: {exempted}
Standards for others: {standards}
Basis for exemption: {basis}
Domain: {domain}
Context: {context}

Are certain actors given a free pass on epistemic standards based on status or identity? Return ONLY valid JSON."""


class EpistemicFreePassService:
    """Detects epistemic free pass — some actors exempt from epistemic standards."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        exempted: str = "",
        standards: str = "",
        basis: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic free pass."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_FREE_PASS_PROMPT.format(
                situation=situation,
                exempted=exempted or "Not specified",
                standards=standards or "Not specified",
                basis=basis or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_FREE_PASS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "free_pass_present": data.get("free_pass_present", False),
            "severity": data.get("severity", ""),
            "exempted": data.get("exempted", ""),
            "standard_applied": data.get("standard_applied", ""),
            "basis": data.get("basis", ""),
            "recommendation": data.get("recommendation", ""),
        }
