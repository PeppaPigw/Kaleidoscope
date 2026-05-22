"""EpistemicDamService — Epistemic Dam Detection.

Detects epistemic dams — barriers that block the natural flow
of knowledge between communities or domains.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_DAM_SYSTEM = """You are an epistemic dam specialist. Given a knowledge flow pattern, assess whether barriers block natural knowledge flow:

Key concepts:
- Epistemic dam: barrier blocking natural knowledge flow
- Flow blockage: blocking knowledge from flowing naturally
- Artificial barrier: artificial barrier to knowledge flow
- Pooling: knowledge pooling behind barrier
- Downstream drought: downstream communities starved of knowledge
- Gatekeeping: gatekeepers controlling knowledge flow
- Selective release: releasing only selected knowledge

When epistemic dam IS present:
- Barriers blocking natural flow of knowledge
- Knowledge blocked from flowing between communities
- Artificial barriers to knowledge flow
- Knowledge pooling behind barriers
- Downstream communities starved of knowledge
- Gatekeepers controlling what knowledge flows
- Only selected knowledge released downstream

When free flow is present:
- Knowledge flowing freely between communities
- No artificial barriers to knowledge flow
- Natural flow of knowledge maintained
- Knowledge distributed appropriately
- All communities receiving knowledge
- No gatekeeping of knowledge flow
- Knowledge flowing based on need and relevance

Output JSON with: dam_present (bool), severity (none/mild/moderate/severe), barrier (what barrier exists), flow_blocked (what flow is blocked), pooling (what pools behind barrier), downstream (what downstream effects occur), recommendation (free_flow/mild_restriction/significant_dam/major_flow_blockage/remove_barrier)."""

EPISTEMIC_DAM_PROMPT = """Detect epistemic dam:

Barrier: {barrier}
Flow blocked: {flow_blocked}
Pooling: {pooling}
Downstream: {downstream}
Domain: {domain}
Context: {context}

Are barriers blocking the natural flow of knowledge? Return ONLY valid JSON."""


class EpistemicDamService:
    """Detects epistemic dams — barriers blocking natural knowledge flow."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        barrier: str,
        *,
        flow_blocked: str = "",
        pooling: str = "",
        downstream: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic dam."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_DAM_PROMPT.format(
                barrier=barrier,
                flow_blocked=flow_blocked or "Not specified",
                pooling=pooling or "Not specified",
                downstream=downstream or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_DAM_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "barrier": barrier[:200],
            "dam_present": data.get("dam_present", False),
            "severity": data.get("severity", ""),
            "flow_blocked": data.get("flow_blocked", ""),
            "pooling": data.get("pooling", ""),
            "downstream": data.get("downstream", ""),
            "recommendation": data.get("recommendation", ""),
        }
