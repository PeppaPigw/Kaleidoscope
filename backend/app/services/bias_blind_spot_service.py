"""BiasBlindSpotService — Bias Blind Spot Detection.

Detects bias blind spot — recognizing cognitive biases in
others while failing to see them in oneself. Pronin, Lin &
Ross (2002). "I'm objective, but they're biased." Leads to
overconfidence in own judgment, dismissal of others'
perspectives, and resistance to debiasing.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

BIAS_BLIND_SPOT_SYSTEM = """You are a bias blind spot specialist. Given a claim of objectivity or accusation of others' bias, assess whether the person is exhibiting the bias blind spot:

Key concepts (Pronin, Lin & Ross, 2002):
- Bias blind spot: seeing bias in others but not in oneself
- Introspection illusion: believing self-examination reveals true motives
- Naive realism overlap: "I see reality as it is, they're biased"
- Asymmetric insight: believing you understand others better than they understand you
- Self-serving attribution: own views = objective, others' views = biased
- Debiasing resistance: "I don't need to check my biases"
- Meta-bias: the bias about biases

When bias blind spot IS present:
- "I'm being objective here, but they're clearly biased"
- Identifying specific biases in others while claiming immunity
- "I've thought about this carefully" as proof of objectivity
- Dismissing others' views as biased without examining own biases
- Resistance to bias-checking procedures ("I don't need that")
- Asymmetric standards: scrutinizing others' reasoning but not own

When the objectivity claim IS justified:
- The person has actually used debiasing procedures
- They can articulate their own potential biases
- They've sought disconfirming evidence for their position
- They acknowledge uncertainty in their own judgment
- They apply the same scrutiny to their own reasoning as others'

Output JSON with: bias_blind_spot_present (bool), severity (none/mild/moderate/severe), claim (what objectivity is being claimed), others_bias (what bias is attributed to others), own_bias_acknowledged (bool — does the person acknowledge own potential biases?), debiasing_used (bool — has the person used debiasing procedures?), asymmetric_scrutiny (bool — different standards for self vs others?), introspection_relied_on (bool — is introspection treated as proof of objectivity?), evidence_of_own_bias (what evidence suggests the person may be biased?), recommendation (objectivity_justified/mild_blind_spot/significant_asymmetry/major_bias_blind_spot/apply_same_scrutiny_to_self)."""

BIAS_BLIND_SPOT_PROMPT = """Detect bias blind spot:

Claim: {claim}
Others' bias: {others_bias}
Own reasoning: {own_reasoning}
Debiasing: {debiasing}
Domain: {domain}
Context: {context}

Is the person recognizing bias in others while failing to see it in themselves? Return ONLY valid JSON."""


class BiasBlindSpotService:
    """Detects bias blind spot — seeing bias in others but not in oneself."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        claim: str,
        *,
        others_bias: str = "",
        own_reasoning: str = "",
        debiasing: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect bias blind spot."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=BIAS_BLIND_SPOT_PROMPT.format(
                claim=claim,
                others_bias=others_bias or "Not specified",
                own_reasoning=own_reasoning or "Not specified",
                debiasing=debiasing or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=BIAS_BLIND_SPOT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "claim": claim[:200],
            "bias_blind_spot_present": data.get("bias_blind_spot_present", False),
            "severity": data.get("severity", ""),
            "others_bias": data.get("others_bias", ""),
            "own_bias_acknowledged": data.get("own_bias_acknowledged", True),
            "debiasing_used": data.get("debiasing_used", True),
            "asymmetric_scrutiny": data.get("asymmetric_scrutiny", False),
            "introspection_relied_on": data.get("introspection_relied_on", False),
            "evidence_of_own_bias": data.get("evidence_of_own_bias", ""),
            "recommendation": data.get("recommendation", ""),
        }
