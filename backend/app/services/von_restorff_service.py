"""VonRestorffService — Von Restorff (Isolation) Effect Detection.

Detects the Von Restorff effect — distinctive or isolated items
being remembered better and given disproportionate weight.
Von Restorff (1933). When one item in a list is different from
the rest, it's remembered better. This distinctiveness-driven
salience can distort judgment when the distinctive item isn't
actually the most important one.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

VON_RESTORFF_SYSTEM = """You are a Von Restorff effect specialist. Given a judgment or evaluation situation, assess whether distinctiveness is causing certain information to be overweighted:

Key concepts (Von Restorff, 1933):
- Von Restorff effect: distinctive items remembered better
- Isolation effect: items that stand out from context get attention
- Distinctiveness-based encoding: unique items encoded more deeply
- Salience through contrast: difference from surroundings drives attention
- Novelty capture: new/different things grab cognitive resources
- Figure-ground: distinctive items become figure, rest becomes ground
- Attention capture: perceptual distinctiveness drives processing

When the Von Restorff effect IS distorting:
- One distinctive data point dominating analysis of a uniform dataset
- The unusual case getting more weight than many typical cases
- Distinctive presentation making mediocre content seem important
- Standing out from the crowd being confused with being correct
- Contrarian positions getting attention disproportionate to merit
- The one different item in a list being assumed most important
- Novelty of an argument being confused with strength

When distinctiveness IS informative:
- The distinctive item genuinely signals something important
- Anomalies in data actually indicate meaningful patterns
- The outlier reveals a genuine flaw in the prevailing pattern
- Distinctiveness correlates with actual importance in this context
- The different item provides genuine diagnostic information

Output JSON with: von_restorff_present (bool), severity (none/mild/moderate/severe), situation (what is being evaluated), distinctive_item (what stands out), context_items (what is the background), distinctiveness_source (why does it stand out), actual_importance (is the distinctive item actually most important), attention_distortion (how is distinctiveness distorting attention), recommendation (distinctiveness_informative/mild_salience_bias/significant_von_restorff_effect/major_distinctiveness_dominance/weight_by_importance_not_distinctiveness)."""

VON_RESTORFF_PROMPT = """Detect Von Restorff effect:

Situation: {situation}
Distinctive item: {distinctive}
Background: {background}
Attention pattern: {attention}
Domain: {domain}
Context: {context}

Is distinctiveness causing certain information to receive disproportionate attention and weight? Return ONLY valid JSON."""


class VonRestorffService:
    """Detects Von Restorff effect — distinctiveness distorting information weighting."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        distinctive: str = "",
        background: str = "",
        attention: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect Von Restorff effect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=VON_RESTORFF_PROMPT.format(
                situation=situation,
                distinctive=distinctive or "Not specified",
                background=background or "Not specified",
                attention=attention or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=VON_RESTORFF_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "von_restorff_present": data.get("von_restorff_present", False),
            "severity": data.get("severity", ""),
            "distinctive_item": data.get("distinctive_item", ""),
            "context_items": data.get("context_items", ""),
            "distinctiveness_source": data.get("distinctiveness_source", ""),
            "actual_importance": data.get("actual_importance", ""),
            "attention_distortion": data.get("attention_distortion", ""),
            "recommendation": data.get("recommendation", ""),
        }
