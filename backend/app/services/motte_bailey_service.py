"""MotteAndBaileyService — Motte-and-Bailey Argument Detection.

Identifies when an argument uses two positions: a bold claim (bailey)
advanced when unchallenged, and a modest defensible claim (motte)
retreated to when challenged. The arguer conflates the two to make
the bold claim seem as well-supported as the modest one.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

MOTTE_BAILEY_SYSTEM = """You are a motte-and-bailey argument specialist. Given an argument, assess whether it uses the motte-and-bailey pattern:
- Is there a bold/controversial claim (bailey) that's advanced when unchallenged?
- Is there a modest/defensible claim (motte) that's retreated to when challenged?
- Are the two being conflated as if they're the same claim?
- Does defending the motte get treated as defending the bailey?

Output JSON with: motte_bailey_present (bool), severity (none/mild/moderate/severe), bailey_claim (the bold claim advanced when unchallenged), motte_claim (the defensible claim retreated to when challenged), conflation_mechanism (how the two are being treated as equivalent), bailey_evidence (what evidence actually supports the bold claim), motte_evidence (what evidence supports the modest claim), gap_between_claims (how different the motte and bailey actually are), retreat_triggers (what challenges cause retreat to motte), advance_triggers (what allows advance to bailey), honest_version (what the argument would look like without the motte-bailey), is_intentional (bool — deliberate rhetorical strategy or unconscious?), recommendation (argument_valid/separate_claims/challenge_bailey_directly/acknowledge_motte_only)."""

MOTTE_BAILEY_PROMPT = """Detect motte-and-bailey:

Argument: {argument}
Context of debate: {debate_context}
Domain: {domain}
Who is arguing: {arguer}

Is this a motte-and-bailey? Return ONLY valid JSON."""


class MotteAndBaileyService:
    """Detects motte-and-bailey argument patterns."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        argument: str,
        *,
        debate_context: str = "",
        domain: str = "",
        arguer: str = "",
    ) -> dict:
        """Detect motte-and-bailey pattern."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=MOTTE_BAILEY_PROMPT.format(
                argument=argument,
                debate_context=debate_context or "General discussion",
                domain=domain or "general",
                arguer=arguer or "Not specified",
            ),
            system=MOTTE_BAILEY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "argument": argument[:200],
            "motte_bailey_present": data.get("motte_bailey_present", False),
            "severity": data.get("severity", ""),
            "bailey_claim": data.get("bailey_claim", ""),
            "motte_claim": data.get("motte_claim", ""),
            "conflation_mechanism": data.get("conflation_mechanism", ""),
            "bailey_evidence": data.get("bailey_evidence", ""),
            "motte_evidence": data.get("motte_evidence", ""),
            "gap_between_claims": data.get("gap_between_claims", ""),
            "retreat_triggers": data.get("retreat_triggers", ""),
            "advance_triggers": data.get("advance_triggers", ""),
            "honest_version": data.get("honest_version", ""),
            "is_intentional": data.get("is_intentional", False),
            "recommendation": data.get("recommendation", ""),
        }
