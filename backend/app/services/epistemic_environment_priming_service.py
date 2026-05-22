"""EpistemicEnvironmentPrimingService — Epistemic Environment Priming Detection.

Detects epistemic environment priming — environmental cues priming
specific epistemic conclusions before evidence is considered.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ENVIRONMENT_PRIMING_SYSTEM = """You are an epistemic environment priming specialist. Given environmental cues priming conclusions, assess environment priming:

Key concepts:
- Epistemic environment priming: environmental cues priming specific conclusions
- Context priming: context priming certain interpretations
- Setting influence: physical/social setting influencing conclusions
- Framing environment: environment framing how problems are seen
- Ambient suggestion: ambient cues suggesting conclusions
- Institutional priming: institutional context priming beliefs
- Cultural priming: cultural environment priming interpretations

When epistemic environment priming IS present:
- Environmental cues priming conclusions
- Context priming interpretations
- Setting influencing conclusions
- Environment framing problems
- Ambient cues suggesting
- Institutional context priming
- Cultural environment priming

When no environment priming:
- Conclusions independent of environment
- Context not priming
- Setting not influencing
- Problems seen independently
- No ambient suggestion
- Institutional context recognized
- Cultural influence acknowledged

Output JSON with: environment_priming_detected (bool), severity (none/mild/moderate/severe), context_priming (what context priming), setting_influence (what setting influencing), institutional_priming (what institutional context priming), cultural_priming (what cultural environment priming), recommendation (no_environment_priming/mild_context_awareness/significant_decontextualization/major_intensive_environment_independence/emergency_complete_environment_priming)."""

EPISTEMIC_ENVIRONMENT_PRIMING_PROMPT = """Detect epistemic environment priming:

Context priming: {context_priming}
Setting influence: {setting_influence}
Institutional priming: {institutional_priming}
Cultural priming: {cultural_priming}
Domain: {domain}
Context: {context}

Are environmental cues priming specific epistemic conclusions? Return ONLY valid JSON."""


class EpistemicEnvironmentPrimingService:
    """Detects epistemic environment priming — environmental cues priming conclusions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        context_priming: str,
        *,
        setting_influence: str = "",
        institutional_priming: str = "",
        cultural_priming: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic environment priming."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ENVIRONMENT_PRIMING_PROMPT.format(
                context_priming=context_priming,
                setting_influence=setting_influence or "Not specified",
                institutional_priming=institutional_priming or "Not specified",
                cultural_priming=cultural_priming or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ENVIRONMENT_PRIMING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "context_priming": context_priming[:200],
            "environment_priming_detected": data.get("environment_priming_detected", False),
            "severity": data.get("severity", ""),
            "setting_influence": data.get("setting_influence", ""),
            "institutional_priming": data.get("institutional_priming", ""),
            "cultural_priming": data.get("cultural_priming", ""),
            "recommendation": data.get("recommendation", ""),
        }
