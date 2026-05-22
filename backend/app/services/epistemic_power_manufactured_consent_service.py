"""EpistemicPowerManufacturedConsentService - Epistemic Power Manufactured Consent Detection.

Detects manufactured consent through systematic opinion shaping.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_POWER_MANUFACTURED_CONSENT_SYSTEM = """You are an epistemic power and manufactured consent specialist. Given consent engineering, assess whether consent is being manufactured through systematic opinion shaping:

Key concepts:
- Manufactured consent: systematic engineering of public agreement
- Consent engineering: shaping preferences before consent is expressed
- Agenda setting power: controlling which issues receive attention
- Overton window manipulation: shifting what views seem acceptable
- False consensus creation: making engineered agreement look spontaneous

When manufactured consent IS present:
- Opinion is shaped before people deliberate freely
- Agenda control makes alternatives invisible
- Acceptable positions are narrowed by power
- Apparent consensus is produced through repetition or exclusion
- Dissent is framed as marginal, irrational, or nonexistent

When no manufactured consent:
- People encounter meaningful alternatives
- Agenda setting is transparent and contestable
- Disagreement is visible and fairly represented
- Consent follows informed deliberation
- Consensus emerges without systematic opinion control

Output JSON with: manufactured_consent_detected (bool), severity (none/mild/moderate/severe), consent_engineering (what consent engineering appears), agenda_setting_power (what agenda power operates), overton_window_manipulation (how acceptable opinion is shifted), false_consensus_creation (how false consensus is created), recommendation (no_manufacturing/mild_agenda_awareness/significant_consent_engineering/major_deliberative_repair/emergency_consent_reconstruction)."""

EPISTEMIC_POWER_MANUFACTURED_CONSENT_PROMPT = """Detect epistemic power and manufactured consent:

Consent engineering: {consent_engineering}
Agenda setting power: {agenda_setting_power}
Overton window manipulation: {overton_window_manipulation}
False consensus creation: {false_consensus_creation}
Domain: {domain}
Context: {context}

Is consent being manufactured through systematic opinion shaping? Return ONLY valid JSON."""


class EpistemicPowerManufacturedConsentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        consent_engineering: str,
        *,
        agenda_setting_power: str = "",
        overton_window_manipulation: str = "",
        false_consensus_creation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_POWER_MANUFACTURED_CONSENT_PROMPT.format(
                consent_engineering=consent_engineering,
                agenda_setting_power=agenda_setting_power or "Not specified",
                overton_window_manipulation=overton_window_manipulation or "Not specified",
                false_consensus_creation=false_consensus_creation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_POWER_MANUFACTURED_CONSENT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "consent_engineering": consent_engineering[:200],
            "manufactured_consent_detected": data.get("manufactured_consent_detected", False),
            "severity": data.get("severity", ""),
            "agenda_setting_power": data.get("agenda_setting_power", ""),
            "overton_window_manipulation": data.get("overton_window_manipulation", ""),
            "false_consensus_creation": data.get("false_consensus_creation", ""),
            "recommendation": data.get("recommendation", ""),
        }
