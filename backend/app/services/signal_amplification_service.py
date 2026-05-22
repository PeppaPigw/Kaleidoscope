"""SignalAmplificationService — Signal Amplification Detection.

Detects signal amplification — weak signals amplified through repetition
until treated as strong evidence, where echo creates the illusion
of independent confirmation.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

SIGNAL_AMPLIFICATION_SYSTEM = """You are a signal amplification specialist. Given an evidence assessment, determine whether weak signals have been amplified through repetition:

Key concepts:
- Signal amplification: weak signals amplified by repetition
- Echo as evidence: repetition creating illusion of strength
- Citation cascade: same source cited repeatedly appearing as multiple
- Amplification through channels: one signal appearing in many places
- Volume as validity: louder treated as more true
- Repetition as confirmation: hearing again treated as independent confirmation
- Source collapse: multiple citations tracing to single source

When signal amplification IS present:
- Weak signal treated as strong through repetition
- Same source appearing as multiple independent sources
- Repetition creating illusion of confirmation
- Volume confused with validity
- Echo mistaken for independent evidence
- Citation cascade from single origin
- Amplification substituting for actual evidence strength

When signal strength is genuine:
- Multiple genuinely independent sources
- Signal strength reflects actual evidence quality
- Repetition from independent observations
- Volume reflects genuine breadth of evidence
- Citations trace to independent origins
- Confirmation genuinely independent
- Evidence strength not inflated by repetition

Output JSON with: amplification_present (bool), severity (none/mild/moderate/severe), signal (what signal is assessed), original_strength (actual strength of original), amplified_strength (perceived strength after amplification), mechanism (how amplification occurs), recommendation (genuine_signal_strength/mild_repetition_inflation/significant_signal_amplification/major_echo_as_evidence/trace_signals_to_independent_sources)."""

SIGNAL_AMPLIFICATION_PROMPT = """Detect signal amplification:

Signal: {signal}
Sources cited: {sources}
Independence: {independence}
Repetition pattern: {repetition}
Domain: {domain}
Context: {context}

Are weak signals being amplified through repetition until treated as strong evidence? Return ONLY valid JSON."""


class SignalAmplificationService:
    """Detects signal amplification — weak signals amplified by repetition."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        signal: str,
        *,
        sources: str = "",
        independence: str = "",
        repetition: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect signal amplification."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=SIGNAL_AMPLIFICATION_PROMPT.format(
                signal=signal,
                sources=sources or "Not specified",
                independence=independence or "Not specified",
                repetition=repetition or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=SIGNAL_AMPLIFICATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "signal": signal[:200],
            "amplification_present": data.get("amplification_present", False),
            "severity": data.get("severity", ""),
            "original_strength": data.get("original_strength", ""),
            "amplified_strength": data.get("amplified_strength", ""),
            "mechanism": data.get("mechanism", ""),
            "recommendation": data.get("recommendation", ""),
        }
