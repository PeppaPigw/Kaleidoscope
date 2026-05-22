"""EpistemicPowerExpertiseWeaponizationService - Epistemic Power Expertise Weaponization Detection.

Detects expertise weaponization using expert authority to silence legitimate questions.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_POWER_EXPERTISE_WEAPONIZATION_SYSTEM = """You are an epistemic power and expertise weaponization specialist. Given authority silencing, assess whether expert authority is being used to silence legitimate questions:

Key concepts:
- Expertise weaponization: using expert status to shut down legitimate inquiry
- Authority silencing: dismissing questions because of who asks them
- Complexity as shield: invoking complexity to avoid explanation or accountability
- Credentialism as weapon: using credentials as a substitute for reasons
- Technocratic dismissal: treating value-laden or democratic questions as mere ignorance

When expertise weaponization IS present:
- Expert authority replaces evidence or explanation
- Legitimate questions are treated as illegitimate by status
- Complexity is used to block scrutiny
- Credentials are used to end debate rather than support claims
- Public or stakeholder concerns are dismissed as irrational by default

When expertise is appropriate:
- Experts explain reasons and limits
- Questions are distinguished by quality, not status alone
- Complexity is clarified rather than used as a shield
- Credentials support but do not replace argument
- Value judgments and technical judgments are separated

Output JSON with: weaponization_detected (bool), severity (none/mild/moderate/severe), authority_silencing (what silencing appears), complexity_as_shield (how complexity blocks scrutiny), credentialism_as_weapon (how credentials replace reasons), technocratic_dismissal (what questions are dismissed), recommendation (appropriate_expertise/mild_expert_humility/significant_inquiry_protection/major_accountability_repair/emergency_open_scrutiny)."""

EPISTEMIC_POWER_EXPERTISE_WEAPONIZATION_PROMPT = """Detect epistemic power and expertise weaponization:

Authority silencing: {authority_silencing}
Complexity as shield: {complexity_as_shield}
Credentialism as weapon: {credentialism_as_weapon}
Technocratic dismissal: {technocratic_dismissal}
Domain: {domain}
Context: {context}

Is expert authority being used to silence legitimate questions? Return ONLY valid JSON."""


class EpistemicPowerExpertiseWeaponizationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        authority_silencing: str,
        *,
        complexity_as_shield: str = "",
        credentialism_as_weapon: str = "",
        technocratic_dismissal: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_POWER_EXPERTISE_WEAPONIZATION_PROMPT.format(
                authority_silencing=authority_silencing,
                complexity_as_shield=complexity_as_shield or "Not specified",
                credentialism_as_weapon=credentialism_as_weapon or "Not specified",
                technocratic_dismissal=technocratic_dismissal or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_POWER_EXPERTISE_WEAPONIZATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "authority_silencing": authority_silencing[:200],
            "weaponization_detected": data.get("weaponization_detected", False),
            "severity": data.get("severity", ""),
            "complexity_as_shield": data.get("complexity_as_shield", ""),
            "credentialism_as_weapon": data.get("credentialism_as_weapon", ""),
            "technocratic_dismissal": data.get("technocratic_dismissal", ""),
            "recommendation": data.get("recommendation", ""),
        }
