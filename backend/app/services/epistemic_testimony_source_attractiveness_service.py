"""EpistemicTestimonySourceAttractivenessService — Epistemic Testimony Source Attractiveness Detection.

Detects epistemic testimony source attractiveness — evaluating testimony based on
source attractiveness or likability rather than evidence quality or expertise.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_TESTIMONY_SOURCE_ATTRACTIVENESS_SYSTEM = """You are an epistemic testimony source attractiveness specialist. Given attractiveness-biased testimony evaluation, assess distortion:

Key concepts:
- Epistemic source attractiveness: likability affecting credibility assessment
- Halo effect testimony: attractive sources given more credibility
- Charisma bias: charismatic delivery substituting for evidence
- Likability credibility: liked sources believed more readily
- Appearance authority: professional appearance creating assumed expertise
- Fluency credibility: articulate speakers assumed more knowledgeable
- Similarity bias: similar sources trusted more regardless of expertise

When epistemic source attractiveness IS present:
- Likability affecting credibility
- Attractive sources given more weight
- Charisma substituting for evidence
- Liked sources believed more
- Appearance creating authority
- Fluency assumed as knowledge
- Similarity driving trust

When no source attractiveness bias:
- Credibility based on evidence
- Attractiveness irrelevant
- Charisma separated from evidence
- Belief based on quality
- Appearance not conflated with expertise
- Fluency not assumed as knowledge
- Trust based on track record

Output JSON with: source_attractiveness_detected (bool), severity (none/mild/moderate/severe), halo_effect_testimony (what halo effect operating), charisma_bias (what charisma substituting), likability_credibility (what likability driving belief), fluency_credibility (what fluency assumed as knowledge), recommendation (no_source_attractiveness/mild_evidence_focus/significant_source_independence/major_intensive_credibility_audit/emergency_complete_source_attractiveness)."""

EPISTEMIC_TESTIMONY_SOURCE_ATTRACTIVENESS_PROMPT = """Detect epistemic testimony source attractiveness:

Halo effect testimony: {halo_effect_testimony}
Charisma bias: {charisma_bias}
Likability credibility: {likability_credibility}
Fluency credibility: {fluency_credibility}
Domain: {domain}
Context: {context}

Is testimony being evaluated based on source attractiveness rather than evidence? Return ONLY valid JSON."""


class EpistemicTestimonySourceAttractivenessService:
    """Detects epistemic testimony source attractiveness — likability over evidence."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        halo_effect_testimony: str,
        *,
        charisma_bias: str = "",
        likability_credibility: str = "",
        fluency_credibility: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic testimony source attractiveness."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_TESTIMONY_SOURCE_ATTRACTIVENESS_PROMPT.format(
                halo_effect_testimony=halo_effect_testimony,
                charisma_bias=charisma_bias or "Not specified",
                likability_credibility=likability_credibility or "Not specified",
                fluency_credibility=fluency_credibility or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_TESTIMONY_SOURCE_ATTRACTIVENESS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "halo_effect_testimony": halo_effect_testimony[:200],
            "source_attractiveness_detected": data.get("source_attractiveness_detected", False),
            "severity": data.get("severity", ""),
            "charisma_bias": data.get("charisma_bias", ""),
            "likability_credibility": data.get("likability_credibility", ""),
            "fluency_credibility": data.get("fluency_credibility", ""),
            "recommendation": data.get("recommendation", ""),
        }
