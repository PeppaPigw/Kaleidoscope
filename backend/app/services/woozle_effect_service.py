"""WoozleEffectService — Woozle Effect Detection.

Detects the woozle effect — repeated citation of unverified claims
creating false authority. Named after Winnie-the-Pooh tracking
his own footprints. A claim gets cited, the citation gets cited,
and soon the claim appears well-established despite never having
been verified. Citation chains create the illusion of evidence.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

WOOZLE_EFFECT_SYSTEM = """You are a woozle effect specialist. Given a claim and its evidence base, assess whether repeated citation is creating false authority:

Key concepts:
- Woozle effect: citation chains creating illusion of evidence
- Circular citation: A cites B cites A (or longer chains)
- Citation cascade: one source cited by many, creating false consensus
- Phantom authority: citations that don't actually support the claim
- Source degradation: meaning shifts through citation chain
- Factoid creation: repetition transforms speculation into "fact"
- Evidence laundering: weak evidence gains authority through citation

When woozle effect IS present:
- A claim is widely cited but traces back to a single unverified source
- Citations don't actually support the specific claim being made
- The original source is weaker than the citation pattern suggests
- Repeated citation has elevated speculation to established fact
- No one has independently verified the original claim
- The claim has been subtly transformed through citation chains
- "Everyone knows X" but no one has primary evidence

When citation IS appropriate:
- Multiple independent sources confirm the claim
- The original source is methodologically sound
- Citations accurately represent the source material
- The evidence base has been independently verified
- Citation chains are transparent and traceable
- Limitations of the original source are acknowledged

Output JSON with: woozle_effect_present (bool), severity (none/mild/moderate/severe), claim (what claim is being evaluated), citation_chain (how is the claim supported), original_source (what is the ultimate source), source_quality (how strong is the original evidence), independent_verification (has anyone independently verified), transformation (has the claim changed through citation), recommendation (evidence_solid/mild_citation_inflation/significant_woozle_effect/major_phantom_authority/verify_original_source)."""

WOOZLE_EFFECT_PROMPT = """Detect woozle effect:

Claim: {claim}
Citations: {citations}
Original source: {original}
Verification: {verification}
Domain: {domain}
Context: {context}

Is repeated citation creating false authority for an unverified claim? Return ONLY valid JSON."""


class WoozleEffectService:
    """Detects woozle effect — citation chains creating false authority."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        claim: str,
        *,
        citations: str = "",
        original: str = "",
        verification: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect woozle effect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=WOOZLE_EFFECT_PROMPT.format(
                claim=claim,
                citations=citations or "Not specified",
                original=original or "Not specified",
                verification=verification or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=WOOZLE_EFFECT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "claim": claim[:200],
            "woozle_effect_present": data.get("woozle_effect_present", False),
            "severity": data.get("severity", ""),
            "citation_chain": data.get("citation_chain", ""),
            "original_source": data.get("original_source", ""),
            "source_quality": data.get("source_quality", ""),
            "independent_verification": data.get("independent_verification", ""),
            "transformation": data.get("transformation", ""),
            "recommendation": data.get("recommendation", ""),
        }
