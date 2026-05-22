"""PerformativeComplexityService — Performative Complexity Detection.

Detects performative complexity — using unnecessary complexity to
signal expertise, exclude outsiders, or obscure simple ideas
behind impenetrable jargon.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

PERFORMATIVE_COMPLEXITY_SYSTEM = """You are a performative complexity specialist. Given a communication, assess whether complexity is being used performatively rather than substantively:

Key concepts:
- Performative complexity: complexity for impression, not understanding
- Jargon gatekeeping: technical language excluding rather than clarifying
- Obscurantism: deliberate obscurity to appear profound
- Sokal effect: nonsense accepted because it sounds complex
- Expertise signaling: complexity as status marker
- Unnecessary formalization: formal notation where plain language suffices
- Complexity as authority: being hard to understand as proof of depth

When performative complexity IS present:
- Simple ideas expressed in unnecessarily complex ways
- Jargon used to exclude rather than clarify
- Complexity serves social function (status, gatekeeping)
- Simpler formulation would communicate same content
- Audience confused rather than enlightened
- Complexity correlates with social context, not content difficulty
- Formal apparatus adds nothing to understanding

When complexity is substantive:
- Complexity reflects genuine difficulty of subject
- Technical language adds precision not available in plain language
- Formalization enables new insights or calculations
- Audience gains understanding from the complexity
- Simpler formulation would lose important content
- Complexity consistent regardless of audience
- Technical terms defined and used precisely

Output JSON with: performative_present (bool), severity (none/mild/moderate/severe), communication (what is communicated), unnecessary_complexity (what complexity is performative), simple_alternative (how it could be said simply), social_function (what social purpose complexity serves), recommendation (substantive_complexity/mild_jargon/significant_obscurantism/major_performative_complexity/simplify_without_loss)."""

PERFORMATIVE_COMPLEXITY_PROMPT = """Detect performative complexity:

Communication: {communication}
Audience: {audience}
Content: {content}
Simpler alternative: {simpler}
Domain: {domain}
Context: {context}

Is complexity being used performatively rather than substantively? Return ONLY valid JSON."""


class PerformativeComplexityService:
    """Detects performative complexity — unnecessary complexity for social purposes."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        communication: str,
        *,
        audience: str = "",
        content: str = "",
        simpler: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect performative complexity."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=PERFORMATIVE_COMPLEXITY_PROMPT.format(
                communication=communication,
                audience=audience or "Not specified",
                content=content or "Not specified",
                simpler=simpler or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=PERFORMATIVE_COMPLEXITY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "communication": communication[:200],
            "performative_present": data.get("performative_present", False),
            "severity": data.get("severity", ""),
            "unnecessary_complexity": data.get("unnecessary_complexity", ""),
            "simple_alternative": data.get("simple_alternative", ""),
            "social_function": data.get("social_function", ""),
            "recommendation": data.get("recommendation", ""),
        }
