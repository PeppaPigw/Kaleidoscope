"""FallacyOfGrayService — Fallacy of Gray Detection.

Detects the fallacy of gray — arguing that because nothing is
perfectly black or white, all grays are the same shade. "Nothing
is perfectly certain, so we can't know anything." "No solution
is perfect, so all solutions are equally good/bad." Treating a
spectrum as if differences in degree don't matter.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

FALLACY_OF_GRAY_SYSTEM = """You are a fallacy of gray specialist. Given an argument about degrees or spectra, assess whether differences in degree are being inappropriately dismissed:

Key concepts (Yudkowsky, 2008):
- Fallacy of gray: all grays are the same shade
- Continuum fallacy: no sharp boundary → no real difference
- Degree denial: "nothing is perfect, so nothing matters"
- False equivalence via spectrum: "both have flaws, so they're equal"
- Nirvana fallacy interaction: "not perfect" → "not worth doing"
- Sorites paradox abuse: using heap paradox to deny all distinctions
- Quantitative blindness: ignoring magnitude of differences

When fallacy of gray IS present:
- "All politicians lie, so they're all the same"
- "No energy source is perfectly clean, so why bother"
- "Everyone is biased, so no one's opinion matters more"
- "Nothing is 100% safe, so safety regulations are pointless"
- "All models are wrong" used to dismiss all modeling
- "Both sides have problems" to equate very different problems
- Using imperfection to justify inaction or false equivalence

When degree-based reasoning IS appropriate:
- Genuine cases where the difference in degree is negligible
- Acknowledging a spectrum while still making meaningful distinctions
- The argument is about whether a threshold has been crossed
- Differences in degree are quantified and shown to be small
- The spectrum is acknowledged but meaningful distinctions are preserved

Output JSON with: fallacy_of_gray_present (bool), severity (none/mild/moderate/severe), argument (what argument is being made), spectrum (what spectrum is being referenced), distinction_denied (what meaningful distinction is being erased), actual_difference (what is the actual magnitude of difference), equivalence_claimed (what false equivalence results), consequences (how does this affect decisions), recommendation (degree_argument_valid/mild_gray_flattening/significant_fallacy_of_gray/major_distinction_erasure/preserve_meaningful_distinctions)."""

FALLACY_OF_GRAY_PROMPT = """Detect fallacy of gray:

Argument: {argument}
Spectrum: {spectrum}
Distinction: {distinction}
Magnitude: {magnitude}
Domain: {domain}
Context: {context}

Are differences in degree being inappropriately dismissed because nothing is perfectly black or white? Return ONLY valid JSON."""


class FallacyOfGrayService:
    """Detects fallacy of gray — treating all shades of gray as equal."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        argument: str,
        *,
        spectrum: str = "",
        distinction: str = "",
        magnitude: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect fallacy of gray."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=FALLACY_OF_GRAY_PROMPT.format(
                argument=argument,
                spectrum=spectrum or "Not specified",
                distinction=distinction or "Not specified",
                magnitude=magnitude or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=FALLACY_OF_GRAY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "argument": argument[:200],
            "fallacy_of_gray_present": data.get("fallacy_of_gray_present", False),
            "severity": data.get("severity", ""),
            "spectrum": data.get("spectrum", ""),
            "distinction_denied": data.get("distinction_denied", ""),
            "actual_difference": data.get("actual_difference", ""),
            "equivalence_claimed": data.get("equivalence_claimed", ""),
            "consequences": data.get("consequences", ""),
            "recommendation": data.get("recommendation", ""),
        }
