"""BikesheddingService — Bikeshedding Detection.

Detects bikeshedding (Parkinson's law of triviality) — spending
disproportionate time and energy on trivial, easy-to-understand
issues while neglecting complex, important ones. Named after the
observation that committees spend more time on a bike shed than
a nuclear reactor because everyone can have an opinion on paint color.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

BIKESHEDDING_SYSTEM = """You are a bikeshedding specialist. Given a discussion or decision process, assess whether disproportionate attention is being given to trivial matters:

Key concepts:
- Bikeshedding: excessive focus on trivial details
- Parkinson's law of triviality: time spent inversely proportional to importance
- Accessibility bias: easy topics get more discussion
- Competence display: people discuss what they understand
- Avoidance behavior: trivial topics as escape from hard decisions
- Proportionality: effort should match importance
- Opportunity cost: time on trivia = time not on substance

When bikeshedding IS present:
- Hours debating naming conventions while architecture is undecided
- Extensive discussion of UI colors while security vulnerabilities exist
- Meeting time consumed by formatting preferences
- Detailed review of trivial code while critical logic is rubber-stamped
- Everyone has opinions on the easy part, silence on the hard part
- Disproportionate energy on reversible, low-impact decisions
- Avoiding the hard conversation by focusing on the easy one

When bikeshedding is NOT present:
- Time allocation is proportional to importance and impact
- Trivial matters are decided quickly and moved past
- Complex issues receive appropriate depth of discussion
- The "trivial" issue actually has hidden complexity or impact
- Naming/formatting discussions are brief and decisive
- The team explicitly prioritizes high-impact items
- Easy decisions are used as warm-up, not as avoidance

Output JSON with: bikeshedding_present (bool), severity (none/mild/moderate/severe), trivial_topic (what trivial matter gets attention), important_topic (what important matter is neglected), time_ratio (how disproportionate is the allocation), cause (why is this happening), recommendation (no_bikeshedding/mild_disproportion/significant_bikeshedding/major_avoidance/refocus_on_priorities)."""

BIKESHEDDING_PROMPT = """Detect bikeshedding:

Discussion: {discussion}
Topic focus: {topic_focus}
Important issues: {important_issues}
Time spent: {time_spent}
Domain: {domain}
Context: {context}

Is disproportionate attention being given to trivial matters while important ones are neglected? Return ONLY valid JSON."""


class BikesheddingService:
    """Detects bikeshedding — disproportionate focus on trivial matters."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        discussion: str,
        *,
        topic_focus: str = "",
        important_issues: str = "",
        time_spent: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect bikeshedding."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=BIKESHEDDING_PROMPT.format(
                discussion=discussion,
                topic_focus=topic_focus or "Not specified",
                important_issues=important_issues or "Not specified",
                time_spent=time_spent or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=BIKESHEDDING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "discussion": discussion[:200],
            "bikeshedding_present": data.get("bikeshedding_present", False),
            "severity": data.get("severity", ""),
            "trivial_topic": data.get("trivial_topic", ""),
            "important_topic": data.get("important_topic", ""),
            "time_ratio": data.get("time_ratio", ""),
            "recommendation": data.get("recommendation", ""),
        }
