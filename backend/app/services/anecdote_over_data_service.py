"""AnecdoteOverDataService — Anecdote Over Data Detection.

Detects when vivid anecdotes override systematic data in
reasoning. Individual stories are compelling but may not
represent the broader pattern that data reveals.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

ANECDOTE_OVER_DATA_SYSTEM = """You are an anecdote-over-data specialist. Given reasoning, assess whether anecdotes are overriding systematic evidence:

Key concepts:
- Anecdote vs data: individual stories vs systematic evidence
- Vividness effect: vivid examples more persuasive than statistics
- Identifiable victim: one person's story more compelling than numbers
- Representativeness: anecdotes may not represent the population
- Base rate neglect: ignoring statistics in favor of stories
- Narrative persuasion: stories persuade more than data
- N=1 generalization: generalizing from single cases

When anecdote overrides data:
- Individual story used to dismiss statistical evidence
- "I know someone who..." overriding population data
- Vivid example treated as more informative than systematic study
- Policy based on compelling stories rather than evidence
- Single case generalized to population
- Data dismissed because of contradicting anecdote
- Emotional story overriding rational analysis

When anecdote and data are properly balanced:
- Anecdotes used to illustrate, not override, data
- Statistical evidence given appropriate weight
- Individual cases recognized as potentially unrepresentative
- Both stories and data inform the conclusion
- Anecdotes prompt investigation, not conclusion
- Data used for generalization, anecdotes for understanding
- Distinction made between illustration and evidence

Output JSON with: anecdote_override (bool), severity (none/mild/moderate/severe), anecdote (the story being used), data_available (what systematic evidence exists), conflict (where anecdote and data disagree), weight_given (how much weight anecdote receives), recommendation (proper_balance/mild_anecdote_preference/significant_data_override/major_story_over_evidence/weight_systematic_data)."""

ANECDOTE_OVER_DATA_PROMPT = """Detect anecdote over data:

Reasoning: {reasoning}
Anecdote used: {anecdote}
Data available: {data}
Conclusion: {conclusion}
Domain: {domain}
Context: {context}

Are vivid anecdotes overriding systematic data? Return ONLY valid JSON."""


class AnecdoteOverDataService:
    """Detects anecdote over data — stories overriding systematic evidence."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        reasoning: str,
        *,
        anecdote: str = "",
        data: str = "",
        conclusion: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect anecdote over data."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=ANECDOTE_OVER_DATA_PROMPT.format(
                reasoning=reasoning,
                anecdote=anecdote or "Not specified",
                data=data or "Not specified",
                conclusion=conclusion or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=ANECDOTE_OVER_DATA_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data_result = parse_llm_json(raw)

        return {
            "reasoning": reasoning[:200],
            "anecdote_override": data_result.get("anecdote_override", False),
            "severity": data_result.get("severity", ""),
            "conflict": data_result.get("conflict", ""),
            "weight_given": data_result.get("weight_given", ""),
            "data_available": data_result.get("data_available", ""),
            "recommendation": data_result.get("recommendation", ""),
        }
