"""EpistemicCounterfactualDeficitService — Epistemic Counterfactual Deficit Detection.

Detects epistemic counterfactual deficit — inability to think counterfactually,
stuck in what-is without imagining alternatives.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_COUNTERFACTUAL_DEFICIT_SYSTEM = """You are an epistemic counterfactual deficit specialist. Given inability to think counterfactually, assess counterfactual deficit:

Key concepts:
- Epistemic counterfactual deficit: inability to imagine alternatives to what happened
- Imagination failure: cannot imagine things being different
- Necessity illusion: what happened seems like it had to happen
- Alternative blindness: cannot see alternative paths
- Deterministic thinking: everything seems determined in retrospect
- Learning failure: cannot learn from what-might-have-been
- Flexibility deficit: thinking inflexible about possibilities

When epistemic counterfactual deficit IS present:
- Cannot imagine alternatives
- Imagination failing
- What happened seems necessary
- Alternative paths invisible
- Thinking deterministic
- Learning from alternatives failing
- Thinking inflexible

When no counterfactual deficit:
- Alternatives imagined readily
- Imagination active
- Contingency recognized
- Alternative paths visible
- Thinking probabilistic
- Learning from alternatives active
- Thinking flexible

Output JSON with: counterfactual_deficit_detected (bool), severity (none/mild/moderate/severe), imagination_failure (what imagination failing), necessity_illusion (what seems necessary), alternative_blindness (what alternatives missed), deterministic_thinking (what seems determined), recommendation (no_counterfactual_deficit/mild_imagination_practice/significant_alternative_generation/major_intensive_possibility_training/emergency_complete_counterfactual_deficit)."""

EPISTEMIC_COUNTERFACTUAL_DEFICIT_PROMPT = """Detect epistemic counterfactual deficit:

Imagination failure: {imagination_failure}
Necessity illusion: {necessity_illusion}
Alternative blindness: {alternative_blindness}
Deterministic thinking: {deterministic_thinking}
Domain: {domain}
Context: {context}

Is there inability to think counterfactually — stuck in what-is? Return ONLY valid JSON."""


class EpistemicCounterfactualDeficitService:
    """Detects epistemic counterfactual deficit — cannot imagine alternatives."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        imagination_failure: str,
        *,
        necessity_illusion: str = "",
        alternative_blindness: str = "",
        deterministic_thinking: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic counterfactual deficit."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_COUNTERFACTUAL_DEFICIT_PROMPT.format(
                imagination_failure=imagination_failure,
                necessity_illusion=necessity_illusion or "Not specified",
                alternative_blindness=alternative_blindness or "Not specified",
                deterministic_thinking=deterministic_thinking or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_COUNTERFACTUAL_DEFICIT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "imagination_failure": imagination_failure[:200],
            "counterfactual_deficit_detected": data.get("counterfactual_deficit_detected", False),
            "severity": data.get("severity", ""),
            "necessity_illusion": data.get("necessity_illusion", ""),
            "alternative_blindness": data.get("alternative_blindness", ""),
            "deterministic_thinking": data.get("deterministic_thinking", ""),
            "recommendation": data.get("recommendation", ""),
        }
