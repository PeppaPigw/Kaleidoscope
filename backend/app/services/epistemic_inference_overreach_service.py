"""EpistemicInferenceOverreachService — Epistemic Inference Overreach Detection.

Detects epistemic inference overreach — drawing conclusions that go
beyond what the evidence actually supports.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_INFERENCE_OVERREACH_SYSTEM = """You are an epistemic inference overreach specialist. Given conclusions exceeding evidence, assess inference overreach:

Key concepts:
- Epistemic inference overreach: conclusions going beyond evidence
- Overgeneralization: generalizing beyond data scope
- Certainty inflation: claiming more certainty than warranted
- Scope expansion: expanding conclusion scope beyond evidence scope
- Causal overclaiming: claiming causation from correlation
- Universal from particular: deriving universal from particular cases
- Necessity from contingency: claiming necessity from contingent observations

When epistemic inference overreach IS present:
- Conclusions exceed evidence
- Overgeneralization present
- Certainty inflated
- Scope expanded beyond evidence
- Causation overclaimed
- Universal derived from particular
- Necessity claimed from contingency

When no inference overreach:
- Conclusions match evidence
- Generalization bounded
- Certainty calibrated
- Scope appropriate
- Causal claims warranted
- Generality appropriate
- Modality appropriate

Output JSON with: inference_overreach_detected (bool), severity (none/mild/moderate/severe), overgeneralization (what overgeneralized), certainty_inflation (what certainty inflated), scope_expansion (what scope expanded), causal_overclaiming (what causation overclaimed), recommendation (no_inference_overreach/mild_scope_awareness/significant_conclusion_bounding/major_intensive_evidence_matching/emergency_complete_inference_overreach)."""

EPISTEMIC_INFERENCE_OVERREACH_PROMPT = """Detect epistemic inference overreach:

Overgeneralization: {overgeneralization}
Certainty inflation: {certainty_inflation}
Scope expansion: {scope_expansion}
Causal overclaiming: {causal_overclaiming}
Domain: {domain}
Context: {context}

Are conclusions going beyond what evidence actually supports? Return ONLY valid JSON."""


class EpistemicInferenceOverreachService:
    """Detects epistemic inference overreach — conclusions exceeding evidence."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        overgeneralization: str,
        *,
        certainty_inflation: str = "",
        scope_expansion: str = "",
        causal_overclaiming: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic inference overreach."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_INFERENCE_OVERREACH_PROMPT.format(
                overgeneralization=overgeneralization,
                certainty_inflation=certainty_inflation or "Not specified",
                scope_expansion=scope_expansion or "Not specified",
                causal_overclaiming=causal_overclaiming or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_INFERENCE_OVERREACH_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "overgeneralization": overgeneralization[:200],
            "inference_overreach_detected": data.get("inference_overreach_detected", False),
            "severity": data.get("severity", ""),
            "certainty_inflation": data.get("certainty_inflation", ""),
            "scope_expansion": data.get("scope_expansion", ""),
            "causal_overclaiming": data.get("causal_overclaiming", ""),
            "recommendation": data.get("recommendation", ""),
        }
