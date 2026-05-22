"""EpistemicAttentionCaptureService — Epistemic Attention Capture Detection.

Detects epistemic attention capture — attention captured by emotionally
salient but unimportant information at the expense of what matters.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ATTENTION_CAPTURE_SYSTEM = """You are an epistemic attention capture specialist. Given attention captured by salient but unimportant info, assess attention capture:

Key concepts:
- Epistemic attention capture: attention captured by emotionally salient but unimportant info
- Salience hijacking: emotional salience hijacking attention from important topics
- Outrage capture: outrage capturing attention from substantive issues
- Novelty addiction: attention addicted to novelty over importance
- Drama magnetism: attention drawn to drama over substance
- Urgency illusion: false urgency capturing attention from important long-term issues
- Spectacle over substance: attention on spectacle rather than substance

When epistemic attention capture IS present:
- Attention captured by salient unimportant info
- Emotional salience hijacking attention
- Outrage capturing from substance
- Addicted to novelty over importance
- Drawn to drama over substance
- False urgency capturing attention
- Spectacle over substance

When no attention capture:
- Attention on important information
- Emotional salience recognized but not controlling
- Substance over outrage
- Importance over novelty
- Substance over drama
- True priorities maintained
- Substance over spectacle

Output JSON with: attention_capture_detected (bool), severity (none/mild/moderate/severe), salience_hijacking (what hijacking attention), outrage_capture (what outrage capturing from), novelty_addiction (what novelty distracting from), urgency_illusion (what false urgency about), recommendation (no_attention_capture/mild_refocusing/significant_attention_training/major_intensive_priority_reset/emergency_complete_attention_capture)."""

EPISTEMIC_ATTENTION_CAPTURE_PROMPT = """Detect epistemic attention capture:

Salience hijacking: {salience_hijacking}
Outrage capture: {outrage_capture}
Novelty addiction: {novelty_addiction}
Urgency illusion: {urgency_illusion}
Domain: {domain}
Context: {context}

Is there attention captured by emotionally salient but unimportant information? Return ONLY valid JSON."""


class EpistemicAttentionCaptureService:
    """Detects epistemic attention capture — attention captured by salient unimportant info."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        salience_hijacking: str,
        *,
        outrage_capture: str = "",
        novelty_addiction: str = "",
        urgency_illusion: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic attention capture."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ATTENTION_CAPTURE_PROMPT.format(
                salience_hijacking=salience_hijacking,
                outrage_capture=outrage_capture or "Not specified",
                novelty_addiction=novelty_addiction or "Not specified",
                urgency_illusion=urgency_illusion or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ATTENTION_CAPTURE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "salience_hijacking": salience_hijacking[:200],
            "attention_capture_detected": data.get("attention_capture_detected", False),
            "severity": data.get("severity", ""),
            "outrage_capture": data.get("outrage_capture", ""),
            "novelty_addiction": data.get("novelty_addiction", ""),
            "urgency_illusion": data.get("urgency_illusion", ""),
            "recommendation": data.get("recommendation", ""),
        }
