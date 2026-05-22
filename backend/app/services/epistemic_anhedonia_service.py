"""EpistemicAnhedoniaService — Epistemic Anhedonia Detection.

Detects epistemic anhedonia — inability to derive intellectual pleasure
or satisfaction from previously rewarding activities.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ANHEDONIA_SYSTEM = """You are an epistemic anhedonia specialist. Given inability to derive intellectual pleasure, assess anhedonia:

Key concepts:
- Epistemic anhedonia: inability to derive intellectual pleasure
- Consummatory: unable to enjoy intellectual activities in the moment
- Anticipatory: unable to look forward to intellectual activities
- Reward circuit: pleasure/motivation pathway disrupted
- Motivational deficit: no drive to engage intellectually
- Social anhedonia: no pleasure from intellectual exchange
- Behavioral activation: structured re-engagement with activities

When epistemic anhedonia IS present:
- Unable to derive intellectual pleasure
- No enjoyment in the moment
- No anticipation of future activities
- Pleasure pathway disrupted
- No drive to engage
- No pleasure from exchange
- Structured re-engagement needed

When no anhedonia:
- Normal intellectual pleasure
- Enjoyment in activities
- Anticipation of future work
- Pleasure pathway functioning
- Normal drive to engage
- Pleasure from exchange
- Natural engagement

Output JSON with: anhedonia_detected (bool), severity (none/mild/moderate/severe), pleasure_deficit (what enjoyment lost), motivation_status (what drive), reward_response (what circuit function), onset_pattern (what timeline), recommendation (no_anhedonia/mild_behavioral_activation/significant_structured_engagement/major_pharmacological/emergency_complete_withdrawal)."""

EPISTEMIC_ANHEDONIA_PROMPT = """Detect epistemic anhedonia:

Pleasure deficit: {pleasure_deficit}
Motivation status: {motivation_status}
Reward response: {reward_response}
Onset pattern: {onset_pattern}
Domain: {domain}
Context: {context}

Is there inability to derive intellectual pleasure from previously rewarding activities? Return ONLY valid JSON."""


class EpistemicAnhedoniaService:
    """Detects epistemic anhedonia — inability to derive intellectual pleasure."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        pleasure_deficit: str,
        *,
        motivation_status: str = "",
        reward_response: str = "",
        onset_pattern: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic anhedonia."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ANHEDONIA_PROMPT.format(
                pleasure_deficit=pleasure_deficit,
                motivation_status=motivation_status or "Not specified",
                reward_response=reward_response or "Not specified",
                onset_pattern=onset_pattern or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ANHEDONIA_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "pleasure_deficit": pleasure_deficit[:200],
            "anhedonia_detected": data.get("anhedonia_detected", False),
            "severity": data.get("severity", ""),
            "motivation_status": data.get("motivation_status", ""),
            "reward_response": data.get("reward_response", ""),
            "onset_pattern": data.get("onset_pattern", ""),
            "recommendation": data.get("recommendation", ""),
        }
