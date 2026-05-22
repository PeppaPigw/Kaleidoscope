"""GishGallopService — Gish Gallop Detection.

Detects Gish gallop — overwhelming with a rapid succession of
many arguments regardless of their accuracy or strength.
Named after Duane Gish. The technique exploits the asymmetry
between making claims (fast) and refuting them (slow). By the
time one claim is addressed, ten more have been made. Quantity
substitutes for quality in argumentation.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

GISH_GALLOP_SYSTEM = """You are a Gish gallop specialist. Given an argumentative exchange, assess whether one party is overwhelming with quantity of claims rather than quality:

Key concepts:
- Gish gallop: rapid-fire claims faster than can be refuted
- Asymmetric effort: making claims is easier than refuting them
- Quantity over quality: many weak arguments vs few strong ones
- Refutation exhaustion: opponent can't address everything
- Appearance of strength: unrefuted claims seem valid by default
- Topic shifting: moving to new claims before old ones are resolved
- Firehose of falsehood: related propaganda technique

When a Gish gallop IS occurring:
- Many claims made in rapid succession without supporting each
- Topic shifts before any single point is resolved
- Claims of varying quality mixed together indiscriminately
- The sheer volume makes point-by-point response impossible
- Unaddressed claims are treated as conceded
- New arguments introduced before previous ones are settled
- Breadth of claims substituting for depth of evidence

When comprehensive argumentation IS legitimate:
- Each point is supported with evidence
- The arguer engages with responses to individual points
- Points build on each other rather than just accumulating
- The breadth is appropriate to the complexity of the topic
- The arguer is willing to focus on any single point in depth

Output JSON with: gish_gallop_present (bool), severity (none/mild/moderate/severe), exchange (what argumentative context), claim_count (approximate number of claims), supported_claims (how many are well-supported), unsupported_claims (how many lack support), topic_shifts (how often does the topic shift), refutation_asymmetry (how much harder is refutation than assertion), recommendation (argumentation_legitimate/mild_claim_flooding/significant_gish_gallop/major_firehose_technique/demand_depth_over_breadth)."""

GISH_GALLOP_PROMPT = """Detect Gish gallop:

Exchange: {exchange}
Claims made: {claims}
Support provided: {support}
Response pattern: {response}
Domain: {domain}
Context: {context}

Is one party overwhelming with quantity of arguments rather than quality? Return ONLY valid JSON."""


class GishGallopService:
    """Detects Gish gallop — overwhelming with quantity of claims over quality."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        exchange: str,
        *,
        claims: str = "",
        support: str = "",
        response: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect Gish gallop."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=GISH_GALLOP_PROMPT.format(
                exchange=exchange,
                claims=claims or "Not specified",
                support=support or "Not specified",
                response=response or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=GISH_GALLOP_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "exchange": exchange[:200],
            "gish_gallop_present": data.get("gish_gallop_present", False),
            "severity": data.get("severity", ""),
            "claim_count": data.get("claim_count", ""),
            "supported_claims": data.get("supported_claims", ""),
            "unsupported_claims": data.get("unsupported_claims", ""),
            "topic_shifts": data.get("topic_shifts", ""),
            "refutation_asymmetry": data.get("refutation_asymmetry", ""),
            "recommendation": data.get("recommendation", ""),
        }
