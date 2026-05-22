"""DefaultBiasService — Default Bias Detection.

Detects default bias — when default options disproportionately
influence choices regardless of whether the default is optimal.
People tend to stick with defaults due to inertia, implied
endorsement, or effort avoidance.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

DEFAULT_BIAS_SYSTEM = """You are a default bias specialist. Given a choice situation, assess whether defaults are disproportionately influencing decisions:

Key concepts:
- Default effect: people stick with pre-selected options
- Implied endorsement: defaults seem recommended
- Effort asymmetry: changing from default requires effort
- Status quo as default: current state is the implicit default
- Opt-in vs opt-out: framing dramatically changes participation
- Nudge architecture: defaults as behavioral interventions
- Active choice: requiring explicit selection eliminates default bias

When default bias IS present:
- Choice heavily influenced by which option is pre-selected
- Default accepted without evaluation of alternatives
- Implied endorsement of default not questioned
- Effort to change from default preventing better choices
- Different defaults would produce different outcomes
- No active evaluation of whether default is optimal
- Inertia rather than preference driving the choice

When default bias is NOT present:
- Active evaluation of all options regardless of default
- Default questioned and alternatives considered
- Choice would be the same regardless of which option was default
- Effort to change is not a barrier
- Decision based on merit, not pre-selection
- Awareness of default effect and compensation for it
- Active choice made rather than passive acceptance

Output JSON with: default_bias (bool), severity (none/mild/moderate/severe), default_option (what the default is), chosen (what was chosen), evaluation (whether alternatives were evaluated), effort_barrier (whether effort prevents changing), recommendation (active_choice/mild_default_influence/significant_default_bias/major_passive_acceptance/require_active_selection)."""

DEFAULT_BIAS_PROMPT = """Detect default bias:

Choice: {choice}
Default option: {default}
Alternatives: {alternatives}
Evaluation process: {evaluation}
Domain: {domain}
Context: {context}

Is the default disproportionately influencing this choice? Return ONLY valid JSON."""


class DefaultBiasService:
    """Detects default bias — defaults disproportionately influencing choices."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        choice: str,
        *,
        default: str = "",
        alternatives: str = "",
        evaluation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect default bias."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=DEFAULT_BIAS_PROMPT.format(
                choice=choice,
                default=default or "Not specified",
                alternatives=alternatives or "Not specified",
                evaluation=evaluation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=DEFAULT_BIAS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "choice": choice[:200],
            "default_bias": data.get("default_bias", False),
            "severity": data.get("severity", ""),
            "default_option": data.get("default_option", ""),
            "evaluation": data.get("evaluation", ""),
            "effort_barrier": data.get("effort_barrier", ""),
            "recommendation": data.get("recommendation", ""),
        }
