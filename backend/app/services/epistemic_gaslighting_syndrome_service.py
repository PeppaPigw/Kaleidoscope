"""EpistemicGaslightingSyndromeService — Epistemic Gaslighting Syndrome Detection.

Detects epistemic gaslighting syndrome — systematic undermining of intellectual
self-trust through persistent denial of one's valid perceptions and reasoning.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_GASLIGHTING_SYNDROME_SYSTEM = """You are an epistemic gaslighting syndrome specialist. Given systematic intellectual self-trust undermining, assess gaslighting syndrome:

Key concepts:
- Epistemic gaslighting syndrome: systematic undermining of self-trust
- Reality denial: told your perceptions are wrong
- Memory manipulation: made to doubt what you know
- Confidence erosion: progressive loss of intellectual self-trust
- Isolation: cut off from validating sources
- Dependency creation: made to rely on gaslighter for reality
- Self-doubt spiral: increasingly unable to trust own reasoning

When epistemic gaslighting syndrome IS present:
- Systematic undermining
- Told perceptions wrong
- Made to doubt knowledge
- Progressive confidence loss
- Cut off from validation
- Dependent on other for reality
- Unable to trust own reasoning

When no gaslighting syndrome:
- Self-trust intact
- Perceptions validated
- Knowledge confirmed
- Confidence stable
- Connected to validation
- Independent reality testing
- Trusting own reasoning

Output JSON with: gaslighting_syndrome_detected (bool), severity (none/mild/moderate/severe), reality_denial (what told wrong), confidence_erosion (what progressive loss), isolation_pattern (what cut off), dependency_level (what reliance), recommendation (no_gaslighting_syndrome/mild_reality_testing/significant_trust_rebuilding/major_intensive_recovery/emergency_complete_self_trust_loss)."""

EPISTEMIC_GASLIGHTING_SYNDROME_PROMPT = """Detect epistemic gaslighting syndrome:

Reality denial: {reality_denial}
Confidence erosion: {confidence_erosion}
Isolation pattern: {isolation_pattern}
Dependency level: {dependency_level}
Domain: {domain}
Context: {context}

Is there systematic undermining of intellectual self-trust through persistent denial? Return ONLY valid JSON."""


class EpistemicGaslightingSyndromeService:
    """Detects epistemic gaslighting syndrome — systematic self-trust undermining."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        reality_denial: str,
        *,
        confidence_erosion: str = "",
        isolation_pattern: str = "",
        dependency_level: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic gaslighting syndrome."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_GASLIGHTING_SYNDROME_PROMPT.format(
                reality_denial=reality_denial,
                confidence_erosion=confidence_erosion or "Not specified",
                isolation_pattern=isolation_pattern or "Not specified",
                dependency_level=dependency_level or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_GASLIGHTING_SYNDROME_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "reality_denial": reality_denial[:200],
            "gaslighting_syndrome_detected": data.get("gaslighting_syndrome_detected", False),
            "severity": data.get("severity", ""),
            "confidence_erosion": data.get("confidence_erosion", ""),
            "isolation_pattern": data.get("isolation_pattern", ""),
            "dependency_level": data.get("dependency_level", ""),
            "recommendation": data.get("recommendation", ""),
        }
