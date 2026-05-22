"""EpistemicKnowledgeWeaponizationService — Epistemic Knowledge Weaponization Detection.

Detects epistemic knowledge weaponization — weaponizing knowledge
for power over others in intellectual exchanges.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_KNOWLEDGE_WEAPONIZATION_SYSTEM = """You are an epistemic knowledge weaponization specialist. Given weaponizing knowledge for power, assess knowledge weaponization:

Key concepts:
- Epistemic knowledge weaponization: weaponizing knowledge for power
- Strategic obscurity: using complexity to confuse and control
- Information asymmetry exploitation: leveraging what others don't know
- Jargon as weapon: using technical language to exclude
- Knowledge withholding: strategically not sharing to maintain power
- Gotcha deployment: saving knowledge to embarrass others
- Intellectual ambush: using knowledge to trap others

When epistemic knowledge weaponization IS present:
- Weaponizing knowledge for power
- Using complexity to confuse
- Leveraging information asymmetry
- Using jargon to exclude
- Strategically withholding
- Saving to embarrass
- Using to trap

When no knowledge weaponization:
- Knowledge shared generously
- Clarity as goal
- Reducing information gaps
- Using accessible language
- Sharing openly
- Supporting others' learning
- Using knowledge to empower

Output JSON with: knowledge_weaponization_detected (bool), severity (none/mild/moderate/severe), strategic_obscurity (what using to confuse), information_asymmetry_exploitation (what leveraging), jargon_as_weapon (what excluding with), gotcha_deployment (what saving to embarrass), recommendation (no_knowledge_weaponization/mild_generosity_practice/significant_sharing_work/major_intensive_power_processing/emergency_active_weaponization)."""

EPISTEMIC_KNOWLEDGE_WEAPONIZATION_PROMPT = """Detect epistemic knowledge weaponization:

Strategic obscurity: {strategic_obscurity}
Information asymmetry exploitation: {information_asymmetry_exploitation}
Jargon as weapon: {jargon_as_weapon}
Gotcha deployment: {gotcha_deployment}
Domain: {domain}
Context: {context}

Is there weaponizing knowledge for power over others? Return ONLY valid JSON."""


class EpistemicKnowledgeWeaponizationService:
    """Detects epistemic knowledge weaponization — weaponizing knowledge for power."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        strategic_obscurity: str,
        *,
        information_asymmetry_exploitation: str = "",
        jargon_as_weapon: str = "",
        gotcha_deployment: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic knowledge weaponization."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_KNOWLEDGE_WEAPONIZATION_PROMPT.format(
                strategic_obscurity=strategic_obscurity,
                information_asymmetry_exploitation=information_asymmetry_exploitation or "Not specified",
                jargon_as_weapon=jargon_as_weapon or "Not specified",
                gotcha_deployment=gotcha_deployment or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_KNOWLEDGE_WEAPONIZATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "strategic_obscurity": strategic_obscurity[:200],
            "knowledge_weaponization_detected": data.get("knowledge_weaponization_detected", False),
            "severity": data.get("severity", ""),
            "information_asymmetry_exploitation": data.get("information_asymmetry_exploitation", ""),
            "jargon_as_weapon": data.get("jargon_as_weapon", ""),
            "gotcha_deployment": data.get("gotcha_deployment", ""),
            "recommendation": data.get("recommendation", ""),
        }
