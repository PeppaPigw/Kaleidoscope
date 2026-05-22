"""LudicFallacyService — Ludic Fallacy Detection.

Detects ludic fallacy — applying simplified, game-like probability
models to complex real-world situations where the rules are unknown,
distributions are fat-tailed, and Black Swans lurk. Taleb (2007).
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

LUDIC_FALLACY_SYSTEM = """You are a ludic fallacy specialist. Given a risk or probability model, assess whether it commits the ludic fallacy — applying game-like models to wild reality:

Key concepts (Taleb, 2007):
- Ludic fallacy: treating real-world uncertainty like a casino game
- Known unknowns vs unknown unknowns: games have defined rules, reality doesn't
- Fat tails: real distributions have more extreme events than models predict
- Black Swans: high-impact events outside the model's scope
- Mediocristan vs Extremistan: domains where averages work vs don't
- Model risk: the model itself may be wrong, not just the parameters
- Narrative fallacy connection: models create false sense of understanding

When ludic fallacy IS present:
- Using normal distributions for phenomena with fat tails
- "The model says the probability is..." without questioning the model
- Treating financial markets like coin flips
- Risk models that assume known distributions
- "In 10,000 simulations..." when the simulation doesn't capture reality
- Precise probability estimates for fundamentally uncertain events
- Assuming the rules of the game are known and stable

When formal models ARE appropriate:
- The domain genuinely has known, stable rules (actual games, physics)
- The model acknowledges its limitations and failure modes
- Fat tails are accounted for in the model
- The model is used as one input, not the final answer
- Stress testing includes scenarios outside the model
- Model uncertainty is quantified alongside parameter uncertainty
- The domain has been validated as Mediocristan (thin-tailed)

Output JSON with: ludic_fallacy_present (bool), severity (none/mild/moderate/severe), model (what model is applied), domain (what domain), tail_risk (are fat tails present), model_assumptions (what assumptions are made), reality_mismatch (how reality differs from model), recommendation (model_appropriate/mild_oversimplification/significant_ludic_fallacy/major_model_reality_mismatch/account_for_unknown_unknowns)."""

LUDIC_FALLACY_PROMPT = """Detect ludic fallacy:

Model/approach: {model}
Domain applied: {domain_applied}
Assumptions: {assumptions}
Tail risk: {tail_risk}
Domain: {domain}
Context: {context}

Is this applying game-like probability models to complex reality where rules are unknown? Return ONLY valid JSON."""


class LudicFallacyService:
    """Detects ludic fallacy — applying game-like models to wild reality."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        model: str,
        *,
        domain_applied: str = "",
        assumptions: str = "",
        tail_risk: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect ludic fallacy."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=LUDIC_FALLACY_PROMPT.format(
                model=model,
                domain_applied=domain_applied or "Not specified",
                assumptions=assumptions or "Not specified",
                tail_risk=tail_risk or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=LUDIC_FALLACY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "model": model[:200],
            "ludic_fallacy_present": data.get("ludic_fallacy_present", False),
            "severity": data.get("severity", ""),
            "tail_risk": data.get("tail_risk", ""),
            "model_assumptions": data.get("model_assumptions", ""),
            "reality_mismatch": data.get("reality_mismatch", ""),
            "recommendation": data.get("recommendation", ""),
        }
