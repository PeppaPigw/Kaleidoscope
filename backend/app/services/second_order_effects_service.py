"""SecondOrderEffectsService — Second-Order Effects Detection.

Detects failure to consider second-order effects — the consequences
of consequences. First-order thinking considers only immediate effects;
second-order thinking traces the chain of downstream impacts that
often dominate the long-term outcome.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

SECOND_ORDER_SYSTEM = """You are a second-order effects specialist. Given a decision or analysis, assess whether it fails to consider downstream effects beyond the immediate impact:

Key concepts:
- First-order effects: immediate, direct consequences
- Second-order effects: consequences of consequences
- Third-order effects: further downstream ripples
- Systems thinking: understanding interconnections and feedback
- Temporal myopia: seeing only short-term effects
- Cascade effects: small changes amplifying through systems
- Equilibrium shifts: how systems settle into new states

When second-order neglect IS present:
- Analysis considers only immediate effects
- "If we do X, then Y" without asking "and then what?"
- Ignoring how other actors will respond to the change
- Not considering feedback loops or equilibrium effects
- Short-term gains that create long-term problems
- Failing to trace causal chains beyond one step
- Ignoring how the system will adapt to the intervention

When analysis IS sufficiently deep:
- Multiple orders of effects are explicitly considered
- Feedback loops are identified and analyzed
- Adaptive responses of other actors are anticipated
- Long-term equilibrium effects are considered
- The analysis asks "and then what?" iteratively
- System dynamics are modeled or reasoned about
- Both intended and unintended downstream effects are mapped

Output JSON with: second_order_neglect_present (bool), severity (none/mild/moderate/severe), decision (what decision is analyzed), first_order (immediate effects considered), second_order (downstream effects missed), feedback_loops (feedback effects ignored), adaptive_responses (how others will respond), recommendation (analysis_deep/mild_first_order_thinking/significant_second_order_neglect/major_systems_blindness/trace_downstream_effects)."""

SECOND_ORDER_PROMPT = """Detect second-order effects neglect:

Decision: {decision}
Analysis depth: {analysis}
First-order effects: {first_order}
System complexity: {complexity}
Domain: {domain}
Context: {context}

Does this analysis fail to consider downstream effects beyond the immediate impact? Return ONLY valid JSON."""


class SecondOrderEffectsService:
    """Detects failure to consider second-order effects — consequences of consequences."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        decision: str,
        *,
        analysis: str = "",
        first_order: str = "",
        complexity: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect second-order effects neglect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=SECOND_ORDER_PROMPT.format(
                decision=decision,
                analysis=analysis or "Not specified",
                first_order=first_order or "Not specified",
                complexity=complexity or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=SECOND_ORDER_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "decision": decision[:200],
            "second_order_neglect_present": data.get("second_order_neglect_present", False),
            "severity": data.get("severity", ""),
            "first_order": data.get("first_order", ""),
            "second_order": data.get("second_order", ""),
            "feedback_loops": data.get("feedback_loops", ""),
            "adaptive_responses": data.get("adaptive_responses", ""),
            "recommendation": data.get("recommendation", ""),
        }
