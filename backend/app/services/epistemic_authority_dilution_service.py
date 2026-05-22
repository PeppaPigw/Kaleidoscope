"""EpistemicAuthorityDilutionService — Epistemic Authority Dilution Detection.

Detects epistemic authority dilution — diluting genuine authority by
over-extending claims beyond what expertise supports.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_AUTHORITY_DILUTION_SYSTEM = """You are an epistemic authority dilution specialist. Given authority dilution, assess over-extension:

Key concepts:
- Epistemic authority dilution: genuine authority diluted by over-extension
- Scope creep of claims: claims expanding beyond evidence base
- Confidence over-extension: high confidence extended beyond warranted range
- Generalization beyond data: generalizing findings beyond study population
- Temporal over-extension: extending findings beyond their temporal validity
- Conditional erasure: removing conditions under which findings hold
- Precision dilution: precise findings diluted into vague general claims

When epistemic authority dilution IS present:
- Genuine authority diluted by over-extension
- Claims scope creeping
- Confidence over-extended
- Generalizations beyond data
- Temporal validity over-extended
- Conditions erased
- Precision diluted

When no authority dilution:
- Authority appropriately bounded
- Claims within scope
- Confidence calibrated
- Generalizations appropriate
- Temporal bounds stated
- Conditions preserved
- Precision maintained

Output JSON with: authority_dilution_detected (bool), severity (none/mild/moderate/severe), scope_creep (what scope creeping), confidence_over_extension (what confidence over-extended), generalization_beyond_data (what generalized beyond data), conditional_erasure (what conditions erased), recommendation (no_authority_dilution/mild_scope_bounding/significant_claim_narrowing/major_intensive_evidence_matching/emergency_complete_authority_dilution)."""

EPISTEMIC_AUTHORITY_DILUTION_PROMPT = """Detect epistemic authority dilution:

Scope creep: {scope_creep}
Confidence over extension: {confidence_over_extension}
Generalization beyond data: {generalization_beyond_data}
Conditional erasure: {conditional_erasure}
Domain: {domain}
Context: {context}

Is genuine authority being diluted by over-extending claims? Return ONLY valid JSON."""


class EpistemicAuthorityDilutionService:
    """Detects epistemic authority dilution — over-extension of claims."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        scope_creep: str,
        *,
        confidence_over_extension: str = "",
        generalization_beyond_data: str = "",
        conditional_erasure: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic authority dilution."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_AUTHORITY_DILUTION_PROMPT.format(
                scope_creep=scope_creep,
                confidence_over_extension=confidence_over_extension or "Not specified",
                generalization_beyond_data=generalization_beyond_data or "Not specified",
                conditional_erasure=conditional_erasure or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_AUTHORITY_DILUTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "scope_creep": scope_creep[:200],
            "authority_dilution_detected": data.get("authority_dilution_detected", False),
            "severity": data.get("severity", ""),
            "confidence_over_extension": data.get("confidence_over_extension", ""),
            "generalization_beyond_data": data.get("generalization_beyond_data", ""),
            "conditional_erasure": data.get("conditional_erasure", ""),
            "recommendation": data.get("recommendation", ""),
        }
