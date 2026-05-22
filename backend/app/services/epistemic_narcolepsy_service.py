"""EpistemicNarcolepsyService — Epistemic Narcolepsy Detection.

Detects epistemic narcolepsy — sudden uncontrollable episodes of
intellectual shutdown or collapse during active thinking.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_NARCOLEPSY_SYSTEM = """You are an epistemic narcolepsy specialist. Given sudden intellectual shutdown, assess narcolepsy patterns:

Key concepts:
- Epistemic narcolepsy: sudden uncontrollable intellectual shutdown
- Cataplexy: sudden loss of intellectual muscle tone
- Sleep attacks: irresistible episodes of mental shutdown
- Hypnagogic: hallucination-like thoughts at shutdown onset
- Sleep paralysis: aware but unable to think
- Fragmented wakefulness: inability to maintain sustained thought
- Orexin deficiency: lacking intellectual wakefulness signal

When epistemic narcolepsy IS present:
- Sudden uncontrollable shutdown
- Loss of intellectual tone
- Irresistible shutdown episodes
- Hallucination-like thoughts
- Aware but unable to think
- Cannot maintain sustained thought
- Lacking wakefulness signal

When no narcolepsy:
- Controlled transitions
- Maintained intellectual tone
- No irresistible episodes
- Clear thought transitions
- Full thinking capacity
- Sustained thought maintained
- Normal wakefulness

Output JSON with: narcolepsy_detected (bool), severity (none/mild/moderate/severe), shutdown_pattern (what episodes), cataplexy_triggers (what causes collapse), fragmentation_level (what sustained thought loss), onset_context (what circumstances), recommendation (no_narcolepsy/mild_scheduled_rest/significant_stimulant_equivalent/major_intensive_management/emergency_dangerous_shutdown)."""

EPISTEMIC_NARCOLEPSY_PROMPT = """Detect epistemic narcolepsy:

Shutdown pattern: {shutdown_pattern}
Cataplexy triggers: {cataplexy_triggers}
Fragmentation level: {fragmentation_level}
Onset context: {onset_context}
Domain: {domain}
Context: {context}

Are there sudden uncontrollable episodes of intellectual shutdown during active thinking? Return ONLY valid JSON."""


class EpistemicNarcolepsyService:
    """Detects epistemic narcolepsy — sudden intellectual shutdown episodes."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        shutdown_pattern: str,
        *,
        cataplexy_triggers: str = "",
        fragmentation_level: str = "",
        onset_context: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic narcolepsy."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_NARCOLEPSY_PROMPT.format(
                shutdown_pattern=shutdown_pattern,
                cataplexy_triggers=cataplexy_triggers or "Not specified",
                fragmentation_level=fragmentation_level or "Not specified",
                onset_context=onset_context or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_NARCOLEPSY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "shutdown_pattern": shutdown_pattern[:200],
            "narcolepsy_detected": data.get("narcolepsy_detected", False),
            "severity": data.get("severity", ""),
            "cataplexy_triggers": data.get("cataplexy_triggers", ""),
            "fragmentation_level": data.get("fragmentation_level", ""),
            "onset_context": data.get("onset_context", ""),
            "recommendation": data.get("recommendation", ""),
        }
