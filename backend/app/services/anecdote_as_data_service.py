"""AnecdoteAsDataService — Anecdote as Data Detection.

Detects anecdote-as-data reasoning — treating individual stories,
personal experiences, or isolated examples as if they constitute
statistical evidence. "The plural of anecdote is not data."
Individual cases can illustrate but cannot establish patterns.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

ANECDOTE_AS_DATA_SYSTEM = """You are an anecdote-as-data specialist. Given a claim and its support, assess whether individual stories are being treated as statistical evidence:

Key concepts:
- Anecdote as data: treating stories as statistics
- Plural of anecdote: many stories still aren't data
- Identifiable victim effect: stories are more compelling than statistics
- Narrative vs. statistical evidence: different epistemic weight
- Availability heuristic overlap: memorable stories seem more common
- Survivorship bias overlap: we hear from survivors, not failures
- Base rate neglect: stories don't tell you how common something is

When anecdote-as-data IS present:
- Personal stories used to establish frequency or probability
- "I know someone who..." as evidence for how common something is
- Individual cases treated as representative without verification
- Testimonials used instead of systematic evidence
- Stories selected for emotional impact rather than representativeness
- "It happened to me, so it must be common"
- Rejecting statistics because of a contradicting personal story

When anecdotes ARE appropriate evidence:
- Used to illustrate a pattern already established by data
- Presented as existence proofs ("it's possible") not frequency claims
- The claim is about individual experience, not population patterns
- Anecdotes are explicitly acknowledged as non-systematic
- They generate hypotheses rather than confirm them
- The context is qualitative research with appropriate methods
- Stories complement rather than replace statistical evidence

Output JSON with: anecdote_as_data_present (bool), severity (none/mild/moderate/severe), claim (what is being claimed), evidence_type (what kind of evidence is offered), statistical_alternative (what systematic evidence would be needed), frequency_claim (is a frequency/probability being implied), appropriate_use (would anecdotes be appropriate here), recommendation (anecdote_appropriate/mild_overweight/significant_anecdote_as_data/major_story_as_statistics/seek_systematic_evidence)."""

ANECDOTE_AS_DATA_PROMPT = """Detect anecdote as data:

Claim: {claim}
Evidence: {evidence}
Type: {evidence_type}
Frequency implied: {frequency}
Domain: {domain}
Context: {context}

Are individual stories being treated as statistical evidence? Return ONLY valid JSON."""


class AnecdoteAsDataService:
    """Detects anecdote-as-data — treating stories as statistics."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        claim: str,
        *,
        evidence: str = "",
        evidence_type: str = "",
        frequency: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect anecdote as data."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=ANECDOTE_AS_DATA_PROMPT.format(
                claim=claim,
                evidence=evidence or "Not specified",
                evidence_type=evidence_type or "Not specified",
                frequency=frequency or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=ANECDOTE_AS_DATA_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "claim": claim[:200],
            "anecdote_as_data_present": data.get("anecdote_as_data_present", False),
            "severity": data.get("severity", ""),
            "evidence_type": data.get("evidence_type", ""),
            "statistical_alternative": data.get("statistical_alternative", ""),
            "frequency_claim": data.get("frequency_claim", ""),
            "recommendation": data.get("recommendation", ""),
        }
