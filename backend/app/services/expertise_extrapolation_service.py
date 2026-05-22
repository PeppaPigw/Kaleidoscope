"""ExpertiseExtrapolationService — Expertise Extrapolation Detection.

Detects expertise extrapolation — extending expertise beyond its
valid domain, where competence in one area is treated as competence
in unrelated areas without justification.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EXPERTISE_EXTRAPOLATION_SYSTEM = """You are an expertise extrapolation specialist. Given a claim, assess whether expertise is being extended beyond its valid domain:

Key concepts:
- Expertise extrapolation: competence extended beyond valid domain
- Domain transfer error: expertise in A assumed for B
- Halo expertise: success in one field assumed for all
- Nobel disease: laureates opining outside their field
- Competence creep: gradual expansion beyond expertise
- Authority spillover: authority in one domain claimed for another
- Expertise inflation: narrow expertise presented as broad

When expertise extrapolation IS present:
- Expert opines outside their domain of competence
- Success in one field treated as qualification for another
- Narrow expertise presented as broad authority
- Domain-specific knowledge applied to unrelated areas
- Competence in one area assumed to transfer without justification
- Authority from one field claimed in another
- Expert's opinion weighted equally across all domains

When cross-domain expertise is appropriate:
- Transfer of expertise explicitly justified
- Relevant connections between domains identified
- Limitations of cross-domain application acknowledged
- Expert's specific relevant knowledge identified
- Cross-domain competence independently established
- Appropriate humility about domain boundaries
- Transferable skills distinguished from domain knowledge

Output JSON with: extrapolation_present (bool), severity (none/mild/moderate/severe), expert (who is claiming expertise), source_domain (domain of actual expertise), target_domain (domain expertise is extended to), justification (justification for transfer), recommendation (appropriate_cross_domain/mild_overreach/significant_expertise_extrapolation/major_domain_transfer_error/bound_expertise_to_domain)."""

EXPERTISE_EXTRAPOLATION_PROMPT = """Detect expertise extrapolation:

Claim: {claim}
Expert's domain: {source_domain}
Claim's domain: {target_domain}
Transfer justification: {justification}
Domain: {domain}
Context: {context}

Is expertise being extended beyond its valid domain? Return ONLY valid JSON."""


class ExpertiseExtrapolationService:
    """Detects expertise extrapolation — extending expertise beyond valid domain."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        claim: str,
        *,
        source_domain: str = "",
        target_domain: str = "",
        justification: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect expertise extrapolation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EXPERTISE_EXTRAPOLATION_PROMPT.format(
                claim=claim,
                source_domain=source_domain or "Not specified",
                target_domain=target_domain or "Not specified",
                justification=justification or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EXPERTISE_EXTRAPOLATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "claim": claim[:200],
            "extrapolation_present": data.get("extrapolation_present", False),
            "severity": data.get("severity", ""),
            "source_domain": data.get("source_domain", ""),
            "target_domain": data.get("target_domain", ""),
            "justification": data.get("justification", ""),
            "recommendation": data.get("recommendation", ""),
        }
