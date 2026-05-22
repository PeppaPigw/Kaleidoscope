"""GeneticOriginFallacyService — Genetic Origin Fallacy Detection.

Detects genetic origin fallacy — judging an idea, argument, or
proposal based on its source or origin rather than its current
merits. Distinct from the existing genetic_fallacy tool by
focusing specifically on origin-based dismissal in organizational
and intellectual contexts.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

GENETIC_ORIGIN_SYSTEM = """You are a genetic origin fallacy specialist. Given an evaluation of an idea, assess whether it's being judged by its source rather than its merits:

Key concepts:
- Genetic fallacy: judging by origin rather than current merit
- Source bias: accepting/rejecting based on who said it
- NIH syndrome: "Not Invented Here" — rejecting external ideas
- Authority transfer: accepting because of prestigious source
- Poisoning the well: preemptive source-based dismissal
- Ad hominem variant: dismissing ideas because of their proponent
- Idea laundering: the same idea accepted when from a different source

When genetic origin fallacy IS present:
- "That idea came from [disliked source], so it must be bad"
- Rejecting a proposal because of who suggested it
- "We can't use that — it came from our competitors"
- Accepting an idea uncritically because it came from a prestigious source
- "That's a [political group] idea" as if that settles its merit
- NIH syndrome: rejecting external solutions for being external
- Dismissing research because of the institution that produced it

When genetic origin fallacy is NOT present:
- Source is relevant to credibility (track record, expertise)
- The evaluation engages with the idea's merits AND notes the source
- Source bias is one factor among many in evaluation
- The origin provides relevant context (conflicts of interest)
- The idea is evaluated on its own terms after noting the source
- Source credibility is used as a Bayesian prior, not a verdict
- The same evaluation would apply regardless of source

Output JSON with: genetic_origin_present (bool), severity (none/mild/moderate/severe), idea (what idea is being evaluated), source (what origin is cited), merit_evaluation (is the idea evaluated on merits), source_relevance (is the source genuinely relevant), recommendation (no_genetic_origin/mild_source_bias/significant_genetic_origin/major_source_based_dismissal/evaluate_on_merits)."""

GENETIC_ORIGIN_PROMPT = """Detect genetic origin fallacy:

Evaluation: {evaluation}
Idea: {idea}
Source: {source}
Merit discussion: {merit}
Domain: {domain}
Context: {context}

Is this idea being judged by its source rather than its merits? Return ONLY valid JSON."""


class GeneticOriginFallacyService:
    """Detects genetic origin fallacy — judging ideas by source, not merit."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        evaluation: str,
        *,
        idea: str = "",
        source: str = "",
        merit: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect genetic origin fallacy."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=GENETIC_ORIGIN_PROMPT.format(
                evaluation=evaluation,
                idea=idea or "Not specified",
                source=source or "Not specified",
                merit=merit or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=GENETIC_ORIGIN_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "evaluation": evaluation[:200],
            "genetic_origin_present": data.get("genetic_origin_present", False),
            "severity": data.get("severity", ""),
            "idea": data.get("idea", ""),
            "source": data.get("source", ""),
            "source_relevance": data.get("source_relevance", ""),
            "recommendation": data.get("recommendation", ""),
        }
