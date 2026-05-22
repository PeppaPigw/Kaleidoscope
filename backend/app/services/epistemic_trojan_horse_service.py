"""EpistemicTrojanHorseService — Epistemic Trojan Horse Detection.

Detects epistemic trojan horses — harmful ideas disguised as
beneficial ones to bypass intellectual defenses.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_TROJAN_HORSE_SYSTEM = """You are an epistemic trojan horse specialist. Given an idea presentation, assess whether harmful ideas are disguised as beneficial:

Key concepts:
- Epistemic trojan horse: harmful idea disguised as beneficial
- Disguised payload: harmful content hidden in appealing wrapper
- Defense bypass: bypassing defenses through disguise
- Attractive packaging: harmful content in attractive package
- Hidden agenda: hidden harmful agenda within beneficial framing
- Delayed activation: harm activating after acceptance
- Trust exploitation: exploiting trust to deliver harm

When epistemic trojan horse IS present:
- Harmful ideas disguised as beneficial ones
- Harmful content hidden in appealing wrapper
- Bypassing intellectual defenses through disguise
- Harmful content in attractive packaging
- Hidden harmful agenda within beneficial framing
- Harm activating only after idea is accepted
- Exploiting trust to deliver harmful content

When genuine benefit is present:
- Ideas that are what they appear to be
- Content transparent about its nature
- Engaging defenses honestly
- Packaging matches content
- Agenda transparent and beneficial
- Benefits immediate and ongoing
- Trust maintained through honesty

Output JSON with: trojan_horse_present (bool), severity (none/mild/moderate/severe), disguise (what disguise is used), payload (what harmful payload is hidden), bypass (how defenses are bypassed), activation (when harm activates), recommendation (genuine_benefit/mild_mismatch/significant_trojan_horse/major_disguised_harm/expose_hidden_payload)."""

EPISTEMIC_TROJAN_HORSE_PROMPT = """Detect epistemic trojan horse:

Disguise: {disguise}
Payload: {payload}
Bypass: {bypass}
Activation: {activation}
Domain: {domain}
Context: {context}

Are harmful ideas disguised as beneficial to bypass intellectual defenses? Return ONLY valid JSON."""


class EpistemicTrojanHorseService:
    """Detects epistemic trojan horses — harmful ideas disguised as beneficial."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        disguise: str,
        *,
        payload: str = "",
        bypass: str = "",
        activation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic trojan horse."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_TROJAN_HORSE_PROMPT.format(
                disguise=disguise,
                payload=payload or "Not specified",
                bypass=bypass or "Not specified",
                activation=activation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_TROJAN_HORSE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "disguise": disguise[:200],
            "trojan_horse_present": data.get("trojan_horse_present", False),
            "severity": data.get("severity", ""),
            "payload": data.get("payload", ""),
            "bypass": data.get("bypass", ""),
            "activation": data.get("activation", ""),
            "recommendation": data.get("recommendation", ""),
        }
