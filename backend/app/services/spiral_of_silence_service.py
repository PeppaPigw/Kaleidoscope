"""SpiralOfSilenceService — Spiral of Silence Detection.

Detects spiral of silence — people suppressing opinions they perceive
as minority views, which further reduces the visibility of those views,
creating a self-reinforcing cycle. Noelle-Neumann (1974).
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

SPIRAL_SILENCE_SYSTEM = """You are a spiral of silence specialist. Given a discourse environment, assess whether a spiral of silence is suppressing minority opinions:

Key concepts (Noelle-Neumann, 1974):
- Spiral of silence: minority views suppressed → appear even more minority
- Fear of isolation: people avoid expressing unpopular opinions
- Quasi-statistical sense: people estimate opinion climate
- Opinion climate: perceived distribution of views
- Hardcore: those who speak up regardless of perceived minority status
- Media influence: media shapes perception of opinion climate
- Self-reinforcing: silence begets more silence

When spiral of silence IS present:
- People privately hold views they won't express publicly
- The perceived opinion climate differs from actual opinion distribution
- Fear of social consequences suppresses expression
- Vocal minority appears to be majority due to silence of actual majority
- People self-censor based on perceived social acceptability
- The discourse environment punishes dissent
- Private polls show different results than public discourse suggests

When silence IS appropriate:
- The opinion is genuinely held by very few people
- The silence reflects genuine consensus, not suppression
- People have changed their minds, not just gone silent
- The topic is genuinely settled by evidence
- Expression is limited by relevance, not fear
- Multiple channels exist for expressing dissent
- The perceived and actual opinion climates align

Output JSON with: spiral_of_silence_present (bool), severity (none/mild/moderate/severe), topic (what topic is affected), suppressed_view (what view is being suppressed), perceived_climate (what opinion climate is perceived), actual_climate (what actual distribution might be), fear_mechanism (what fear drives silence), recommendation (genuine_consensus/mild_self_censorship/significant_spiral_of_silence/major_opinion_suppression/create_safe_expression_channels)."""

SPIRAL_SILENCE_PROMPT = """Detect spiral of silence:

Topic: {topic}
Discourse environment: {environment}
Suppression evidence: {suppression}
Opinion climate: {climate}
Domain: {domain}
Context: {context}

Is a spiral of silence suppressing minority opinions in this discourse? Return ONLY valid JSON."""


class SpiralOfSilenceService:
    """Detects spiral of silence — self-reinforcing suppression of minority views."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        topic: str,
        *,
        environment: str = "",
        suppression: str = "",
        climate: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect spiral of silence."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=SPIRAL_SILENCE_PROMPT.format(
                topic=topic,
                environment=environment or "Not specified",
                suppression=suppression or "Not specified",
                climate=climate or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=SPIRAL_SILENCE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "topic": topic[:200],
            "spiral_of_silence_present": data.get("spiral_of_silence_present", False),
            "severity": data.get("severity", ""),
            "suppressed_view": data.get("suppressed_view", ""),
            "perceived_climate": data.get("perceived_climate", ""),
            "actual_climate": data.get("actual_climate", ""),
            "fear_mechanism": data.get("fear_mechanism", ""),
            "recommendation": data.get("recommendation", ""),
        }
