"""GeneticFallacyService — Genetic Fallacy Detection.

Detects genetic fallacy — judging something as good or bad based on
where it comes from (its origin or source) rather than evaluating it
on its current merits, evidence, or logical validity.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

GENETIC_FALLACY_SYSTEM = """You are a genetic fallacy specialist. Given an argument, assess whether it commits the genetic fallacy — evaluating a claim based on its origin rather than its merits:

Key concepts:
- Genetic fallacy: judging truth/value by origin rather than current merit
- Source confusion: conflating where something came from with what it is
- Ad hominem variant: rejecting argument because of who made it
- Appeal to authority variant: accepting argument because of who made it
- Historical origin: "it started as X, therefore it still is X"
- Guilt by association: rejecting ideas because of who else holds them
- Poisoning the well: discrediting source to discredit the argument

When genetic fallacy IS present:
- "That idea came from X, so it must be wrong/right"
- Rejecting evidence because of who funded the study
- "That word originally meant X, so it still means X"
- Dismissing an argument because of its historical origins
- "They only believe that because of their background"
- Accepting a claim solely because of its prestigious source
- Evaluating a policy by who proposed it rather than its effects

When origin IS relevant:
- Source reliability is genuinely at issue (credibility assessment)
- The origin reveals a conflict of interest that affects reliability
- Historical context is needed to understand current meaning
- The argument explicitly depends on the authority of its source
- Provenance is part of the evidence (e.g., chain of custody)
- The origin reveals systematic bias in methodology
- Source evaluation is one factor among many, not the sole basis

Output JSON with: genetic_fallacy_present (bool), severity (none/mild/moderate/severe), claim (what is being evaluated), origin (what origin is cited), merit_evaluation (is the claim evaluated on merits), relevance (is the origin actually relevant), conflation (how origin and merit are confused), recommendation (merit_based/mild_origin_focus/significant_genetic_fallacy/major_source_conflation/evaluate_on_current_merits)."""

GENETIC_FALLACY_PROMPT = """Detect genetic fallacy:

Claim: {claim}
Origin cited: {origin}
Merit evaluation: {merit}
Relevance: {relevance}
Domain: {domain}
Context: {context}

Is this claim being judged by its origin rather than its current merits? Return ONLY valid JSON."""


class GeneticFallacyService:
    """Detects genetic fallacy — judging claims by origin rather than merit."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        claim: str,
        *,
        origin: str = "",
        merit: str = "",
        relevance: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect genetic fallacy."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=GENETIC_FALLACY_PROMPT.format(
                claim=claim,
                origin=origin or "Not specified",
                merit=merit or "Not specified",
                relevance=relevance or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=GENETIC_FALLACY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "claim": claim[:200],
            "genetic_fallacy_present": data.get("genetic_fallacy_present", False),
            "severity": data.get("severity", ""),
            "origin": data.get("origin", ""),
            "merit_evaluation": data.get("merit_evaluation", ""),
            "relevance": data.get("relevance", ""),
            "conflation": data.get("conflation", ""),
            "recommendation": data.get("recommendation", ""),
        }
