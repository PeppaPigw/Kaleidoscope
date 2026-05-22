"""HindsightDeterminismService — Hindsight Determinism Detection.

Detects hindsight determinism — treating what happened as what had
to happen, seeing historical outcomes as inevitable rather than
contingent, removing agency and chance from explanations.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

HINDSIGHT_DETERMINISM_SYSTEM = """You are a hindsight determinism specialist. Given a historical or causal explanation, assess whether outcomes are being treated as inevitable:

Key concepts:
- Hindsight determinism: treating outcomes as inevitable after the fact
- Inevitability illusion: what happened had to happen
- Contingency denial: removing chance and choice from history
- Teleological history: history moving toward predetermined end
- Path not taken: alternative outcomes that were possible
- Agency erasure: removing human choice from explanations
- Structural determinism: treating structures as fully determining outcomes

When hindsight determinism IS present:
- Outcomes treated as inevitable after they occurred
- Alternative possibilities dismissed or invisible
- Contingency and chance removed from explanation
- History presented as moving toward predetermined end
- Agency of actors minimized or erased
- Structural factors treated as fully determining
- 'It was bound to happen' reasoning

When deterministic explanation is appropriate:
- Strong structural constraints genuinely limited options
- Contingency acknowledged alongside structural factors
- Alternative possibilities discussed
- Probability language used rather than inevitability
- Agency preserved within constraints
- Determinism is a hypothesis being tested, not assumed
- Degree of contingency vs. determination assessed

Output JSON with: determinism_present (bool), severity (none/mild/moderate/severe), explanation (what is explained), outcome_treated (how outcome is treated), contingencies_ignored (what contingencies are missed), alternatives (what alternatives were possible), recommendation (appropriate_structural_analysis/mild_inevitability_language/significant_hindsight_determinism/major_contingency_denial/acknowledge_contingency)."""

HINDSIGHT_DETERMINISM_PROMPT = """Detect hindsight determinism:

Explanation: {explanation}
Outcome: {outcome}
Alternatives: {alternatives}
Contingencies: {contingencies}
Domain: {domain}
Context: {context}

Is the outcome being treated as inevitable rather than contingent? Return ONLY valid JSON."""


class HindsightDeterminismService:
    """Detects hindsight determinism — treating outcomes as inevitable."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        explanation: str,
        *,
        outcome: str = "",
        alternatives: str = "",
        contingencies: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect hindsight determinism."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=HINDSIGHT_DETERMINISM_PROMPT.format(
                explanation=explanation,
                outcome=outcome or "Not specified",
                alternatives=alternatives or "Not specified",
                contingencies=contingencies or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=HINDSIGHT_DETERMINISM_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "explanation": explanation[:200],
            "determinism_present": data.get("determinism_present", False),
            "severity": data.get("severity", ""),
            "outcome_treated": data.get("outcome_treated", ""),
            "contingencies_ignored": data.get("contingencies_ignored", ""),
            "alternatives": data.get("alternatives", ""),
            "recommendation": data.get("recommendation", ""),
        }
