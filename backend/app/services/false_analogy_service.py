"""FalseAnalogyService — False Analogy Detection.

Detects false analogy — comparing things that are superficially
similar but fundamentally different in ways relevant to the
conclusion being drawn. The analogy breaks down when examined
more closely.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

FALSE_ANALOGY_SYSTEM = """You are a false analogy specialist. Given a comparison used as argument, assess whether the analogy holds in relevant respects:

Key concepts:
- False analogy: comparison that breaks down in relevant ways
- Relevant similarity: do the things share the features that matter?
- Disanalogy: ways in which the compared things differ
- Structural similarity: deep vs superficial resemblance
- Analogical reasoning: legitimate when similarities are relevant
- Overextension: pushing an analogy beyond its valid scope
- Model limitations: all analogies break down somewhere

When false analogy IS present:
- The compared things differ in ways relevant to the conclusion
- Superficial similarity masks fundamental differences
- The analogy is used to prove rather than illustrate
- Key structural differences are ignored
- "X is like Y, therefore X has property Z" when the similarity doesn't extend to Z
- The analogy breaks down exactly where it needs to hold
- Emotional resonance of the analogy substitutes for logical validity

When false analogy is NOT present:
- The similarity is in features relevant to the conclusion
- The analogy is used to illustrate, not prove
- Limitations of the analogy are acknowledged
- Structural similarities are genuine and relevant
- The conclusion follows from the shared features
- Disanalogies are addressed and shown to be irrelevant
- The analogy is one piece of evidence among many

Output JSON with: false_analogy_present (bool), severity (none/mild/moderate/severe), analogy (what is compared to what), similarities (genuine shared features), disanalogies (relevant differences), conclusion_drawn (what is concluded from the analogy), breakdown_point (where the analogy fails), recommendation (no_false_analogy/mild_overextension/significant_false_analogy/major_disanalogy/acknowledge_differences)."""

FALSE_ANALOGY_PROMPT = """Detect false analogy:

Argument: {argument}
Thing compared: {thing_a}
Compared to: {thing_b}
Conclusion drawn: {conclusion}
Domain: {domain}
Context: {context}

Does this analogy break down in ways relevant to the conclusion? Return ONLY valid JSON."""


class FalseAnalogyService:
    """Detects false analogy — comparisons that break down in relevant ways."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        argument: str,
        *,
        thing_a: str = "",
        thing_b: str = "",
        conclusion: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect false analogy."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=FALSE_ANALOGY_PROMPT.format(
                argument=argument,
                thing_a=thing_a or "Not specified",
                thing_b=thing_b or "Not specified",
                conclusion=conclusion or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=FALSE_ANALOGY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "argument": argument[:200],
            "false_analogy_present": data.get("false_analogy_present", False),
            "severity": data.get("severity", ""),
            "analogy": data.get("analogy", ""),
            "disanalogies": data.get("disanalogies", ""),
            "breakdown_point": data.get("breakdown_point", ""),
            "recommendation": data.get("recommendation", ""),
        }
