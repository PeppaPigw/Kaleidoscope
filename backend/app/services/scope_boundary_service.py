"""ScopeBoundaryService — Claim Scope Validation.

Identifies when claims are being applied beyond their validated scope.
Detects overgeneralization, scope creep, and unwarranted extrapolation
from limited evidence to broad conclusions.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

SCOPE_SYSTEM = """You are a scope boundary analyst. Given a claim and its application context, determine whether the claim is being applied within or beyond its validated scope. Check for:
- Overgeneralization: applying findings from a specific population/context to all cases
- Temporal extrapolation: assuming past findings hold indefinitely into the future
- Scale extrapolation: assuming what works at one scale works at all scales
- Domain transfer: applying findings from one domain to another without validation
- Precision inflation: treating approximate findings as exact

Output JSON with: scope_analysis.original_scope (what the evidence actually supports), scope_analysis.applied_scope (how the claim is being used), scope_analysis.scope_violation (bool), scope_analysis.violation_type (none/overgeneralization/temporal/scale/domain/precision), scope_analysis.severity (none/minor/moderate/major/critical), scope_analysis.valid_boundaries (where the claim legitimately applies), scope_analysis.invalid_extensions (where it's being stretched too far), scope_analysis.correction (how to properly scope the claim), scope_analysis.confidence (0-1)."""

SCOPE_PROMPT = """Check scope boundaries for this claim:

Claim: {claim}
Applied to: {application}
Original evidence context: {evidence_context}
Domain: {domain}

Is this claim being applied beyond its validated scope? Return ONLY valid JSON."""


class ScopeBoundaryService:
    """Detects when claims are applied beyond their validated scope."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def check_scope(
        self,
        claim: str,
        application: str,
        *,
        evidence_context: str = "",
        domain: str = "",
    ) -> dict:
        """Check if a claim is being applied beyond its scope."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=SCOPE_PROMPT.format(
                claim=claim,
                application=application,
                evidence_context=evidence_context or "Not specified",
                domain=domain or "research",
            ),
            system=SCOPE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)
        analysis = data.get("scope_analysis", data)

        return {
            "claim": claim[:200],
            "application": application[:200],
            "scope_violation": analysis.get("scope_violation", False),
            "violation_type": analysis.get("violation_type", "none"),
            "severity": analysis.get("severity", "none"),
            "original_scope": analysis.get("original_scope", ""),
            "valid_boundaries": analysis.get("valid_boundaries", []),
            "invalid_extensions": analysis.get("invalid_extensions", []),
            "correction": analysis.get("correction", ""),
            "confidence": analysis.get("confidence", 0),
        }
