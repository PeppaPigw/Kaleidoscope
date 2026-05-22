"""EpistemicAttentionManipulationService — Epistemic Attention Manipulation Detection.

Detects epistemic attention manipulation — manipulating others' attention
to control what they think about.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ATTENTION_MANIPULATION_SYSTEM = """You are an epistemic attention manipulation specialist. Given manipulating others' attention, assess attention manipulation:

Key concepts:
- Epistemic attention manipulation: manipulating others' attention to control thinking
- Distraction deployment: deploying distractions to redirect attention
- Misdirection: misdirecting attention from important issues
- Agenda setting: controlling what others pay attention to
- Framing control: controlling frames to direct attention
- Salience manufacturing: manufacturing salience for chosen topics
- Attention gatekeeping: gatekeeping what gets attention

When epistemic attention manipulation IS present:
- Manipulating others' attention
- Deploying distractions
- Misdirecting from important issues
- Controlling what others attend to
- Controlling frames
- Manufacturing salience
- Gatekeeping attention

When no attention manipulation:
- Respecting others' attention
- No distractions deployed
- Honest direction of attention
- Others choose own focus
- Transparent framing
- Natural salience
- Open attention

Output JSON with: attention_manipulation_detected (bool), severity (none/mild/moderate/severe), distraction_deployment (what distractions deployed), misdirection (what misdirecting from), agenda_setting (what agenda being set), salience_manufacturing (what salience manufactured for), recommendation (no_attention_manipulation/mild_transparency_practice/significant_honesty_building/major_intensive_manipulation_cessation/emergency_complete_attention_manipulation)."""

EPISTEMIC_ATTENTION_MANIPULATION_PROMPT = """Detect epistemic attention manipulation:

Distraction deployment: {distraction_deployment}
Misdirection: {misdirection}
Agenda setting: {agenda_setting}
Salience manufacturing: {salience_manufacturing}
Domain: {domain}
Context: {context}

Is there manipulating others' attention to control what they think about? Return ONLY valid JSON."""


class EpistemicAttentionManipulationService:
    """Detects epistemic attention manipulation — manipulating to control thinking."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        distraction_deployment: str,
        *,
        misdirection: str = "",
        agenda_setting: str = "",
        salience_manufacturing: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic attention manipulation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ATTENTION_MANIPULATION_PROMPT.format(
                distraction_deployment=distraction_deployment,
                misdirection=misdirection or "Not specified",
                agenda_setting=agenda_setting or "Not specified",
                salience_manufacturing=salience_manufacturing or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ATTENTION_MANIPULATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "distraction_deployment": distraction_deployment[:200],
            "attention_manipulation_detected": data.get("attention_manipulation_detected", False),
            "severity": data.get("severity", ""),
            "misdirection": data.get("misdirection", ""),
            "agenda_setting": data.get("agenda_setting", ""),
            "salience_manufacturing": data.get("salience_manufacturing", ""),
            "recommendation": data.get("recommendation", ""),
        }
