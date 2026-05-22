"""MotivatedComplexityService — Motivated Complexity Detection.

Detects motivated complexity — making things complex to avoid simple
but uncomfortable truths, where unnecessary complexity serves
as a defense against clear but unwelcome conclusions.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

MOTIVATED_COMPLEXITY_SYSTEM = """You are a motivated complexity specialist. Given an analysis, assess whether complexity is being introduced to avoid simple uncomfortable truths:

Key concepts:
- Motivated complexity: complexity to avoid uncomfortable simplicity
- Obfuscation through complexity: hiding simple truth in complexity
- Complexity as defense: unnecessary complexity protecting beliefs
- Simple truth avoidance: avoiding clear but unwelcome conclusions
- Intellectual smoke screen: complexity obscuring obvious answers
- Nuance weaponization: false nuance preventing clear conclusions
- Overthinking as avoidance: excessive analysis avoiding obvious

When motivated complexity IS present:
- Complexity introduced to avoid simple conclusion
- Unnecessary nuance preventing clear answer
- Obvious truth obscured by elaborate analysis
- Complexity serving avoidance not understanding
- Simple uncomfortable truth available but rejected
- Intellectual sophistication masking avoidance
- Overthinking substituting for accepting obvious

When genuine complexity is appropriate:
- Complexity reflects actual complexity of situation
- Nuance genuinely warranted by evidence
- Simple answers genuinely inadequate
- Complexity serving understanding not avoidance
- Elaborate analysis revealing genuine subtlety
- Intellectual depth discovering non-obvious truths
- Thorough analysis finding genuine complications

Output JSON with: motivated_complexity_present (bool), severity (none/mild/moderate/severe), analysis (what analysis is occurring), complexity_introduced (what complexity is added), simple_truth (what simple truth is avoided), motivation (why complexity is preferred), recommendation (genuine_complexity/mild_overcomplication/significant_motivated_complexity/major_truth_avoidance/accept_simple_truth_when_warranted)."""

MOTIVATED_COMPLEXITY_PROMPT = """Detect motivated complexity:

Analysis: {analysis}
Complexity introduced: {complexity}
Simple alternative: {simple}
Motivation: {motivation}
Domain: {domain}
Context: {context}

Is complexity being introduced to avoid simple but uncomfortable truths? Return ONLY valid JSON."""


class MotivatedComplexityService:
    """Detects motivated complexity — complexity to avoid uncomfortable simplicity."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        analysis: str,
        *,
        complexity: str = "",
        simple: str = "",
        motivation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect motivated complexity."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=MOTIVATED_COMPLEXITY_PROMPT.format(
                analysis=analysis,
                complexity=complexity or "Not specified",
                simple=simple or "Not specified",
                motivation=motivation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=MOTIVATED_COMPLEXITY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "analysis": analysis[:200],
            "motivated_complexity_present": data.get("motivated_complexity_present", False),
            "severity": data.get("severity", ""),
            "complexity_introduced": data.get("complexity_introduced", ""),
            "simple_truth": data.get("simple_truth", ""),
            "motivation": data.get("motivation", ""),
            "recommendation": data.get("recommendation", ""),
        }
