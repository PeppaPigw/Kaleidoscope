"""EpistemicDecisionArchitectureDefaultBiasService — Default Bias Detection.

Detects over-reliance on default options regardless of fit.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_DECISION_ARCHITECTURE_DEFAULT_BIAS_SYSTEM = """You are an epistemic decision architecture default bias specialist. Given status quo preference, assess whether default options are being over-relied on regardless of fit:

Key concepts:
- Default bias: choosing preselected or existing options because they are defaults
- Status quo preference: preferring the current state despite weak fit
- Opt-out friction: effort, confusion, or cost required to reject the default
- Inertia exploitation: using passivity to secure a choice
- Default as recommendation: treating the default as expert endorsement

When default bias IS present:
- Defaults are accepted without fit evaluation
- Status quo preference substitutes for comparison
- Opt-out friction makes alternatives costly
- Inertia is exploited to shape choices
- Defaults are interpreted as recommendations without evidence

When no default bias:
- Defaults are evaluated against user needs and goals
- Opt-out paths are clear and low-friction
- Alternatives are visible and comparable
- Default rationale is explicit

Output JSON with: default_bias_detected (bool), severity (none/mild/moderate/severe), opt_out_friction (how opt-out friction appears), inertia_exploitation (how inertia is exploited), default_as_recommendation (how default is treated as recommendation), recommendation (no_default_bias/mild_default_review/significant_opt_out_reduction/major_default_redesign/emergency_default_removal)."""

EPISTEMIC_DECISION_ARCHITECTURE_DEFAULT_BIAS_PROMPT = """Detect decision architecture default bias:

Status quo preference: {status_quo_preference}
Opt out friction: {opt_out_friction}
Inertia exploitation: {inertia_exploitation}
Default as recommendation: {default_as_recommendation}
Domain: {domain}
Context: {context}

Are default options being over-relied on regardless of fit? Return ONLY valid JSON."""


class EpistemicDecisionArchitectureDefaultBiasService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        status_quo_preference: str,
        *,
        opt_out_friction: str = "",
        inertia_exploitation: str = "",
        default_as_recommendation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_DECISION_ARCHITECTURE_DEFAULT_BIAS_PROMPT.format(
                status_quo_preference=status_quo_preference,
                opt_out_friction=opt_out_friction or "Not specified",
                inertia_exploitation=inertia_exploitation or "Not specified",
                default_as_recommendation=default_as_recommendation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_DECISION_ARCHITECTURE_DEFAULT_BIAS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "status_quo_preference": status_quo_preference[:200],
            "default_bias_detected": data.get("default_bias_detected", False),
            "severity": data.get("severity", ""),
            "opt_out_friction": data.get("opt_out_friction", ""),
            "inertia_exploitation": data.get("inertia_exploitation", ""),
            "default_as_recommendation": data.get("default_as_recommendation", ""),
            "recommendation": data.get("recommendation", ""),
        }
