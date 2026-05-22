"""FalseControversyService — False Controversy Detection.

Detects false controversy — manufacturing controversy where genuine
expert consensus exists, creating appearance of debate where none
exists among qualified experts.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

FALSE_CONTROVERSY_SYSTEM = """You are a false controversy specialist. Given a debate or controversy, assess whether it is manufactured rather than genuine:

Key concepts:
- False controversy: manufactured debate where consensus exists
- Manufactured doubt: creating uncertainty about settled science
- Astroturfing: fake grassroots disagreement
- Tobacco strategy: manufacturing controversy to delay action
- Merchant of doubt: professional doubt creation
- False balance: media presenting fringe as mainstream
- Controversy entrepreneur: profiting from manufactured debate

When false controversy IS present:
- Controversy manufactured where expert consensus exists
- Doubt created about well-established findings
- Fringe positions elevated to appear mainstream
- Professional doubt-creation industry involved
- Controversy serves interests of specific parties
- Debate manufactured to delay action
- Appearance of disagreement where experts agree

When controversy is genuine:
- Genuine disagreement among qualified experts
- Multiple legitimate positions with evidence
- Debate reflects real uncertainty in the field
- Controversy not serving specific interests
- Disagreement proportionate to actual uncertainty
- Expert community genuinely divided
- Debate advancing understanding

Output JSON with: false_controversy_present (bool), severity (none/mild/moderate/severe), topic (what topic is controversial), actual_consensus (what consensus actually exists), manufactured_doubt (what doubt is manufactured), beneficiary (who benefits from controversy), recommendation (genuine_controversy/mild_doubt_amplification/significant_false_controversy/major_manufactured_doubt/acknowledge_consensus)."""

FALSE_CONTROVERSY_PROMPT = """Detect false controversy:

Topic: {topic}
Controversy claimed: {controversy}
Expert consensus: {consensus}
Doubt sources: {sources}
Domain: {domain}
Context: {context}

Is controversy being manufactured where genuine expert consensus exists? Return ONLY valid JSON."""


class FalseControversyService:
    """Detects false controversy — manufactured debate where consensus exists."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        topic: str,
        *,
        controversy: str = "",
        consensus: str = "",
        sources: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect false controversy."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=FALSE_CONTROVERSY_PROMPT.format(
                topic=topic,
                controversy=controversy or "Not specified",
                consensus=consensus or "Not specified",
                sources=sources or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=FALSE_CONTROVERSY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "topic": topic[:200],
            "false_controversy_present": data.get("false_controversy_present", False),
            "severity": data.get("severity", ""),
            "actual_consensus": data.get("actual_consensus", ""),
            "manufactured_doubt": data.get("manufactured_doubt", ""),
            "beneficiary": data.get("beneficiary", ""),
            "recommendation": data.get("recommendation", ""),
        }
