"""BizarrenessEffectService — Bizarreness Effect Detection.

Detects the bizarreness effect — unusual or bizarre information
being remembered better and thus given disproportionate weight
in decisions. McDaniel & Einstein (1986). Bizarre examples
stick in memory while mundane but important information fades.
The unusual case dominates thinking even when it's statistically
irrelevant.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

BIZARRENESS_EFFECT_SYSTEM = """You are a bizarreness effect specialist. Given a judgment or decision situation, assess whether unusual/bizarre information is being given disproportionate weight due to its memorability:

Key concepts (McDaniel & Einstein, 1986):
- Bizarreness effect: unusual items remembered better
- Salience through novelty: strange things grab attention
- Availability through distinctiveness: bizarre cases come to mind easily
- Von Restorff interaction: distinctive items stand out in memory
- Anecdote dominance: one bizarre story outweighs many normal cases
- Fear of the unusual: bizarre risks overweighted vs common risks
- Media bias amplification: news reports bizarre events, skewing perception

When the bizarreness effect IS distorting:
- One unusual case dominating decision-making over many typical cases
- Bizarre failure modes getting more attention than common ones
- Unusual anecdotes overriding statistical evidence
- "Remember that time when..." (bizarre event) driving policy
- Exotic risks getting more resources than mundane frequent risks
- Memorable outliers being treated as representative
- Strange edge cases consuming disproportionate planning effort

When attention to unusual cases IS appropriate:
- The unusual case reveals a genuine systemic vulnerability
- Bizarre outcomes signal previously unknown failure modes
- The unusual case is actually representative of a class of risks
- Novel threats genuinely require novel responses
- The bizarre case provides genuine diagnostic information

Output JSON with: bizarreness_effect_present (bool), severity (none/mild/moderate/severe), situation (what decision is being made), bizarre_info (what unusual information is dominating), mundane_info (what normal information is being underweighted), memorability_bias (how is memorability affecting judgment), base_rate (what is the actual frequency/importance), salience_distortion (how much is salience distorting), recommendation (attention_appropriate/mild_novelty_bias/significant_bizarreness_effect/major_anecdote_dominance/weight_by_frequency_not_memorability)."""

BIZARRENESS_EFFECT_PROMPT = """Detect bizarreness effect:

Situation: {situation}
Unusual information: {bizarre}
Normal information: {mundane}
Decision impact: {impact}
Domain: {domain}
Context: {context}

Is unusual/bizarre information being given disproportionate weight due to its memorability? Return ONLY valid JSON."""


class BizarrenessEffectService:
    """Detects bizarreness effect — unusual information distorting judgment through memorability."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        bizarre: str = "",
        mundane: str = "",
        impact: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect bizarreness effect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=BIZARRENESS_EFFECT_PROMPT.format(
                situation=situation,
                bizarre=bizarre or "Not specified",
                mundane=mundane or "Not specified",
                impact=impact or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=BIZARRENESS_EFFECT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "bizarreness_effect_present": data.get("bizarreness_effect_present", False),
            "severity": data.get("severity", ""),
            "bizarre_info": data.get("bizarre_info", ""),
            "mundane_info": data.get("mundane_info", ""),
            "memorability_bias": data.get("memorability_bias", ""),
            "base_rate": data.get("base_rate", ""),
            "salience_distortion": data.get("salience_distortion", ""),
            "recommendation": data.get("recommendation", ""),
        }
