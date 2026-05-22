"""DoubleIllusionTransparencyService — Double Illusion of Transparency Detection.

Detects double illusion of transparency — both parties in a
communication believing the other understands their position when
neither actually does. Each side thinks they've been clear and that
the other's failure to agree must be due to bad faith rather than
genuine misunderstanding.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

DOUBLE_ILLUSION_SYSTEM = """You are a double illusion of transparency specialist. Given a disagreement, assess whether both parties mistakenly believe the other understands their position:

Key concepts:
- Double illusion of transparency: both sides think they're understood
- Illusion of transparency: overestimating how well others understand you
- Curse of knowledge overlap: can't imagine not knowing what you know
- Bad faith attribution: "they understand but disagree anyway"
- Communication failure: mistaking disagreement for understanding
- Inferential distance: gap between what's said and what's understood
- Typical mind overlap: assuming others process information like you do

When double illusion IS present:
- Both parties say "I've explained this clearly" but neither feels understood
- Disagreement attributed to bad faith rather than misunderstanding
- Each side can't articulate the other's position accurately
- "They know what I mean" when they demonstrably don't
- Frustration on both sides that the other "won't listen"
- Repeated explanations without checking comprehension
- Each side's summary of the other's position would be rejected by the other

When understanding IS genuine:
- Each party can articulate the other's position to their satisfaction
- Disagreement persists after confirmed mutual understanding
- Both parties have verified comprehension, not just assumed it
- The disagreement is about values or priorities, not facts
- Paraphrasing has been used and confirmed
- Both parties acknowledge what they find compelling in the other's view
- The communication has been tested for understanding

Output JSON with: double_illusion_present (bool), severity (none/mild/moderate/severe), disagreement (what is being disagreed about), party_a_understanding (does A understand B), party_b_understanding (does B understand A), bad_faith_attribution (is misunderstanding attributed to bad faith), verification (has understanding been verified), recommendation (understanding_genuine/mild_miscommunication/significant_double_illusion/major_mutual_misunderstanding/verify_comprehension_before_attributing_bad_faith)."""

DOUBLE_ILLUSION_PROMPT = """Detect double illusion of transparency:

Disagreement: {disagreement}
Party A's view: {party_a}
Party B's view: {party_b}
Attribution: {attribution}
Domain: {domain}
Context: {context}

Do both parties mistakenly believe the other understands their position? Return ONLY valid JSON."""


class DoubleIllusionTransparencyService:
    """Detects double illusion of transparency — mutual misunderstanding."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        disagreement: str,
        *,
        party_a: str = "",
        party_b: str = "",
        attribution: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect double illusion of transparency."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=DOUBLE_ILLUSION_PROMPT.format(
                disagreement=disagreement,
                party_a=party_a or "Not specified",
                party_b=party_b or "Not specified",
                attribution=attribution or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=DOUBLE_ILLUSION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "disagreement": disagreement[:200],
            "double_illusion_present": data.get("double_illusion_present", False),
            "severity": data.get("severity", ""),
            "party_a_understanding": data.get("party_a_understanding", ""),
            "party_b_understanding": data.get("party_b_understanding", ""),
            "bad_faith_attribution": data.get("bad_faith_attribution", ""),
            "verification": data.get("verification", ""),
            "recommendation": data.get("recommendation", ""),
        }
