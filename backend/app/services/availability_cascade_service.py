"""AvailabilityCascadeService — Availability Cascade Detection.

Detects availability cascade — a self-reinforcing cycle where
a belief gains credibility through repetition in public
discourse. Kuran & Sunstein (1999). Something repeated often
enough starts to seem true. Media amplification creates
perceived consensus. "Everyone knows X" when few have
independently verified X.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

AVAILABILITY_CASCADE_SYSTEM = """You are an availability cascade specialist. Given a widely-held belief, assess whether its credibility comes from repetition rather than evidence:

Key concepts (Kuran & Sunstein, 1999):
- Availability cascade: belief gains credibility through repetition
- Informational cascade: people adopt beliefs because others hold them
- Reputational cascade: people express beliefs to maintain social standing
- Illusory truth effect: repetition increases perceived truth
- Media amplification: coverage creates perceived importance/consensus
- Social proof interaction: widespread belief used as evidence
- Manufactured consensus: repetition creating appearance of agreement

When availability cascade IS present:
- A claim is widely believed primarily because it's widely repeated
- "Everyone knows X" but few can cite primary evidence
- Media repetition has created perceived consensus
- The belief spread through social channels rather than evidence
- Questioning the belief is socially costly (reputational cascade)
- The original evidence is thin relative to the confidence level

When the belief IS well-founded:
- Multiple independent lines of evidence support it
- The belief predates its media amplification
- Experts in the relevant field confirm it based on evidence
- The belief survives critical scrutiny
- People can cite evidence beyond "everyone says so"

Output JSON with: availability_cascade_present (bool), severity (none/mild/moderate/severe), belief (what belief is being evaluated), repetition_sources (where is the belief being repeated?), original_evidence (what is the original evidence?), evidence_strength (how strong is the underlying evidence?), social_pressure (is there pressure to agree?), independent_verification (has anyone independently verified?), amplification_mechanism (how did the belief spread?), questioning_cost (what is the social cost of questioning?), recommendation (belief_well_founded/mild_cascade/significant_repetition_driven/major_availability_cascade/verify_independently)."""

AVAILABILITY_CASCADE_PROMPT = """Detect availability cascade:

Belief: {belief}
Prevalence: {prevalence}
Evidence: {evidence}
Spread mechanism: {mechanism}
Domain: {domain}
Context: {context}

Is this belief's credibility driven by repetition rather than evidence? Return ONLY valid JSON."""


class AvailabilityCascadeService:
    """Detects availability cascade — belief gaining credibility through repetition."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        belief: str,
        *,
        prevalence: str = "",
        evidence: str = "",
        mechanism: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect availability cascade."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=AVAILABILITY_CASCADE_PROMPT.format(
                belief=belief,
                prevalence=prevalence or "Not specified",
                evidence=evidence or "Not specified",
                mechanism=mechanism or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=AVAILABILITY_CASCADE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "belief": belief[:200],
            "availability_cascade_present": data.get("availability_cascade_present", False),
            "severity": data.get("severity", ""),
            "repetition_sources": data.get("repetition_sources", ""),
            "original_evidence": data.get("original_evidence", ""),
            "evidence_strength": data.get("evidence_strength", ""),
            "social_pressure": data.get("social_pressure", ""),
            "independent_verification": data.get("independent_verification", ""),
            "amplification_mechanism": data.get("amplification_mechanism", ""),
            "questioning_cost": data.get("questioning_cost", ""),
            "recommendation": data.get("recommendation", ""),
        }
