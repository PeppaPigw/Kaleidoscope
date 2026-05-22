"""ToxoplasmaOfRageService — Toxoplasma of Rage Detection.

Detects the toxoplasma of rage pattern — controversial topics
getting disproportionate attention precisely because they're
divisive. Alexander (2014). The most controversial examples of
an issue get the most attention, not because they're most
important or representative, but because they generate the most
engagement through outrage and disagreement.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

TOXOPLASMA_OF_RAGE_SYSTEM = """You are a toxoplasma of rage specialist. Given a topic or controversy, assess whether it's receiving attention because of its divisiveness rather than its importance:

Key concepts (Alexander, 2014):
- Toxoplasma of rage: controversial cases spread because they're controversial
- Engagement optimization: divisive content gets more shares/clicks
- Worst example selection: the most controversial case becomes the poster child
- Outrage as signal boost: anger drives sharing and attention
- Representativeness inversion: least representative cases get most attention
- Motte-and-bailey interaction: extreme cases used to argue for moderate positions
- Attention economy: controversy is currency

When toxoplasma of rage IS present:
- The most controversial example of an issue dominates discussion
- Attention is proportional to divisiveness, not importance
- The case being discussed is specifically chosen because it's ambiguous
- Both sides can claim the example supports their position
- More representative cases are ignored in favor of controversial ones
- The discussion generates heat but not light
- Engagement metrics drive topic selection over importance

When attention IS proportional to importance:
- The case is genuinely representative of the broader issue
- Attention reflects actual stakes and impact
- The controversy is about substance, not just engagement
- Less controversial but more important cases also get attention
- The discussion advances understanding rather than just generating outrage
- Topic selection is driven by impact, not engagement

Output JSON with: toxoplasma_present (bool), severity (none/mild/moderate/severe), topic (what topic is getting attention), controversy_level (how divisive is it), importance_level (how important is it actually), attention_driver (what drives the attention — importance or divisiveness), representativeness (how representative is this case), better_examples (are there more representative cases being ignored), recommendation (attention_proportional/mild_controversy_bias/significant_toxoplasma/major_outrage_driven_attention/refocus_on_representative_cases)."""

TOXOPLASMA_OF_RAGE_PROMPT = """Detect toxoplasma of rage:

Topic: {topic}
Attention level: {attention}
Importance: {importance}
Controversy: {controversy}
Domain: {domain}
Context: {context}

Is this topic receiving attention because of its divisiveness rather than its importance? Return ONLY valid JSON."""


class ToxoplasmaOfRageService:
    """Detects toxoplasma of rage — attention driven by divisiveness not importance."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        topic: str,
        *,
        attention: str = "",
        importance: str = "",
        controversy: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect toxoplasma of rage."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=TOXOPLASMA_OF_RAGE_PROMPT.format(
                topic=topic,
                attention=attention or "Not specified",
                importance=importance or "Not specified",
                controversy=controversy or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=TOXOPLASMA_OF_RAGE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "topic": topic[:200],
            "toxoplasma_present": data.get("toxoplasma_present", False),
            "severity": data.get("severity", ""),
            "controversy_level": data.get("controversy_level", ""),
            "importance_level": data.get("importance_level", ""),
            "attention_driver": data.get("attention_driver", ""),
            "representativeness": data.get("representativeness", ""),
            "better_examples": data.get("better_examples", ""),
            "recommendation": data.get("recommendation", ""),
        }
