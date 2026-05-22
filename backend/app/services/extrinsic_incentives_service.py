"""ExtrinsicIncentivesService — Extrinsic Incentives Bias Detection.

Detects extrinsic incentives bias — believing others are more
motivated by external rewards (money, status, pressure) than
oneself, while believing own motivation is more intrinsic
(interest, values, meaning). Heath (1999). This creates
systematic misunderstanding of others' motivations and leads
to poorly designed incentive systems.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EXTRINSIC_INCENTIVES_SYSTEM = """You are an extrinsic incentives bias specialist. Given attributions about motivation, assess whether there's an asymmetry in how own vs others' motivations are characterized:

Key concepts (Heath, 1999):
- Extrinsic incentives bias: others motivated by rewards, self by meaning
- Motivation attribution asymmetry: intrinsic for self, extrinsic for others
- Cynicism about others: assuming mercenary motivations
- Self-enhancement: seeing own motivations as noble
- Incentive design failure: designing for extrinsic when intrinsic matters
- Crowding out: extrinsic rewards destroying intrinsic motivation
- Projection failure: not recognizing others' intrinsic drives

When extrinsic incentives bias IS present:
- "They're only in it for the money; I do it because I love it"
- Designing incentive systems based on assumed extrinsic motivation
- Assuming others need carrots/sticks while self is self-motivated
- "They wouldn't do it without the bonus" about intrinsically motivated people
- Cynical interpretation of others' prosocial behavior
- Overlooking others' genuine passion or values-driven behavior
- "What's in it for them?" as default question about others

When motivation assessment IS accurate:
- Evidence genuinely shows different motivation profiles
- The person has stated their motivations explicitly
- Behavioral evidence supports the attribution
- Context genuinely creates different incentive structures
- Both intrinsic and extrinsic factors are considered for all parties

Output JSON with: extrinsic_bias_present (bool), severity (none/mild/moderate/severe), situation (what motivation is being assessed), self_motivation (how own motivation is characterized), other_motivation (how others' motivation is characterized), asymmetry (what is the attribution difference), evidence (what evidence supports the characterization), incentive_implications (how does this affect incentive design), recommendation (motivation_assessment_accurate/mild_attribution_asymmetry/significant_extrinsic_bias/major_motivation_cynicism/assess_motivations_symmetrically)."""

EXTRINSIC_INCENTIVES_PROMPT = """Detect extrinsic incentives bias:

Situation: {situation}
Self-motivation: {self_motivation}
Others' motivation: {other_motivation}
Evidence: {evidence}
Domain: {domain}
Context: {context}

Is there an asymmetry — believing own motivation is intrinsic while others' is extrinsic? Return ONLY valid JSON."""


class ExtrinsicIncentivesService:
    """Detects extrinsic incentives bias — asymmetric motivation attribution."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        self_motivation: str = "",
        other_motivation: str = "",
        evidence: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect extrinsic incentives bias."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EXTRINSIC_INCENTIVES_PROMPT.format(
                situation=situation,
                self_motivation=self_motivation or "Not specified",
                other_motivation=other_motivation or "Not specified",
                evidence=evidence or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EXTRINSIC_INCENTIVES_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "extrinsic_bias_present": data.get("extrinsic_bias_present", False),
            "severity": data.get("severity", ""),
            "self_motivation": data.get("self_motivation", ""),
            "other_motivation": data.get("other_motivation", ""),
            "asymmetry": data.get("asymmetry", ""),
            "evidence": data.get("evidence", ""),
            "incentive_implications": data.get("incentive_implications", ""),
            "recommendation": data.get("recommendation", ""),
        }
