"""LegitimacyService — Legitimacy Assessment.

Evaluates whether a claim, institution, decision, or authority has
legitimate standing. Distinct from expertise (epistemic trespassing) —
this is about whether the entity has the right kind of authority:
democratic mandate, procedural legitimacy, consent, track record,
or proper jurisdiction.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

LEGITIMACY_SYSTEM = """You are a legitimacy assessment specialist. Given a claim of authority or a decision, assess whether it has legitimate standing:
- Does the authority have proper jurisdiction over this matter?
- Was the authority granted through legitimate processes (election, appointment, expertise, consent)?
- Is the authority being exercised within its proper scope?
- Do those affected recognize the authority as legitimate?
- Has the authority maintained legitimacy through fair process and accountability?

Output JSON with: legitimacy_assessment (legitimate/questionable/illegitimate), legitimacy_score (0-1), authority_type (democratic/expert/traditional/legal/procedural/charismatic/delegated), source_of_authority (where the authority claims to derive from), jurisdiction_match (bool — is this within their proper scope?), process_legitimacy (bool — was authority obtained through proper process?), consent_of_governed (bool — do those affected accept this authority?), accountability_present (bool — can the authority be held accountable?), scope_creep (bool — is authority being exercised beyond its mandate?), legitimacy_challenges (what undermines the legitimacy claim), legitimacy_supports (what supports the legitimacy claim), alternative_authorities (who else might have legitimate standing here), democratic_deficit (bool — are affected parties excluded from decision?), track_record (how has this authority performed historically?), legitimacy_erosion_risk (0-1 — risk that current actions undermine future legitimacy), recommendation (accept_authority/challenge_jurisdiction/demand_accountability/seek_alternative/conditional_acceptance)."""

LEGITIMACY_PROMPT = """Assess legitimacy:

Authority/Decision: {authority}
Claim being made: {claim}
Affected parties: {affected_parties}
Basis of authority: {basis}
Domain: {domain}
Context: {context}

Is this authority legitimate? Return ONLY valid JSON."""


class LegitimacyService:
    """Assesses legitimacy of authority claims and decisions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def assess(
        self,
        authority: str,
        *,
        claim: str = "",
        affected_parties: str = "",
        basis: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Assess legitimacy."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=LEGITIMACY_PROMPT.format(
                authority=authority,
                claim=claim or "Not specified",
                affected_parties=affected_parties or "Not specified",
                basis=basis or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=LEGITIMACY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "authority": authority[:200],
            "legitimacy_assessment": data.get("legitimacy_assessment", ""),
            "legitimacy_score": data.get("legitimacy_score", 0),
            "authority_type": data.get("authority_type", ""),
            "source_of_authority": data.get("source_of_authority", ""),
            "jurisdiction_match": data.get("jurisdiction_match", False),
            "process_legitimacy": data.get("process_legitimacy", False),
            "consent_of_governed": data.get("consent_of_governed", False),
            "accountability_present": data.get("accountability_present", False),
            "scope_creep": data.get("scope_creep", False),
            "legitimacy_challenges": data.get("legitimacy_challenges", ""),
            "legitimacy_supports": data.get("legitimacy_supports", ""),
            "alternative_authorities": data.get("alternative_authorities", ""),
            "democratic_deficit": data.get("democratic_deficit", False),
            "track_record": data.get("track_record", ""),
            "legitimacy_erosion_risk": data.get("legitimacy_erosion_risk", 0),
            "recommendation": data.get("recommendation", ""),
        }
