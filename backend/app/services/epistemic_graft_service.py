"""EpistemicGraftService — Epistemic Graft Detection.

Detects epistemic grafting need — transplanting intellectual tissue from
one area to repair damage in another.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_GRAFT_SYSTEM = """You are an epistemic graft specialist. Given intellectual tissue damage, assess grafting need:

Key concepts:
- Epistemic graft: transplanting intellectual tissue to repair damage
- Autograft: using own intellectual tissue from another area
- Allograft: using tissue from another intellectual system
- Xenograft: using tissue from different intellectual species
- Take rate: percentage of graft that survives
- Donor site: where tissue is harvested from
- Recipient site: where tissue is placed

When epistemic grafting IS needed:
- Intellectual tissue damage too large for self-repair
- Own tissue available from another area
- Compatible tissue from other systems available
- Cross-species tissue applicable
- Reasonable survival rate expected
- Suitable donor site identified
- Recipient site prepared

When no grafting needed:
- Self-repair sufficient
- No tissue deficit
- Wound closing naturally
- No donor tissue needed
- Natural healing adequate
- No harvest required
- No transplant necessary

Output JSON with: graft_needed (bool), severity (none/mild/moderate/severe), graft_type (what source), donor_site (what harvest location), take_rate_estimate (what survival expectation), recipient_preparation (what site readiness), recommendation (no_graft_needed/mild_patch/significant_graft/major_full_thickness/emergency_coverage)."""

EPISTEMIC_GRAFT_PROMPT = """Detect epistemic grafting need:

Graft type: {graft_type}
Donor site: {donor_site}
Take rate estimate: {take_rate_estimate}
Recipient preparation: {recipient_preparation}
Domain: {domain}
Context: {context}

Is intellectual tissue damage too large for self-repair and requiring grafting? Return ONLY valid JSON."""


class EpistemicGraftService:
    """Detects epistemic grafting need — transplanting tissue to repair damage."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        graft_type: str,
        *,
        donor_site: str = "",
        take_rate_estimate: str = "",
        recipient_preparation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic grafting need."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_GRAFT_PROMPT.format(
                graft_type=graft_type,
                donor_site=donor_site or "Not specified",
                take_rate_estimate=take_rate_estimate or "Not specified",
                recipient_preparation=recipient_preparation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_GRAFT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "graft_type": graft_type[:200],
            "graft_needed": data.get("graft_needed", False),
            "severity": data.get("severity", ""),
            "donor_site": data.get("donor_site", ""),
            "take_rate_estimate": data.get("take_rate_estimate", ""),
            "recipient_preparation": data.get("recipient_preparation", ""),
            "recommendation": data.get("recommendation", ""),
        }
