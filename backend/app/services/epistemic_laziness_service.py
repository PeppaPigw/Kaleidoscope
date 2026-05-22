"""EpistemicLazinessService — Epistemic Laziness Detection.

Detects epistemic laziness — taking cognitive shortcuts when thorough
analysis is warranted, where effort avoidance compromises
epistemic quality.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_LAZINESS_SYSTEM = """You are an epistemic laziness specialist. Given a reasoning process, assess whether cognitive shortcuts are compromising quality:

Key concepts:
- Epistemic laziness: shortcuts when thoroughness is needed
- Cognitive effort avoidance: avoiding effortful thinking
- Premature satisfaction: accepting first plausible answer
- Depth avoidance: staying shallow when depth is needed
- Heuristic overreliance: using shortcuts for complex problems
- Satisficing inappropriately: good enough when best is needed
- Intellectual shortcuts: bypassing necessary reasoning steps

When epistemic laziness IS present:
- Cognitive shortcuts taken when thoroughness warranted
- First plausible answer accepted without verification
- Shallow analysis where depth is needed
- Heuristics used for problems requiring careful analysis
- Effort avoided despite high stakes
- Reasoning steps skipped
- Satisficing when optimization is needed

When efficiency is appropriate:
- Shortcuts proportionate to stakes
- Heuristics appropriate for problem type
- Satisficing when stakes are low
- Effort allocated by importance
- Depth proportionate to complexity
- Efficiency serving rather than compromising quality
- Shortcuts validated by experience

Output JSON with: laziness_present (bool), severity (none/mild/moderate/severe), reasoning (what reasoning is occurring), shortcuts_taken (what shortcuts are used), thoroughness_needed (what thoroughness is warranted), stakes (what is at stake), recommendation (appropriate_efficiency/mild_shortcutting/significant_epistemic_laziness/major_effort_avoidance/invest_cognitive_effort_proportionate_to_stakes)."""

EPISTEMIC_LAZINESS_PROMPT = """Detect epistemic laziness:

Reasoning process: {reasoning}
Shortcuts taken: {shortcuts}
Thoroughness warranted: {thoroughness}
Stakes: {stakes}
Domain: {domain}
Context: {context}

Are cognitive shortcuts compromising epistemic quality when thoroughness is warranted? Return ONLY valid JSON."""


class EpistemicLazinessService:
    """Detects epistemic laziness — shortcuts when thoroughness is warranted."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        reasoning: str,
        *,
        shortcuts: str = "",
        thoroughness: str = "",
        stakes: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic laziness."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_LAZINESS_PROMPT.format(
                reasoning=reasoning,
                shortcuts=shortcuts or "Not specified",
                thoroughness=thoroughness or "Not specified",
                stakes=stakes or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_LAZINESS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "reasoning": reasoning[:200],
            "laziness_present": data.get("laziness_present", False),
            "severity": data.get("severity", ""),
            "shortcuts_taken": data.get("shortcuts_taken", ""),
            "thoroughness_needed": data.get("thoroughness_needed", ""),
            "stakes": data.get("stakes", ""),
            "recommendation": data.get("recommendation", ""),
        }
