"""CompletenessIllusionService — Completeness Illusion Detection.

Detects completeness illusion — preferring complete-seeming explanations
over honest incompleteness, mistaking coverage for accuracy.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

COMPLETENESS_ILLUSION_SYSTEM = """You are a completeness illusion specialist. Given an explanation, assess whether apparent completeness is being mistaken for accuracy:

Key concepts:
- Completeness illusion: mistaking complete-seeming for accurate
- Coverage over accuracy: preferring coverage over correctness
- Gap-filling fabrication: filling gaps with fabrication for completeness
- Pseudo-completeness: appearing complete while actually incomplete
- Honest incompleteness rejection: rejecting honest admission of gaps
- Totality preference: preferring total explanations over partial truths
- Closure need: needing closure driving false completeness

When completeness illusion IS present:
- Complete-seeming explanation preferred over honest incompleteness
- Coverage mistaken for accuracy
- Gaps filled with fabrication to appear complete
- Pseudo-completeness preferred over partial truth
- Honest admission of gaps rejected
- Total explanation preferred over accurate partial one
- Need for closure driving false completeness

When appropriate completeness is present:
- Completeness reflecting genuine understanding
- Coverage proportionate to actual knowledge
- Gaps honestly acknowledged
- Completeness earned through evidence
- Partial knowledge honestly presented
- Totality claims supported by evidence
- Closure appropriate to evidence state

Output JSON with: illusion_present (bool), severity (none/mild/moderate/severe), explanation (what explanation is offered), apparent_completeness (what makes it seem complete), actual_gaps (what gaps exist), honest_alternative (what honest incomplete version would be), recommendation (appropriate_completeness/mild_gap_filling/significant_completeness_illusion/major_pseudo_completeness/acknowledge_honest_gaps)."""

COMPLETENESS_ILLUSION_PROMPT = """Detect completeness illusion:

Explanation: {explanation}
Apparent completeness: {completeness}
Actual gaps: {gaps}
Honest alternative: {alternative}
Domain: {domain}
Context: {context}

Is apparent completeness being mistaken for accuracy? Return ONLY valid JSON."""


class CompletenessIllusionService:
    """Detects completeness illusion — mistaking complete-seeming for accurate."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        explanation: str,
        *,
        completeness: str = "",
        gaps: str = "",
        alternative: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect completeness illusion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=COMPLETENESS_ILLUSION_PROMPT.format(
                explanation=explanation,
                completeness=completeness or "Not specified",
                gaps=gaps or "Not specified",
                alternative=alternative or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=COMPLETENESS_ILLUSION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "explanation": explanation[:200],
            "illusion_present": data.get("illusion_present", False),
            "severity": data.get("severity", ""),
            "apparent_completeness": data.get("apparent_completeness", ""),
            "actual_gaps": data.get("actual_gaps", ""),
            "honest_alternative": data.get("honest_alternative", ""),
            "recommendation": data.get("recommendation", ""),
        }
