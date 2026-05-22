"""EpistemicIntellectualRebellionService — Epistemic Intellectual Rebellion Detection.

Detects epistemic intellectual rebellion — reflexively opposing mentor or
authority positions regardless of their merit.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_INTELLECTUAL_REBELLION_SYSTEM = """You are an epistemic intellectual rebellion specialist. Given reflexively opposing authority, assess intellectual rebellion:

Key concepts:
- Epistemic intellectual rebellion: reflexively opposing authority positions
- Contrarian reflex: automatically opposing whatever authority says
- Reactive positioning: positions determined by what one opposes
- Authority rejection: rejecting views because of who holds them
- Rebellion as identity: defining self through intellectual opposition
- Indiscriminate rejection: rejecting everything from authority figures
- Counter-dependence: depending on authority by always opposing them

When epistemic intellectual rebellion IS present:
- Reflexively opposing authority
- Automatically opposing whatever authority says
- Positions determined by opposition
- Rejecting views because of source
- Defining self through opposition
- Rejecting everything from authority
- Depending on authority by opposing

When no intellectual rebellion:
- Evaluating positions on merit
- Considering authority views fairly
- Positions determined by evidence
- Evaluating views regardless of source
- Self defined positively not oppositionally
- Selective engagement with authority
- Independent of authority in both directions

Output JSON with: intellectual_rebellion_detected (bool), severity (none/mild/moderate/severe), contrarian_reflex (what automatically opposing), reactive_positioning (what positions determined by opposition), authority_rejection (whose views rejected because of source), counter_dependence (how depending by opposing), recommendation (no_intellectual_rebellion/mild_merit_evaluation/significant_independence_building/major_intensive_disentanglement/emergency_complete_reactive_opposition)."""

EPISTEMIC_INTELLECTUAL_REBELLION_PROMPT = """Detect epistemic intellectual rebellion:

Contrarian reflex: {contrarian_reflex}
Reactive positioning: {reactive_positioning}
Authority rejection: {authority_rejection}
Counter dependence: {counter_dependence}
Domain: {domain}
Context: {context}

Is there reflexively opposing mentor or authority positions? Return ONLY valid JSON."""


class EpistemicIntellectualRebellionService:
    """Detects epistemic intellectual rebellion — reflexively opposing authority."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        contrarian_reflex: str,
        *,
        reactive_positioning: str = "",
        authority_rejection: str = "",
        counter_dependence: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic intellectual rebellion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_INTELLECTUAL_REBELLION_PROMPT.format(
                contrarian_reflex=contrarian_reflex,
                reactive_positioning=reactive_positioning or "Not specified",
                authority_rejection=authority_rejection or "Not specified",
                counter_dependence=counter_dependence or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_INTELLECTUAL_REBELLION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "contrarian_reflex": contrarian_reflex[:200],
            "intellectual_rebellion_detected": data.get("intellectual_rebellion_detected", False),
            "severity": data.get("severity", ""),
            "reactive_positioning": data.get("reactive_positioning", ""),
            "authority_rejection": data.get("authority_rejection", ""),
            "counter_dependence": data.get("counter_dependence", ""),
            "recommendation": data.get("recommendation", ""),
        }
