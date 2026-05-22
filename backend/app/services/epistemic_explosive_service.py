"""EpistemicExplosiveService — Epistemic Intermittent Explosive Detection.

Detects epistemic intermittent explosive disorder — sudden disproportionate
intellectual rage outbursts in response to minor provocations.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_EXPLOSIVE_SYSTEM = """You are an epistemic explosive disorder specialist. Given intellectual rage outbursts, assess explosive patterns:

Key concepts:
- Epistemic explosive: sudden disproportionate intellectual rage
- Disproportionate: response far exceeds provocation
- Impulsive: no premeditation, sudden onset
- Brief: episodes short-lived but intense
- Remorse: regret after outburst
- Trigger sensitivity: low threshold for intellectual frustration
- Escalation: minor irritation to full rage instantly

When epistemic explosive IS present:
- Sudden disproportionate rage
- Response exceeds provocation
- No premeditation
- Short but intense episodes
- Regret after outburst
- Low frustration threshold
- Instant escalation

When no explosive:
- Proportionate responses
- Measured reactions
- Considered responses
- Sustained composure
- No regret needed
- Normal frustration tolerance
- Gradual escalation if any

Output JSON with: explosive_detected (bool), severity (none/mild/moderate/severe), rage_pattern (what outbursts), disproportionality (what excess), trigger_threshold (what sensitivity), remorse_level (what regret), recommendation (no_explosive/mild_anger_management/significant_cbt/major_intensive_therapy/emergency_dangerous_outbursts)."""

EPISTEMIC_EXPLOSIVE_PROMPT = """Detect epistemic intermittent explosive:

Rage pattern: {rage_pattern}
Disproportionality: {disproportionality}
Trigger threshold: {trigger_threshold}
Remorse level: {remorse_level}
Domain: {domain}
Context: {context}

Are there sudden disproportionate intellectual rage outbursts to minor provocations? Return ONLY valid JSON."""


class EpistemicExplosiveService:
    """Detects epistemic explosive — sudden intellectual rage outbursts."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        rage_pattern: str,
        *,
        disproportionality: str = "",
        trigger_threshold: str = "",
        remorse_level: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic intermittent explosive."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_EXPLOSIVE_PROMPT.format(
                rage_pattern=rage_pattern,
                disproportionality=disproportionality or "Not specified",
                trigger_threshold=trigger_threshold or "Not specified",
                remorse_level=remorse_level or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_EXPLOSIVE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "rage_pattern": rage_pattern[:200],
            "explosive_detected": data.get("explosive_detected", False),
            "severity": data.get("severity", ""),
            "disproportionality": data.get("disproportionality", ""),
            "trigger_threshold": data.get("trigger_threshold", ""),
            "remorse_level": data.get("remorse_level", ""),
            "recommendation": data.get("recommendation", ""),
        }
