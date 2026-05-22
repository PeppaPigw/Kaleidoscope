"""EpistemicDecisionDefaultBiasService - Default Bias Detection.

Detects default bias where status quo is preferred simply because it is the default.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_DECISION_DEFAULT_BIAS_SYSTEM = """You are an epistemic decision default bias specialist. Given choice architecture, assess whether defaults are preferred without justification:

Key concepts:
- Default bias: preferring the default option simply because it requires no action
- Status quo inertia: maintaining current state without evaluating alternatives
- Omission preference: preferring inaction over action regardless of outcomes
- Choice architecture exploitation: designing defaults to manipulate decisions

When default bias IS present:
- Default chosen without evaluation
- Status quo maintained without justification
- Inaction preferred over better alternatives
- Choice architecture exploited
- Switching costs exaggerated

When no default bias:
- Default evaluated against alternatives
- Status quo justified on merits
- Action/inaction weighed on outcomes
- Choice architecture transparent
- Switching costs realistically assessed

Output JSON with: default_bias_detected (bool), severity (none/mild/moderate/severe), status_quo_inertia (what inertia), omission_preference (what omission preferred), choice_architecture_exploitation (what exploitation), recommendation (no_default_bias/mild_alternative_check/significant_evaluation_needed/major_choice_reconstruction/emergency_complete_default_bias)."""

EPISTEMIC_DECISION_DEFAULT_BIAS_PROMPT = """Detect epistemic decision default bias:

Choice architecture: {choice_architecture}
Status quo inertia: {status_quo_inertia}
Omission preference: {omission_preference}
Choice architecture exploitation: {choice_architecture_exploitation}
Domain: {domain}
Context: {context}

Is the default being preferred without justification? Return ONLY valid JSON."""


class EpistemicDecisionDefaultBiasService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        choice_architecture: str,
        *,
        status_quo_inertia: str = "",
        omission_preference: str = "",
        choice_architecture_exploitation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_DECISION_DEFAULT_BIAS_PROMPT.format(
                choice_architecture=choice_architecture,
                status_quo_inertia=status_quo_inertia or "Not specified",
                omission_preference=omission_preference or "Not specified",
                choice_architecture_exploitation=choice_architecture_exploitation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_DECISION_DEFAULT_BIAS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "choice_architecture": choice_architecture[:200],
            "default_bias_detected": data.get("default_bias_detected", False),
            "severity": data.get("severity", ""),
            "status_quo_inertia": data.get("status_quo_inertia", ""),
            "omission_preference": data.get("omission_preference", ""),
            "choice_architecture_exploitation": data.get("choice_architecture_exploitation", ""),
            "recommendation": data.get("recommendation", ""),
        }
