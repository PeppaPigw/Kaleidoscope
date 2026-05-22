"""InfohazardDetectService — Information Hazard Detection.

Detects infohazards — situations where the information itself
could cause harm if spread, regardless of intent. Bostrom (2011).
Some truths are dangerous not because they're false but because
knowing them enables harm. Detecting when sharing information
requires weighing truth-value against potential for misuse.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

INFOHAZARD_SYSTEM = """You are an information hazard specialist. Given information being shared or considered, assess whether the information itself could cause harm if spread:

Key concepts (Bostrom, 2011):
- Infohazard: information that causes harm by being known
- Dual-use information: knowledge with both beneficial and harmful applications
- Attention hazard: drawing attention to something increases risk
- Idea hazard: concepts that are harmful once conceived
- Knowledge asymmetry: information that benefits attackers more than defenders
- Streisand effect: suppression attempts that amplify spread
- Responsible disclosure: managing timing and audience of information

Types of infohazards:
- Technical: how to create weapons, exploit vulnerabilities
- Social: information that enables manipulation or discrimination
- Psychological: ideas that cause distress once known
- Strategic: information that shifts power dynamics dangerously
- Attention: drawing attention to exploitable vulnerabilities
- Norm: information that normalizes harmful behavior

When infohazard concern IS warranted:
- Information enables harm that couldn't occur without it
- The information asymmetrically benefits bad actors
- Sharing increases risk without proportional benefit
- The audience includes potential bad actors
- No defensive use justifies the offensive potential
- Timing of release matters for safety

When sharing IS appropriate:
- Defensive value exceeds offensive potential
- The information is already widely available
- Responsible disclosure protocols are followed
- The audience is restricted to those who need it
- Benefits of transparency outweigh risks
- Suppression would cause more harm than sharing

Output JSON with: infohazard_present (bool), severity (none/mild/moderate/severe), information (what information is at issue), harm_mechanism (how could this information cause harm), beneficiaries_of_knowledge (who benefits from knowing), potential_misuse (how could it be misused), availability (is it already widely known), defensive_value (does knowing help defense), recommendation (sharing_appropriate/mild_caution_needed/significant_infohazard/major_information_risk/restrict_or_delay_sharing)."""

INFOHAZARD_PROMPT = """Detect information hazard:

Information: {information}
Sharing context: {sharing_context}
Audience: {audience}
Potential harm: {potential_harm}
Domain: {domain}
Context: {context}

Could this information cause harm if spread, regardless of intent? Return ONLY valid JSON."""


class InfohazardDetectService:
    """Detects infohazards — information that could cause harm if spread."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        information: str,
        *,
        sharing_context: str = "",
        audience: str = "",
        potential_harm: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect information hazard."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=INFOHAZARD_PROMPT.format(
                information=information,
                sharing_context=sharing_context or "Not specified",
                audience=audience or "Not specified",
                potential_harm=potential_harm or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=INFOHAZARD_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "information": information[:200],
            "infohazard_present": data.get("infohazard_present", False),
            "severity": data.get("severity", ""),
            "harm_mechanism": data.get("harm_mechanism", ""),
            "beneficiaries_of_knowledge": data.get("beneficiaries_of_knowledge", ""),
            "potential_misuse": data.get("potential_misuse", ""),
            "availability": data.get("availability", ""),
            "defensive_value": data.get("defensive_value", ""),
            "recommendation": data.get("recommendation", ""),
        }
