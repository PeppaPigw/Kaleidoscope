"""EtymologicalFallacyService — Etymological Fallacy Detection.

Detects etymological fallacy — arguing that a word's current meaning
must be determined by or is constrained by its historical etymology,
ignoring that language evolves and words acquire new meanings through use.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

ETYMOLOGICAL_SYSTEM = """You are an etymological fallacy specialist. Given an argument about meaning, assess whether it commits the etymological fallacy — insisting current meaning must match historical etymology:

Key concepts:
- Etymological fallacy: current meaning must equal original meaning
- Semantic drift: words change meaning over time
- Prescriptivism vs descriptivism: how language should vs does work
- Living language: meaning is determined by current usage
- False precision: using etymology to artificially narrow meaning
- Equivocation: switching between historical and current meanings
- Stipulative definition: defining terms for argument rather than accuracy

When etymological fallacy IS present:
- "Literally means X because it comes from Latin Y"
- Using original meaning to invalidate current usage
- "The word 'nice' originally meant 'ignorant', so..."
- Insisting on etymological meaning against established usage
- "Democracy means 'rule by the people' so any deviation isn't democracy"
- Using word origins to win definitional arguments
- Treating etymology as prescriptive rather than descriptive

When etymology IS relevant:
- Tracing how a concept has evolved to understand it better
- Identifying when a word is being used in a genuinely confusing way
- Historical linguistics as academic study
- Understanding technical terms in their original context
- Identifying genuine equivocation between distinct meanings
- Clarifying ambiguity by reference to distinct historical senses
- The argument is about historical meaning, not current usage

Output JSON with: etymological_fallacy_present (bool), severity (none/mild/moderate/severe), word (what word or term), etymology_cited (what historical meaning is invoked), current_usage (how the word is currently used), semantic_drift (has meaning changed), argument_purpose (why etymology is being cited), recommendation (etymology_relevant/mild_prescriptivism/significant_etymological_fallacy/major_meaning_conflation/use_current_meaning)."""

ETYMOLOGICAL_PROMPT = """Detect etymological fallacy:

Argument: {argument}
Word/term: {word}
Etymology cited: {etymology}
Current usage: {current_usage}
Domain: {domain}
Context: {context}

Is this argument insisting that current meaning must match historical etymology? Return ONLY valid JSON."""


class EtymologicalFallacyService:
    """Detects etymological fallacy — insisting current meaning must match etymology."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        argument: str,
        *,
        word: str = "",
        etymology: str = "",
        current_usage: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect etymological fallacy."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=ETYMOLOGICAL_PROMPT.format(
                argument=argument,
                word=word or "Not specified",
                etymology=etymology or "Not specified",
                current_usage=current_usage or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=ETYMOLOGICAL_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "argument": argument[:200],
            "etymological_fallacy_present": data.get("etymological_fallacy_present", False),
            "severity": data.get("severity", ""),
            "word": data.get("word", ""),
            "etymology_cited": data.get("etymology_cited", ""),
            "current_usage": data.get("current_usage", ""),
            "semantic_drift": data.get("semantic_drift", ""),
            "recommendation": data.get("recommendation", ""),
        }
