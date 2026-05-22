"""EpistemicProcrastinationService — Epistemic Procrastination Detection.

Detects epistemic procrastination — delaying necessary epistemic
work indefinitely, avoiding needed inquiry or belief revision.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PROCRASTINATION_SYSTEM = """You are an epistemic procrastination specialist. Given an epistemic situation, assess whether necessary epistemic work is being indefinitely delayed:

Key concepts:
- Epistemic procrastination: delaying necessary epistemic work
- Inquiry avoidance: avoiding needed investigation
- Revision postponement: postponing needed belief revision
- Evidence avoidance: avoiding gathering needed evidence
- Uncomfortable truth delay: delaying confrontation with uncomfortable truths
- Epistemic comfort zone: staying in comfort zone avoiding challenge
- Indefinite deferral: always deferring epistemic work to later

When epistemic procrastination IS present:
- Necessary epistemic work indefinitely delayed
- Needed investigation avoided
- Required belief revision postponed
- Evidence gathering avoided
- Uncomfortable truths not confronted
- Comfort zone maintained at cost of knowledge
- Epistemic work always deferred to later

When appropriate pacing is present:
- Epistemic work paced appropriately
- Investigation conducted when needed
- Belief revision undertaken when warranted
- Evidence gathered at appropriate pace
- Uncomfortable truths confronted when ready
- Challenge accepted at sustainable rate
- Epistemic work prioritized appropriately

Output JSON with: procrastination_present (bool), severity (none/mild/moderate/severe), work_needed (what epistemic work is needed), delay_pattern (how delay manifests), avoidance_reason (why work is avoided), consequence (what consequences result), recommendation (appropriate_pacing/mild_delay/significant_epistemic_procrastination/major_inquiry_avoidance/begin_epistemic_work_now)."""

EPISTEMIC_PROCRASTINATION_PROMPT = """Detect epistemic procrastination:

Work needed: {work}
Delay pattern: {delay}
Avoidance reason: {reason}
Consequence: {consequence}
Domain: {domain}
Context: {context}

Is necessary epistemic work being indefinitely delayed? Return ONLY valid JSON."""


class EpistemicProcrastinationService:
    """Detects epistemic procrastination — delaying necessary epistemic work."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        work: str,
        *,
        delay: str = "",
        reason: str = "",
        consequence: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic procrastination."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PROCRASTINATION_PROMPT.format(
                work=work,
                delay=delay or "Not specified",
                reason=reason or "Not specified",
                consequence=consequence or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PROCRASTINATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "work": work[:200],
            "procrastination_present": data.get("procrastination_present", False),
            "severity": data.get("severity", ""),
            "delay_pattern": data.get("delay_pattern", ""),
            "avoidance_reason": data.get("avoidance_reason", ""),
            "consequence": data.get("consequence", ""),
            "recommendation": data.get("recommendation", ""),
        }
