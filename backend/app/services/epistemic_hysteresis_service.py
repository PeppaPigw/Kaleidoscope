"""EpistemicHysteresisService — Epistemic Hysteresis Detection.

Detects epistemic hysteresis — intellectual state depending not just on
current input but on the history of past inputs, creating path-dependent behavior.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_HYSTERESIS_SYSTEM = """You are an epistemic hysteresis specialist. Given an intellectual state transition, assess whether history creates path-dependent behavior:

Key concepts:
- Epistemic hysteresis: state depending on input history
- Path dependence: different paths to same input yield different states
- Threshold asymmetry: different thresholds for forward vs reverse
- Memory effect: system remembering past states
- Backlash: dead zone where input changes without output change
- Remanence: residual state after input removed
- Coercivity: input needed to overcome remanence

When epistemic hysteresis IS present:
- State depending on history of past inputs
- Different paths yielding different current states
- Different thresholds for adopting vs abandoning
- System remembering where it has been
- Dead zones where evidence doesn't change position
- Residual beliefs after evidence removed
- Effort needed to overcome residual beliefs

When memoryless operation is present:
- State depending only on current input
- Same input always yields same state
- Symmetric thresholds in both directions
- No memory of past states
- Immediate response to all input changes
- No residual effects
- No overcoming effort needed

Output JSON with: hysteresis_present (bool), severity (none/mild/moderate/severe), path_dependence (what history effect), threshold_asymmetry (what different thresholds), remanence (what residual state), coercivity (what overcoming effort), recommendation (memoryless_operation/mild_hysteresis/significant_hysteresis/major_path_dependence/reduce_remanence)."""

EPISTEMIC_HYSTERESIS_PROMPT = """Detect epistemic hysteresis:

Path dependence: {path_dependence}
Threshold asymmetry: {threshold_asymmetry}
Remanence: {remanence}
Coercivity: {coercivity}
Domain: {domain}
Context: {context}

Does the intellectual state depend not just on current input but on the history of past inputs, creating path-dependent behavior? Return ONLY valid JSON."""


class EpistemicHysteresisService:
    """Detects epistemic hysteresis — path-dependent intellectual state."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        path_dependence: str,
        *,
        threshold_asymmetry: str = "",
        remanence: str = "",
        coercivity: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic hysteresis."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_HYSTERESIS_PROMPT.format(
                path_dependence=path_dependence,
                threshold_asymmetry=threshold_asymmetry or "Not specified",
                remanence=remanence or "Not specified",
                coercivity=coercivity or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_HYSTERESIS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "path_dependence": path_dependence[:200],
            "hysteresis_present": data.get("hysteresis_present", False),
            "severity": data.get("severity", ""),
            "threshold_asymmetry": data.get("threshold_asymmetry", ""),
            "remanence": data.get("remanence", ""),
            "coercivity": data.get("coercivity", ""),
            "recommendation": data.get("recommendation", ""),
        }
