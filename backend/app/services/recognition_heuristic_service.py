"""RecognitionHeuristicService — Recognition Heuristic Detection.

Detects recognition heuristic — inferring that recognized
objects have higher value on a criterion than unrecognized
ones. Goldstein & Gigerenzer (2002). "I've heard of it,
so it must be better/bigger/more important." Works well
in some environments but fails when recognition is driven
by irrelevant factors (advertising, media coverage).
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

RECOGNITION_HEURISTIC_SYSTEM = """You are a recognition heuristic specialist. Given a judgment based on familiarity, assess whether recognition is being appropriately used as a cue:

Key concepts (Goldstein & Gigerenzer, 2002):
- Recognition heuristic: recognized > unrecognized on criterion
- Ecological rationality: works when recognition correlates with criterion
- Less-is-more effect: partial knowledge can outperform full knowledge
- Recognition validity: correlation between recognition and criterion
- Advertising effect: recognition from marketing ≠ quality
- Media bias: recognition from coverage ≠ importance
- Brand recognition: familiarity ≠ superiority

When recognition heuristic IS problematic:
- Choosing recognized brands over better unknown alternatives
- "I've heard of them, so they must be good"
- Judging importance by media coverage/familiarity
- Investing in recognized companies without analysis
- Hiring from recognized schools over better candidates
- "Never heard of it" as reason to dismiss
- Recognition from advertising treated as quality signal

When recognition IS a valid cue:
- Recognition genuinely correlates with the criterion
- The recognition comes from relevant experience
- The environment rewards recognized options (network effects)
- The person uses recognition as one input among many
- Recognition reflects genuine quality signals

Output JSON with: recognition_heuristic_present (bool), severity (none/mild/moderate/severe), judgment (what judgment is being made), recognized (what is recognized), unrecognized (what is not recognized), recognition_source (why is it recognized), recognition_validity (does recognition correlate with the criterion), criterion (what is being judged), recommendation (recognition_valid/mild_familiarity_bias/significant_recognition_reliance/major_recognition_heuristic/evaluate_beyond_recognition)."""

RECOGNITION_HEURISTIC_PROMPT = """Detect recognition heuristic:

Judgment: {judgment}
Recognized option: {recognized}
Alternative: {alternative}
Recognition source: {source}
Domain: {domain}
Context: {context}

Is recognition being inappropriately used as a quality signal? Return ONLY valid JSON."""


class RecognitionHeuristicService:
    """Detects recognition heuristic — familiarity misused as quality signal."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        judgment: str,
        *,
        recognized: str = "",
        alternative: str = "",
        source: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect recognition heuristic."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=RECOGNITION_HEURISTIC_PROMPT.format(
                judgment=judgment,
                recognized=recognized or "Not specified",
                alternative=alternative or "Not specified",
                source=source or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=RECOGNITION_HEURISTIC_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "judgment": judgment[:200],
            "recognition_heuristic_present": data.get("recognition_heuristic_present", False),
            "severity": data.get("severity", ""),
            "recognition_source": data.get("recognition_source", ""),
            "recognition_validity": data.get("recognition_validity", ""),
            "criterion": data.get("criterion", ""),
            "recommendation": data.get("recommendation", ""),
        }
