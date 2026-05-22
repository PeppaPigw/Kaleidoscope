"""EpistemicAcutePoisoningService — Epistemic Acute Poisoning Detection.

Detects epistemic acute poisoning — sudden toxic exposure overwhelming
intellectual defenses in a single catastrophic event.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ACUTE_POISONING_SYSTEM = """You are an epistemic acute poisoning specialist. Given intellectual toxic exposure, assess whether sudden overwhelming poisoning has occurred:

Key concepts:
- Epistemic acute poisoning: sudden toxic exposure overwhelming defenses
- Lethal dose: amount causing intellectual death
- Toxidrome: recognizable pattern of poisoning symptoms
- Decontamination: removing toxin before absorption
- Antidote: specific counteragent to the poison
- Organ damage: specific intellectual systems affected
- Recovery window: time available for intervention

When epistemic acute poisoning IS present:
- Sudden toxic exposure overwhelming defenses
- Near-lethal intellectual dose received
- Recognizable pattern of poisoning symptoms
- Need for immediate decontamination
- Specific antidote required
- Specific intellectual systems damaged
- Narrow recovery window

When healthy state is present:
- No toxic exposure
- Well below harmful thresholds
- No poisoning symptoms
- No decontamination needed
- No antidote required
- All systems functioning
- No urgency

Output JSON with: acute_poisoning_present (bool), severity (none/mild/moderate/severe), toxidrome (what symptom pattern), organ_damage (what systems affected), decontamination_need (what removal required), recovery_window (what time available), recommendation (healthy_state/mild_poisoning/significant_acute_poisoning/major_toxic_crisis/emergency_intellectual_decontamination)."""

EPISTEMIC_ACUTE_POISONING_PROMPT = """Detect epistemic acute poisoning:

Toxidrome: {toxidrome}
Organ damage: {organ_damage}
Decontamination need: {decontamination_need}
Recovery window: {recovery_window}
Domain: {domain}
Context: {context}

Has sudden toxic exposure overwhelmed intellectual defenses? Return ONLY valid JSON."""


class EpistemicAcutePoisoningService:
    """Detects epistemic acute poisoning — sudden toxic intellectual exposure."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        toxidrome: str,
        *,
        organ_damage: str = "",
        decontamination_need: str = "",
        recovery_window: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic acute poisoning."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ACUTE_POISONING_PROMPT.format(
                toxidrome=toxidrome,
                organ_damage=organ_damage or "Not specified",
                decontamination_need=decontamination_need or "Not specified",
                recovery_window=recovery_window or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ACUTE_POISONING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "toxidrome": toxidrome[:200],
            "acute_poisoning_present": data.get("acute_poisoning_present", False),
            "severity": data.get("severity", ""),
            "organ_damage": data.get("organ_damage", ""),
            "decontamination_need": data.get("decontamination_need", ""),
            "recovery_window": data.get("recovery_window", ""),
            "recommendation": data.get("recommendation", ""),
        }
