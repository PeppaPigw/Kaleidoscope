"""EpistemicTrespassService — Epistemic Trespassing Detection.

Identifies when a source or argument relies on authority claims
that cross domain boundaries without proper epistemic humility.
A physicist opining on evolutionary biology, an economist making
claims about clinical psychology, etc. — expertise in one domain
does not transfer automatically to another.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

TRESPASS_SYSTEM = """You are an epistemic trespassing specialist. Given a claim and its source, assess whether the authority being invoked is operating outside their domain of expertise:
- Is the claimant's expertise in the same domain as the claim?
- Are they acknowledging the domain boundary or speaking as if their authority transfers?
- Is the claim within their circle of competence?
- Are they citing domain experts or substituting their own judgment?
- Would domain experts agree with their framing?

Output JSON with: trespassing_detected (bool), severity (none/mild/moderate/severe), source_domain (the claimant's actual expertise), claim_domain (the domain the claim belongs to), domain_distance (how far apart the domains are: adjacent/moderate/distant/unrelated), authority_transfer_valid (bool — does expertise actually transfer here?), why_it_might_transfer (legitimate reasons expertise could apply), why_it_doesnt_transfer (reasons the expertise gap matters), epistemic_humility_shown (bool — does the source acknowledge limits?), hidden_complexity (what domain-specific knowledge is being overlooked), dunning_kruger_risk (0-1 — likelihood they don't know what they don't know), credentialed_but_wrong_risk (0-1 — risk that credentials create false confidence), who_should_be_asked (what kind of expert should weigh in), recommendation (accept/verify_with_domain_expert/discount/reject)."""

TRESPASS_PROMPT = """Detect epistemic trespassing:

Claim: {claim}
Source/Claimant: {source}
Source's expertise: {source_expertise}
Claim domain: {claim_domain}
Context: {context}

Is this epistemic trespassing? Return ONLY valid JSON."""


class EpistemicTrespassService:
    """Detects epistemic trespassing — authority claims outside domain."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        claim: str,
        *,
        source: str = "",
        source_expertise: str = "",
        claim_domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic trespassing."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=TRESPASS_PROMPT.format(
                claim=claim,
                source=source or "Not specified",
                source_expertise=source_expertise or "Not specified",
                claim_domain=claim_domain or "Not specified",
                context=context or "No additional context",
            ),
            system=TRESPASS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "claim": claim[:200],
            "trespassing_detected": data.get("trespassing_detected", False),
            "severity": data.get("severity", ""),
            "source_domain": data.get("source_domain", ""),
            "claim_domain": data.get("claim_domain", ""),
            "domain_distance": data.get("domain_distance", ""),
            "authority_transfer_valid": data.get("authority_transfer_valid", False),
            "why_it_might_transfer": data.get("why_it_might_transfer", ""),
            "why_it_doesnt_transfer": data.get("why_it_doesnt_transfer", ""),
            "epistemic_humility_shown": data.get("epistemic_humility_shown", False),
            "hidden_complexity": data.get("hidden_complexity", ""),
            "dunning_kruger_risk": data.get("dunning_kruger_risk", 0),
            "credentialed_but_wrong_risk": data.get("credentialed_but_wrong_risk", 0),
            "who_should_be_asked": data.get("who_should_be_asked", ""),
            "recommendation": data.get("recommendation", ""),
        }
