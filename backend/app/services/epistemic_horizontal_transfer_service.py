"""EpistemicHorizontalTransferService — Epistemic Horizontal Transfer Detection.

Detects epistemic horizontal transfer — beliefs jumping between
unrelated domains without appropriate adaptation.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_HORIZONTAL_TRANSFER_SYSTEM = """You are an epistemic horizontal transfer specialist. Given a cross-domain belief pattern, assess whether beliefs jump between unrelated domains without adaptation:

Key concepts:
- Epistemic horizontal transfer: beliefs jumping between unrelated domains
- Domain jumping: beliefs applied in inappropriate domains
- Inappropriate transfer: transfer without necessary adaptation
- Context stripping: losing necessary context during transfer
- False universality: assuming universal applicability
- Analogy overextension: extending analogies beyond validity
- Category crossing: crossing category boundaries inappropriately

When epistemic horizontal transfer IS present:
- Beliefs jumping between unrelated domains without adaptation
- Beliefs applied in domains where they don't belong
- Transfer occurring without necessary adaptation
- Necessary context lost during domain transfer
- Assuming universal applicability without justification
- Extending analogies far beyond their validity
- Crossing category boundaries inappropriately

When appropriate transfer is present:
- Cross-domain transfer with appropriate adaptation
- Beliefs applied in domains where they genuinely fit
- Transfer accompanied by necessary modifications
- Context preserved or appropriately translated
- Universality claims justified by evidence
- Analogies used within their valid range
- Category boundaries respected or explicitly bridged

Output JSON with: horizontal_transfer_present (bool), severity (none/mild/moderate/severe), belief (what belief transfers), source_domain (where it comes from), target_domain (where it goes), adaptation_failure (what adaptation is missing), recommendation (appropriate_transfer/mild_overextension/significant_horizontal_transfer/major_domain_violation/adapt_for_target_domain)."""

EPISTEMIC_HORIZONTAL_TRANSFER_PROMPT = """Detect epistemic horizontal transfer:

Belief: {belief}
Source domain: {source_domain}
Target domain: {target_domain}
Adaptation failure: {adaptation_failure}
Domain: {domain}
Context: {context}

Are beliefs jumping between unrelated domains without appropriate adaptation? Return ONLY valid JSON."""


class EpistemicHorizontalTransferService:
    """Detects epistemic horizontal transfer — beliefs jumping domains without adaptation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        belief: str,
        *,
        source_domain: str = "",
        target_domain: str = "",
        adaptation_failure: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic horizontal transfer."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_HORIZONTAL_TRANSFER_PROMPT.format(
                belief=belief,
                source_domain=source_domain or "Not specified",
                target_domain=target_domain or "Not specified",
                adaptation_failure=adaptation_failure or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_HORIZONTAL_TRANSFER_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "belief": belief[:200],
            "horizontal_transfer_present": data.get("horizontal_transfer_present", False),
            "severity": data.get("severity", ""),
            "source_domain": data.get("source_domain", ""),
            "target_domain": data.get("target_domain", ""),
            "adaptation_failure": data.get("adaptation_failure", ""),
            "recommendation": data.get("recommendation", ""),
        }
