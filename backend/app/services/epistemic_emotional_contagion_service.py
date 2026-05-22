"""EpistemicEmotionalContagionService — Epistemic Emotional Contagion Detection.

Detects epistemic emotional contagion — catching others' emotional states
and mistaking them for evidence about the world.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_EMOTIONAL_CONTAGION_SYSTEM = """You are an epistemic emotional contagion specialist. Given catching emotions and mistaking for evidence, assess emotional contagion:

Key concepts:
- Epistemic emotional contagion: catching emotions and mistaking for evidence
- Mood as evidence: treating caught mood as evidence
- Group emotion adoption: adopting group emotions as own beliefs
- Panic contagion: catching panic and treating as information
- Enthusiasm infection: catching enthusiasm and treating as validation
- Anxiety transmission: transmitted anxiety becoming belief about danger
- Emotional reasoning from others: reasoning from others' emotions

When epistemic emotional contagion IS present:
- Catching emotions mistaken for evidence
- Treating mood as evidence
- Adopting group emotions as beliefs
- Catching panic as information
- Catching enthusiasm as validation
- Transmitted anxiety becoming belief
- Reasoning from others' emotions

When no emotional contagion:
- Distinguishing emotions from evidence
- Mood separate from evidence
- Own beliefs independent of group emotion
- Panic recognized as contagion
- Enthusiasm evaluated independently
- Anxiety recognized as transmitted
- Reasoning from evidence not emotion

Output JSON with: emotional_contagion_detected (bool), severity (none/mild/moderate/severe), mood_as_evidence (what mood treated as evidence for), group_emotion_adoption (what group emotions adopted as beliefs), panic_contagion (what panic caught and treated as info), anxiety_transmission (what transmitted anxiety became belief about), recommendation (no_emotional_contagion/mild_source_checking/significant_emotion_evidence_separation/major_intensive_independence_building/emergency_complete_emotional_contagion)."""

EPISTEMIC_EMOTIONAL_CONTAGION_PROMPT = """Detect epistemic emotional contagion:

Mood as evidence: {mood_as_evidence}
Group emotion adoption: {group_emotion_adoption}
Panic contagion: {panic_contagion}
Anxiety transmission: {anxiety_transmission}
Domain: {domain}
Context: {context}

Is there catching others' emotional states and mistaking them for evidence? Return ONLY valid JSON."""


class EpistemicEmotionalContagionService:
    """Detects epistemic emotional contagion — catching emotions mistaken for evidence."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        mood_as_evidence: str,
        *,
        group_emotion_adoption: str = "",
        panic_contagion: str = "",
        anxiety_transmission: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic emotional contagion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_EMOTIONAL_CONTAGION_PROMPT.format(
                mood_as_evidence=mood_as_evidence,
                group_emotion_adoption=group_emotion_adoption or "Not specified",
                panic_contagion=panic_contagion or "Not specified",
                anxiety_transmission=anxiety_transmission or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_EMOTIONAL_CONTAGION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "mood_as_evidence": mood_as_evidence[:200],
            "emotional_contagion_detected": data.get("emotional_contagion_detected", False),
            "severity": data.get("severity", ""),
            "group_emotion_adoption": data.get("group_emotion_adoption", ""),
            "panic_contagion": data.get("panic_contagion", ""),
            "anxiety_transmission": data.get("anxiety_transmission", ""),
            "recommendation": data.get("recommendation", ""),
        }
