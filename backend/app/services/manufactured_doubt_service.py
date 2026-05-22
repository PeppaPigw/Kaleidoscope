"""ManufacturedDoubtService — Manufactured Doubt Detection.

Detects manufactured doubt — deliberately creating doubt about
well-established knowledge for strategic purposes.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

MANUFACTURED_DOUBT_SYSTEM = """You are a manufactured doubt specialist. Given a discourse about established knowledge, assess whether doubt is being deliberately manufactured:

Key concepts:
- Manufactured doubt: deliberately creating doubt about established knowledge
- Doubt as product: doubt produced strategically not epistemically
- False controversy: creating appearance of controversy where consensus exists
- Expert doubt manufacturing: using credentialed voices to create doubt
- Evidence denial industry: organized denial of established evidence
- Strategic uncertainty: amplifying uncertainty beyond what evidence warrants
- Doubt merchants: actors whose goal is doubt not truth

When manufactured doubt IS present:
- Doubt deliberately created about well-established knowledge
- Strategic purpose behind doubt creation
- False controversy manufactured where consensus exists
- Credentialed voices used to create unwarranted doubt
- Evidence denial organized and funded
- Uncertainty amplified beyond what evidence warrants
- Doubt serving interests rather than truth

When legitimate skepticism is present:
- Doubt proportionate to actual uncertainty
- Genuine questions about evidence quality
- Real controversy about genuinely uncertain matters
- Expert disagreement reflecting genuine uncertainty
- Evidence questioned on methodological grounds
- Uncertainty acknowledged honestly
- Skepticism serving truth-seeking

Output JSON with: manufactured_doubt_present (bool), severity (none/mild/moderate/severe), knowledge (what established knowledge is targeted), doubt_strategy (how doubt is manufactured), purpose (what purpose doubt serves), evidence_status (what evidence actually shows), recommendation (legitimate_skepticism/mild_doubt_amplification/significant_manufactured_doubt/major_evidence_denial/acknowledge_established_knowledge)."""

MANUFACTURED_DOUBT_PROMPT = """Detect manufactured doubt:

Knowledge targeted: {knowledge}
Doubt strategy: {strategy}
Purpose served: {purpose}
Evidence status: {evidence}
Domain: {domain}
Context: {context}

Is doubt being deliberately manufactured about well-established knowledge? Return ONLY valid JSON."""


class ManufacturedDoubtService:
    """Detects manufactured doubt — deliberately creating doubt about established knowledge."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        knowledge: str,
        *,
        strategy: str = "",
        purpose: str = "",
        evidence: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect manufactured doubt."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=MANUFACTURED_DOUBT_PROMPT.format(
                knowledge=knowledge,
                strategy=strategy or "Not specified",
                purpose=purpose or "Not specified",
                evidence=evidence or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=MANUFACTURED_DOUBT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "knowledge": knowledge[:200],
            "manufactured_doubt_present": data.get("manufactured_doubt_present", False),
            "severity": data.get("severity", ""),
            "doubt_strategy": data.get("doubt_strategy", ""),
            "purpose": data.get("purpose", ""),
            "evidence_status": data.get("evidence_status", ""),
            "recommendation": data.get("recommendation", ""),
        }
