"""SpotlightEffectService — Spotlight Effect Detection.

Detects the spotlight effect — overestimating how much others
notice your appearance, behavior, or mistakes. Gilovich, Medvec
& Savitsky (2000). You think everyone noticed your stain, your
stumble, your awkward comment. In reality, others are far less
attentive to you than you believe.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

SPOTLIGHT_SYSTEM = """You are a spotlight effect specialist. Given a social situation, assess whether the spotlight effect is causing overestimation of others' attention:

Key concepts (Gilovich, Medvec & Savitsky, 2000):
- Spotlight effect: believing others notice you more than they actually do
- Anchoring on own experience: your embarrassment is vivid to you, so you assume it's visible
- Asymmetric attention: you notice your own flaws far more than others do
- Social anxiety amplification: the effect is stronger when self-conscious
- Illusion of transparency overlap: but spotlight is about external appearance, not internal states
- Recall bias: overestimating how memorable your actions were to others

When the spotlight effect IS present:
- Excessive worry about minor appearance issues
- Believing a small mistake was noticed by everyone
- Assuming others remember your embarrassing moment
- Overestimating how much attention your behavior drew
- Avoiding situations because "everyone will notice"
- Post-event rumination about how you were perceived

When attention IS genuinely high:
- You are in a formal presentation or performance role
- The behavior was genuinely disruptive or unusual
- Others explicitly commented or reacted
- The context specifically draws attention to you (interview, stage)
- The "flaw" is objectively very noticeable

Output JSON with: spotlight_present (bool), severity (none/mild/moderate/severe), perceived_attention (what the person thinks others noticed), actual_attention (realistic estimate of others' attention), attention_gap (difference between perceived and actual), trigger (what caused the self-consciousness), social_context (formal/informal/anonymous/intimate), audience_size (how many people were present), duration_of_exposure (how long the "noticed" thing was visible), objective_noticeability (how noticeable the thing actually is), self_consciousness_level (how self-aware the person is), evidence_of_notice (did anyone actually react?), memory_persistence (will others remember this?), recommendation (attention_warranted/mild_overestimation/significant_spotlight/major_spotlight_effect/others_arent_watching)."""

SPOTLIGHT_PROMPT = """Detect spotlight effect:

Situation: {situation}
What's believed noticed: {believed_noticed}
Social context: {social_context}
Evidence of attention: {evidence}
Domain: {domain}
Context: {context}

Is the spotlight effect causing overestimation of others' attention? Return ONLY valid JSON."""


class SpotlightEffectService:
    """Detects spotlight effect — overestimating how much others notice you."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        believed_noticed: str = "",
        social_context: str = "",
        evidence: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect spotlight effect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=SPOTLIGHT_PROMPT.format(
                situation=situation,
                believed_noticed=believed_noticed or "Not specified",
                social_context=social_context or "Not specified",
                evidence=evidence or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=SPOTLIGHT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "spotlight_present": data.get("spotlight_present", False),
            "severity": data.get("severity", ""),
            "perceived_attention": data.get("perceived_attention", ""),
            "actual_attention": data.get("actual_attention", ""),
            "attention_gap": data.get("attention_gap", ""),
            "trigger": data.get("trigger", ""),
            "social_context": data.get("social_context", ""),
            "audience_size": data.get("audience_size", ""),
            "duration_of_exposure": data.get("duration_of_exposure", ""),
            "objective_noticeability": data.get("objective_noticeability", ""),
            "self_consciousness_level": data.get("self_consciousness_level", ""),
            "evidence_of_notice": data.get("evidence_of_notice", ""),
            "memory_persistence": data.get("memory_persistence", ""),
            "recommendation": data.get("recommendation", ""),
        }
