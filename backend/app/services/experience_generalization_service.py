"""ExperienceGeneralizationService — Experience Generalization Detection.

Detects inappropriate experience generalization — generalizing from
limited personal experience to universal claims, where anecdote
becomes treated as data.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EXPERIENCE_GENERALIZATION_SYSTEM = """You are an experience generalization specialist. Given a claim derived from experience, assess whether personal experience is being inappropriately generalized:

Key concepts:
- Experience generalization: personal experience treated as universal
- Anecdote as data: individual cases treated as representative
- Sample of one: single experience generating universal claims
- Perspective universalization: own perspective assumed universal
- Experiential authority: personal experience trumping systematic data
- Representativeness assumption: own experience assumed typical
- Inductive overreach: too much concluded from too little experience

When experience generalization IS present:
- Personal experience treated as universal truth
- Individual cases generalized without justification
- Own perspective assumed to be everyone's
- Anecdotes used as if they were systematic data
- Limited experience generating broad claims
- Representativeness of experience not questioned
- Systematic evidence ignored in favor of personal experience

When learning from experience is appropriate:
- Experience acknowledged as limited data point
- Generalization bounded by sample size
- Systematic evidence sought to complement experience
- Own perspective recognized as one among many
- Anecdotes used as illustration not proof
- Representativeness of experience questioned
- Experience and data integrated appropriately

Output JSON with: generalization_present (bool), severity (none/mild/moderate/severe), claim (what claim is made), experience_base (what experience supports it), scope_claimed (how broadly it's applied), evidence_gap (what systematic evidence is missing), recommendation (appropriate_experiential_learning/mild_overgeneralization/significant_experience_universalization/major_anecdote_as_data/seek_systematic_evidence)."""

EXPERIENCE_GENERALIZATION_PROMPT = """Detect experience generalization:

Claim: {claim}
Experience base: {experience}
Scope claimed: {scope}
Systematic evidence: {systematic}
Domain: {domain}
Context: {context}

Is limited personal experience being inappropriately generalized to universal claims? Return ONLY valid JSON."""


class ExperienceGeneralizationService:
    """Detects experience generalization — personal experience treated as universal."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        claim: str,
        *,
        experience: str = "",
        scope: str = "",
        systematic: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect experience generalization."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EXPERIENCE_GENERALIZATION_PROMPT.format(
                claim=claim,
                experience=experience or "Not specified",
                scope=scope or "Not specified",
                systematic=systematic or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EXPERIENCE_GENERALIZATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "claim": claim[:200],
            "generalization_present": data.get("generalization_present", False),
            "severity": data.get("severity", ""),
            "experience_base": data.get("experience_base", ""),
            "scope_claimed": data.get("scope_claimed", ""),
            "evidence_gap": data.get("evidence_gap", ""),
            "recommendation": data.get("recommendation", ""),
        }
