"""EpistemicComplexityLinearThinkingService — Epistemic Complexity Linear Thinking Detection.

Detects epistemic complexity linear thinking — assuming linear relationships
in systems that exhibit nonlinear dynamics, thresholds, and tipping points.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_COMPLEXITY_LINEAR_THINKING_SYSTEM = """You are an epistemic complexity linear thinking specialist. Given linear assumptions, assess nonlinearity blindness:

Key concepts:
- Epistemic linear thinking: assuming proportional cause-effect in nonlinear systems
- Threshold blindness: missing tipping points and phase transitions
- Proportionality assumption: assuming effects proportional to causes
- Extrapolation error: linearly extrapolating nonlinear trends
- Diminishing returns blindness: missing saturation effects
- Exponential blindness: underestimating exponential growth/decay
- Interaction neglect: missing how variables interact nonlinearly

When epistemic linear thinking IS present:
- Linear relationships assumed
- Thresholds missed
- Proportionality assumed
- Linear extrapolation applied
- Saturation effects missed
- Exponential growth underestimated
- Interactions neglected

When no linear thinking bias:
- Nonlinearity considered
- Thresholds identified
- Proportionality tested
- Extrapolation bounded
- Saturation recognized
- Exponential dynamics modeled
- Interactions mapped

Output JSON with: linear_thinking_detected (bool), severity (none/mild/moderate/severe), threshold_blindness (what thresholds missed), proportionality_assumption (what proportionality assumed), exponential_blindness (what exponential underestimated), interaction_neglect (what interactions missed), recommendation (no_linear_thinking/mild_nonlinearity_awareness/significant_threshold_mapping/major_intensive_systems_modeling/emergency_complete_linear_thinking)."""

EPISTEMIC_COMPLEXITY_LINEAR_THINKING_PROMPT = """Detect epistemic complexity linear thinking:

Threshold blindness: {threshold_blindness}
Proportionality assumption: {proportionality_assumption}
Exponential blindness: {exponential_blindness}
Interaction neglect: {interaction_neglect}
Domain: {domain}
Context: {context}

Are linear relationships being assumed in nonlinear systems? Return ONLY valid JSON."""


class EpistemicComplexityLinearThinkingService:
    """Detects epistemic complexity linear thinking — nonlinearity blindness."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        threshold_blindness: str,
        *,
        proportionality_assumption: str = "",
        exponential_blindness: str = "",
        interaction_neglect: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic complexity linear thinking."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_COMPLEXITY_LINEAR_THINKING_PROMPT.format(
                threshold_blindness=threshold_blindness,
                proportionality_assumption=proportionality_assumption or "Not specified",
                exponential_blindness=exponential_blindness or "Not specified",
                interaction_neglect=interaction_neglect or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_COMPLEXITY_LINEAR_THINKING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "threshold_blindness": threshold_blindness[:200],
            "linear_thinking_detected": data.get("linear_thinking_detected", False),
            "severity": data.get("severity", ""),
            "proportionality_assumption": data.get("proportionality_assumption", ""),
            "exponential_blindness": data.get("exponential_blindness", ""),
            "interaction_neglect": data.get("interaction_neglect", ""),
            "recommendation": data.get("recommendation", ""),
        }
