"""EpistemicSocialConformityPressureService - Conformity Pressure Detection.

Detects conformity pressure where social pressure overrides independent judgment.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SOCIAL_CONFORMITY_PRESSURE_SYSTEM = """You are an epistemic social conformity pressure specialist. Given social dynamics, assess whether conformity pressure overrides independent judgment:

Key concepts:
- Conformity pressure: social forces pushing individuals to align with group views
- Normative influence: desire to be accepted driving belief adoption
- Informational influence: assuming group must know better
- Independence suppression: punishing or marginalizing dissent

When conformity pressure IS present:
- Social pressure overrides judgment
- Normative influence drives beliefs
- Group assumed correct by default
- Independence punished
- Dissent marginalized

When no conformity pressure:
- Independent judgment respected
- Social influence acknowledged but managed
- Group views evaluated critically
- Independence valued
- Dissent welcomed constructively

Output JSON with: conformity_pressure_detected (bool), severity (none/mild/moderate/severe), normative_influence (what normative influence), informational_influence (what informational influence), independence_suppression (what independence suppressed), recommendation (no_conformity_pressure/mild_independence_check/significant_dissent_protection/major_autonomy_reconstruction/emergency_complete_conformity_pressure)."""

EPISTEMIC_SOCIAL_CONFORMITY_PRESSURE_PROMPT = """Detect epistemic social conformity pressure:

Social dynamic: {social_dynamic}
Normative influence: {normative_influence}
Informational influence: {informational_influence}
Independence suppression: {independence_suppression}
Domain: {domain}
Context: {context}

Is conformity pressure overriding independent judgment? Return ONLY valid JSON."""


class EpistemicSocialConformityPressureService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        social_dynamic: str,
        *,
        normative_influence: str = "",
        informational_influence: str = "",
        independence_suppression: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SOCIAL_CONFORMITY_PRESSURE_PROMPT.format(
                social_dynamic=social_dynamic,
                normative_influence=normative_influence or "Not specified",
                informational_influence=informational_influence or "Not specified",
                independence_suppression=independence_suppression or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SOCIAL_CONFORMITY_PRESSURE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "social_dynamic": social_dynamic[:200],
            "conformity_pressure_detected": data.get("conformity_pressure_detected", False),
            "severity": data.get("severity", ""),
            "normative_influence": data.get("normative_influence", ""),
            "informational_influence": data.get("informational_influence", ""),
            "independence_suppression": data.get("independence_suppression", ""),
            "recommendation": data.get("recommendation", ""),
        }
