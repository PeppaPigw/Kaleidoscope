"""EpistemicAuthorityHaloTransferService — Epistemic Authority Halo Transfer Detection.

Detects epistemic authority halo transfer — transferring authority from one
domain to unrelated domains where expertise doesn't apply.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_AUTHORITY_HALO_TRANSFER_SYSTEM = """You are an epistemic authority halo transfer specialist. Given authority halo transfer, assess domain-crossing authority:

Key concepts:
- Epistemic authority halo transfer: transferring authority across unrelated domains
- Domain expertise leakage: expertise in one area assumed to apply elsewhere
- Nobel disease: accomplished scientists making claims outside their field
- Celebrity authority: fame treated as expertise
- Success halo: success in one domain treated as general competence
- Institutional halo: institutional prestige transferred to individual claims
- Historical authority: past authority assumed to persist in changed conditions

When epistemic authority halo transfer IS present:
- Authority transferred across domains
- Domain expertise leaking
- Nobel disease operating
- Celebrity treated as expertise
- Success halo active
- Institutional prestige transferred
- Historical authority assumed current

When no authority halo transfer:
- Authority bounded to domain
- Expertise limits acknowledged
- Domain boundaries respected
- Celebrity distinguished from expertise
- Success contextualized
- Institutional claims verified
- Authority currency checked

Output JSON with: authority_halo_transfer_detected (bool), severity (none/mild/moderate/severe), domain_expertise_leakage (what expertise leaking), celebrity_authority (what celebrity authority), success_halo (what success halo), institutional_halo (what institutional halo), recommendation (no_halo_transfer/mild_domain_bounding/significant_expertise_verification/major_intensive_authority_audit/emergency_complete_halo_transfer)."""

EPISTEMIC_AUTHORITY_HALO_TRANSFER_PROMPT = """Detect epistemic authority halo transfer:

Domain expertise leakage: {domain_expertise_leakage}
Celebrity authority: {celebrity_authority}
Success halo: {success_halo}
Institutional halo: {institutional_halo}
Domain: {domain}
Context: {context}

Is authority being transferred from one domain to unrelated domains? Return ONLY valid JSON."""


class EpistemicAuthorityHaloTransferService:
    """Detects epistemic authority halo transfer — cross-domain authority leak."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        domain_expertise_leakage: str,
        *,
        celebrity_authority: str = "",
        success_halo: str = "",
        institutional_halo: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic authority halo transfer."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_AUTHORITY_HALO_TRANSFER_PROMPT.format(
                domain_expertise_leakage=domain_expertise_leakage,
                celebrity_authority=celebrity_authority or "Not specified",
                success_halo=success_halo or "Not specified",
                institutional_halo=institutional_halo or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_AUTHORITY_HALO_TRANSFER_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "domain_expertise_leakage": domain_expertise_leakage[:200],
            "authority_halo_transfer_detected": data.get("authority_halo_transfer_detected", False),
            "severity": data.get("severity", ""),
            "celebrity_authority": data.get("celebrity_authority", ""),
            "success_halo": data.get("success_halo", ""),
            "institutional_halo": data.get("institutional_halo", ""),
            "recommendation": data.get("recommendation", ""),
        }
