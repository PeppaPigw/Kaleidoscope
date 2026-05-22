"""BlindSpotMetaService — Blind Spot Meta-Detection.

Detects meta-level blind spots — when someone recognizes biases
in others but fails to apply the same scrutiny to themselves.
This is the bias blind spot operating at a meta-cognitive level.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

BLIND_SPOT_META_SYSTEM = """You are a meta-level blind spot specialist. Given a critique or analysis, assess whether the critic applies the same standards to themselves:

Key concepts:
- Bias blind spot: seeing bias in others but not in oneself
- Meta-cognitive failure: inability to apply self-scrutiny
- Asymmetric standards: different rules for self vs others
- Naive realism: believing one sees reality objectively
- Intellectual hypocrisy: demanding standards one doesn't meet
- Self-serving attribution: explaining own behavior charitably
- Projection: attributing own biases to others

When meta blind spot IS present:
- Critic identifies biases in others they exhibit themselves
- Standards demanded of others not applied to self
- Own reasoning treated as objective while others' is biased
- Sophisticated bias detection paired with self-exemption
- "I'm aware of biases, so I'm not biased" reasoning
- Applying scrutiny outward but not inward
- Recognizing motivated reasoning in others but not in self

When meta blind spot is NOT present:
- Same standards applied to self and others
- Self-scrutiny matches scrutiny of others
- Own potential biases acknowledged
- Awareness of bias doesn't create false immunity
- Intellectual humility about own reasoning
- Symmetric evaluation of self and others
- Recognition that awareness doesn't equal immunity

Output JSON with: blind_spot_present (bool), severity (none/mild/moderate/severe), critique_made (what bias is identified in others), self_application (whether same standard is applied to self), asymmetry (how standards differ for self vs others), self_exemption (how the critic exempts themselves), recommendation (symmetric_scrutiny/mild_asymmetry/significant_blind_spot/major_self_exemption/apply_standards_symmetrically)."""

BLIND_SPOT_META_PROMPT = """Detect meta-level blind spot:

Analysis: {analysis}
Critic's position: {position}
Standards applied: {standards}
Self-scrutiny: {self_scrutiny}
Domain: {domain}
Context: {context}

Does the critic apply the same standards to themselves that they apply to others? Return ONLY valid JSON."""


class BlindSpotMetaService:
    """Detects meta-level blind spots — seeing bias in others but not self."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        analysis: str,
        *,
        position: str = "",
        standards: str = "",
        self_scrutiny: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect meta-level blind spot."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=BLIND_SPOT_META_PROMPT.format(
                analysis=analysis,
                position=position or "Not specified",
                standards=standards or "Not specified",
                self_scrutiny=self_scrutiny or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=BLIND_SPOT_META_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "analysis": analysis[:200],
            "blind_spot_present": data.get("blind_spot_present", False),
            "severity": data.get("severity", ""),
            "critique_made": data.get("critique_made", ""),
            "asymmetry": data.get("asymmetry", ""),
            "self_exemption": data.get("self_exemption", ""),
            "recommendation": data.get("recommendation", ""),
        }
