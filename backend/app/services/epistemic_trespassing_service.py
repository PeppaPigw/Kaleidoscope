"""EpistemicTrespassingService — Epistemic Trespassing Detection.

Detects epistemic trespassing — experts opining outside their domain
of expertise, leveraging authority from one field in another where
they lack competence.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_TRESPASSING_SYSTEM = """You are an epistemic trespassing specialist. Given a claim or opinion, assess whether someone is opining outside their domain of expertise:

Key concepts:
- Epistemic trespassing: experts speaking beyond their competence
- Authority transfer: leveraging credibility from one field in another
- Domain boundaries: limits of expertise
- Credential inflation: using credentials to claim broader authority
- Halo effect of expertise: being right in one area assumed to mean right in all
- Dunning-Kruger in experts: overconfidence outside one's domain
- Interdisciplinary confusion: conflating familiarity with expertise

When epistemic trespassing IS present:
- Expert opining far outside their trained domain
- Authority from one field used to claim credibility in another
- Domain-specific methods applied where they don't fit
- Credentials cited for unrelated claims
- Confidence level exceeds actual competence in the domain
- No acknowledgment of limited expertise in the area
- Opinions presented as expert when they are lay opinions

When cross-domain contribution is appropriate:
- Expertise genuinely transfers (methodological skills)
- Domain boundaries acknowledged
- Claims appropriately hedged for level of expertise
- Interdisciplinary work with genuine competence in both
- Collaboration with domain experts
- Limitations of cross-domain knowledge stated
- Novel perspective offered as perspective, not authority

Output JSON with: trespassing_present (bool), severity (none/mild/moderate/severe), claim (what is claimed), home_domain (expert's actual domain), trespassed_domain (domain being opined on), authority_transfer (how authority is being transferred), recommendation (appropriate_cross_domain/mild_overreach/significant_trespassing/major_authority_abuse/stay_in_lane)."""

EPISTEMIC_TRESPASSING_PROMPT = """Detect epistemic trespassing:

Claim: {claim}
Claimant expertise: {expertise}
Target domain: {target}
Credentials cited: {credentials}
Domain: {domain}
Context: {context}

Is someone opining outside their domain of expertise using transferred authority? Return ONLY valid JSON."""


class EpistemicTrespassingService:
    """Detects epistemic trespassing — experts opining outside their domain."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        claim: str,
        *,
        expertise: str = "",
        target: str = "",
        credentials: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic trespassing."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_TRESPASSING_PROMPT.format(
                claim=claim,
                expertise=expertise or "Not specified",
                target=target or "Not specified",
                credentials=credentials or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_TRESPASSING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "claim": claim[:200],
            "trespassing_present": data.get("trespassing_present", False),
            "severity": data.get("severity", ""),
            "home_domain": data.get("home_domain", ""),
            "trespassed_domain": data.get("trespassed_domain", ""),
            "authority_transfer": data.get("authority_transfer", ""),
            "recommendation": data.get("recommendation", ""),
        }
