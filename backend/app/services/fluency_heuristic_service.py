"""FluencyHeuristicService — Fluency Heuristic Detection.

Detects fluency heuristic — judging things that are processed
more easily (fluently) as more true, more familiar, more
likeable, or more valuable. Reber & Schwarz (1999).
Easy-to-read = true. Easy-to-pronounce = safe. Easy-to-
process = good. Processing ease is misattributed to the
content rather than the presentation.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

FLUENCY_HEURISTIC_SYSTEM = """You are a fluency heuristic specialist. Given a judgment or preference, assess whether processing ease is being misattributed to content quality:

Key concepts (Reber & Schwarz, 1999):
- Processing fluency: ease of mental processing
- Perceptual fluency: ease of perceiving (clear fonts, high contrast)
- Conceptual fluency: ease of understanding (familiar concepts)
- Fluency-truth link: easy to process → feels true
- Fluency-liking link: easy to process → feels pleasant
- Fluency-familiarity link: easy to process → feels known
- Misattribution: attributing fluency feelings to content properties

When fluency heuristic IS present:
- Judging clearly presented information as more true
- Preferring easy-to-pronounce options (stocks, brands)
- Trusting simple explanations over complex-but-accurate ones
- "It just feels right" based on processing ease
- Rhyming statements judged as more true
- Familiar-sounding claims accepted without scrutiny
- Rejecting valid arguments because they're hard to follow

When the judgment IS appropriate:
- Simplicity genuinely correlates with truth in the domain
- The person evaluates content independently of presentation
- Fluency reflects genuine familiarity with valid information
- The preference for clarity is about communication, not truth
- The person distinguishes ease of processing from accuracy

Output JSON with: fluency_heuristic_present (bool), severity (none/mild/moderate/severe), judgment (what judgment is being made), fluency_source (what makes it easy to process), content_quality (what is the actual quality of the content), misattribution (what is being misattributed to fluency), presentation_vs_substance (is presentation driving the judgment), recommendation (judgment_appropriate/mild_fluency_bias/significant_misattribution/major_fluency_heuristic/evaluate_content_independently)."""

FLUENCY_HEURISTIC_PROMPT = """Detect fluency heuristic:

Judgment: {judgment}
Presentation: {presentation}
Content: {content}
Alternatives: {alternatives}
Domain: {domain}
Context: {context}

Is processing ease being misattributed to content quality? Return ONLY valid JSON."""


class FluencyHeuristicService:
    """Detects fluency heuristic — processing ease misattributed to content quality."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        judgment: str,
        *,
        presentation: str = "",
        content: str = "",
        alternatives: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect fluency heuristic."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=FLUENCY_HEURISTIC_PROMPT.format(
                judgment=judgment,
                presentation=presentation or "Not specified",
                content=content or "Not specified",
                alternatives=alternatives or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=FLUENCY_HEURISTIC_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "judgment": judgment[:200],
            "fluency_heuristic_present": data.get("fluency_heuristic_present", False),
            "severity": data.get("severity", ""),
            "fluency_source": data.get("fluency_source", ""),
            "content_quality": data.get("content_quality", ""),
            "misattribution": data.get("misattribution", ""),
            "presentation_vs_substance": data.get("presentation_vs_substance", ""),
            "recommendation": data.get("recommendation", ""),
        }
