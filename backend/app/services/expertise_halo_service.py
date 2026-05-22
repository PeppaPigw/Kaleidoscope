"""ExpertiseHaloService — Expertise Halo Detection.

Detects expertise halo — when expertise in one domain is
assumed to transfer to unrelated domains. A Nobel physicist
opining on economics, or a successful CEO advising on
public health, may receive unwarranted credibility.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EXPERTISE_HALO_SYSTEM = """You are an expertise halo specialist. Given a claim backed by authority, assess whether the expertise actually applies:

Key concepts:
- Expertise halo: expertise in one domain assumed to transfer
- Domain specificity: expertise is usually narrow
- Nobel disease: Nobel laureates making claims outside their field
- Celebrity expertise: fame confused with knowledge
- Credential inflation: using credentials beyond their scope
- Transfer assumption: assuming skills transfer across domains
- Epistemic trespass: experts opining outside their competence

When expertise halo IS present:
- Expert's credentials are in a different domain than the claim
- Authority cited from an unrelated field
- Success in one area used to validate opinions in another
- Credentials used beyond their actual scope
- "They're brilliant, so they must be right about this too"
- Domain-specific expertise treated as general wisdom
- No acknowledgment that expertise doesn't transfer

When expertise halo is NOT present:
- Expert's credentials match the domain of the claim
- Authority cited from the relevant field
- Domain boundaries of expertise acknowledged
- Credentials used within their proper scope
- Expert's opinion weighted by domain relevance
- Transfer of expertise explicitly justified when claimed
- Distinction made between general intelligence and domain expertise

Output JSON with: halo_present (bool), severity (none/mild/moderate/severe), expert (who is being cited), actual_expertise (their real domain), claim_domain (domain of the claim), transfer_gap (how far the expertise must transfer), recommendation (no_halo/mild_stretch/significant_halo/major_domain_mismatch/find_domain_expert)."""

EXPERTISE_HALO_PROMPT = """Detect expertise halo:

Claim: {claim}
Expert cited: {expert}
Expert's domain: {expert_domain}
Claim domain: {claim_domain}
Domain: {domain}
Context: {context}

Is expertise from one domain being assumed to transfer to another? Return ONLY valid JSON."""


class ExpertiseHaloService:
    """Detects expertise halo — expertise assumed to transfer across domains."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        claim: str,
        *,
        expert: str = "",
        expert_domain: str = "",
        claim_domain: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect expertise halo."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EXPERTISE_HALO_PROMPT.format(
                claim=claim,
                expert=expert or "Not specified",
                expert_domain=expert_domain or "Not specified",
                claim_domain=claim_domain or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EXPERTISE_HALO_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "claim": claim[:200],
            "halo_present": data.get("halo_present", False),
            "severity": data.get("severity", ""),
            "actual_expertise": data.get("actual_expertise", ""),
            "claim_domain": data.get("claim_domain", ""),
            "transfer_gap": data.get("transfer_gap", ""),
            "recommendation": data.get("recommendation", ""),
        }
