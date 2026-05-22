"""TestimonialInjusticeService — Testimonial Injustice Detection.

Detects testimonial injustice — deflating the credibility of a
speaker due to identity prejudice rather than evidence quality,
where social identity affects how testimony is received.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

TESTIMONIAL_INJUSTICE_SYSTEM = """You are a testimonial injustice specialist. Given a credibility assessment, evaluate whether speaker credibility is being deflated due to identity prejudice:

Key concepts:
- Testimonial injustice: credibility deficit due to identity prejudice
- Credibility deficit: less credibility given than warranted
- Identity prejudice: prejudice based on social identity
- Epistemic objectification: treating knower as mere source
- Credibility excess: giving more credibility due to identity
- Systematic credibility patterns: consistent deflation for groups
- Epistemic silencing: effectively silencing through disbelief

When testimonial injustice IS present:
- Credibility deflated based on speaker's identity
- Same evidence weighted differently based on who presents it
- Identity-based patterns of disbelief
- Testimony dismissed without engaging content
- Speaker's competence questioned based on identity
- Systematic credibility deficit for certain groups
- Evidence quality ignored in favor of identity assessment

When credibility assessment is appropriate:
- Credibility based on relevant expertise and track record
- Identity not factor in evidence evaluation
- Same standards applied regardless of speaker
- Content engaged with on merits
- Credibility assessment based on relevant factors
- Expertise genuinely relevant to claim
- Track record of reliability considered

Output JSON with: injustice_present (bool), severity (none/mild/moderate/severe), testimony (what testimony is given), credibility_assessment (how credibility is assessed), identity_factor (what identity factor affects assessment), evidence_quality (actual quality of evidence), recommendation (appropriate_credibility_assessment/mild_identity_influence/significant_testimonial_injustice/major_epistemic_silencing/assess_on_evidence_not_identity)."""

TESTIMONIAL_INJUSTICE_PROMPT = """Detect testimonial injustice:

Testimony: {testimony}
Speaker: {speaker}
Credibility given: {credibility}
Evidence quality: {evidence}
Domain: {domain}
Context: {context}

Is speaker credibility being deflated due to identity prejudice rather than evidence quality? Return ONLY valid JSON."""


class TestimonialInjusticeService:
    """Detects testimonial injustice — credibility deficit due to identity prejudice."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        testimony: str,
        *,
        speaker: str = "",
        credibility: str = "",
        evidence: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect testimonial injustice."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=TESTIMONIAL_INJUSTICE_PROMPT.format(
                testimony=testimony,
                speaker=speaker or "Not specified",
                credibility=credibility or "Not specified",
                evidence=evidence or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=TESTIMONIAL_INJUSTICE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "testimony": testimony[:200],
            "injustice_present": data.get("injustice_present", False),
            "severity": data.get("severity", ""),
            "credibility_assessment": data.get("credibility_assessment", ""),
            "identity_factor": data.get("identity_factor", ""),
            "evidence_quality": data.get("evidence_quality", ""),
            "recommendation": data.get("recommendation", ""),
        }
