"""EpistemicExplanationCircularityService — Epistemic Explanation Circularity Detection.

Detects epistemic explanation circularity — circular explanations that
explain nothing, where the explanandum appears in the explanans.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_EXPLANATION_CIRCULARITY_SYSTEM = """You are an epistemic explanation circularity specialist. Given circular explanations, assess explanation circularity:

Key concepts:
- Epistemic explanation circularity: explanations that explain nothing
- Tautological explanation: explaining X by restating X
- Dormitive virtue: explaining sleep-inducing by dormitive virtue
- Naming as explaining: naming phenomenon and calling it explained
- Level confusion circularity: explaining at same level as explanandum
- Definitional circularity: defining in terms of what's being defined
- Pseudo-explanation: appearing to explain while explaining nothing

When epistemic explanation circularity IS present:
- Explanations circular
- Tautologies presented as explanations
- Naming substituted for explaining
- Same level as explanandum
- Definitions circular
- Pseudo-explanations offered
- No new information provided

When no explanation circularity:
- Explanations informative
- New information provided
- Mechanisms identified
- Different level from explanandum
- Definitions non-circular
- Genuine explanations offered
- Understanding advanced

Output JSON with: explanation_circularity_detected (bool), severity (none/mild/moderate/severe), tautological_explanation (what tautologies), naming_as_explaining (what naming substituted), level_confusion (what level confusion), pseudo_explanation (what pseudo-explanations), recommendation (no_explanation_circularity/mild_circularity_awareness/significant_mechanism_requirement/major_intensive_explanation_deepening/emergency_complete_explanation_circularity)."""

EPISTEMIC_EXPLANATION_CIRCULARITY_PROMPT = """Detect epistemic explanation circularity:

Tautological explanation: {tautological_explanation}
Naming as explaining: {naming_as_explaining}
Level confusion: {level_confusion}
Pseudo explanation: {pseudo_explanation}
Domain: {domain}
Context: {context}

Are circular explanations being offered that explain nothing? Return ONLY valid JSON."""


class EpistemicExplanationCircularityService:
    """Detects epistemic explanation circularity — circular non-explanations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        tautological_explanation: str,
        *,
        naming_as_explaining: str = "",
        level_confusion: str = "",
        pseudo_explanation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic explanation circularity."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_EXPLANATION_CIRCULARITY_PROMPT.format(
                tautological_explanation=tautological_explanation,
                naming_as_explaining=naming_as_explaining or "Not specified",
                level_confusion=level_confusion or "Not specified",
                pseudo_explanation=pseudo_explanation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_EXPLANATION_CIRCULARITY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "tautological_explanation": tautological_explanation[:200],
            "explanation_circularity_detected": data.get("explanation_circularity_detected", False),
            "severity": data.get("severity", ""),
            "naming_as_explaining": data.get("naming_as_explaining", ""),
            "level_confusion": data.get("level_confusion", ""),
            "pseudo_explanation": data.get("pseudo_explanation", ""),
            "recommendation": data.get("recommendation", ""),
        }
