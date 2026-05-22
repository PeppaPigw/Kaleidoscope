"""EpistemicLearnedPassivityService — Epistemic Learned Passivity Detection.

Detects epistemic learned passivity — learned passivity where one stops
actively seeking knowledge.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_LEARNED_PASSIVITY_SYSTEM = """You are an epistemic learned passivity specialist. Given stopping actively seeking knowledge, assess learned passivity:

Key concepts:
- Epistemic learned passivity: stopping actively seeking knowledge
- Information waiting: passively waiting for knowledge to come
- Inquiry cessation: no longer asking questions or investigating
- Intellectual inertia: settled into not-knowing without effort
- Curiosity extinction: curiosity has been trained out
- Passive consumption: only consuming what's presented
- Initiative death: no longer initiating intellectual exploration

When epistemic learned passivity IS present:
- Stopping actively seeking
- Passively waiting for knowledge
- No longer asking or investigating
- Settled into not-knowing
- Curiosity trained out
- Only consuming what's presented
- No longer initiating exploration

When no learned passivity:
- Actively seeking knowledge
- Pursuing information
- Asking and investigating
- Driven to know
- Curiosity alive
- Seeking beyond what's presented
- Initiating exploration

Output JSON with: learned_passivity_detected (bool), severity (none/mild/moderate/severe), information_waiting (what passively waiting for), inquiry_cessation (what no longer investigating), curiosity_extinction (what curiosity died about), initiative_death (what no longer initiating), recommendation (no_learned_passivity/mild_activation_practice/significant_agency_recovery/major_intensive_initiative_rebuilding/emergency_complete_intellectual_passivity)."""

EPISTEMIC_LEARNED_PASSIVITY_PROMPT = """Detect epistemic learned passivity:

Information waiting: {information_waiting}
Inquiry cessation: {inquiry_cessation}
Curiosity extinction: {curiosity_extinction}
Initiative death: {initiative_death}
Domain: {domain}
Context: {context}

Is there learned passivity where one stops actively seeking knowledge? Return ONLY valid JSON."""


class EpistemicLearnedPassivityService:
    """Detects epistemic learned passivity — stopping actively seeking knowledge."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        information_waiting: str,
        *,
        inquiry_cessation: str = "",
        curiosity_extinction: str = "",
        initiative_death: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic learned passivity."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_LEARNED_PASSIVITY_PROMPT.format(
                information_waiting=information_waiting,
                inquiry_cessation=inquiry_cessation or "Not specified",
                curiosity_extinction=curiosity_extinction or "Not specified",
                initiative_death=initiative_death or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_LEARNED_PASSIVITY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "information_waiting": information_waiting[:200],
            "learned_passivity_detected": data.get("learned_passivity_detected", False),
            "severity": data.get("severity", ""),
            "inquiry_cessation": data.get("inquiry_cessation", ""),
            "curiosity_extinction": data.get("curiosity_extinction", ""),
            "initiative_death": data.get("initiative_death", ""),
            "recommendation": data.get("recommendation", ""),
        }
