"""EpistemicResistanceService — Epistemic Resistance Detection.

Detects epistemic resistance — active opposition to illegitimate intellectual
authority, refusing to accept imposed beliefs or knowledge constraints.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_RESISTANCE_SYSTEM = """You are an epistemic resistance specialist. Given active intellectual opposition, assess resistance:

Key concepts:
- Epistemic resistance: active opposition to illegitimate authority
- Counter-narrative: creating alternative accounts
- Refusal: declining to accept imposed beliefs
- Subversion: undermining dominant knowledge systems
- Solidarity: collective intellectual opposition
- Voice reclamation: speaking despite suppression
- Knowledge preservation: protecting threatened understanding

When epistemic resistance IS present:
- Active opposition
- Creating alternatives
- Declining imposed beliefs
- Undermining dominant systems
- Collective opposition
- Speaking despite suppression
- Protecting threatened knowledge

When no resistance:
- No opposition needed
- Legitimate authority
- Freely chosen beliefs
- Fair knowledge systems
- Individual engagement
- Free speech
- Knowledge secure

Output JSON with: resistance_detected (bool), severity (none/mild/moderate/severe), opposition_form (what active opposition), counter_narrative (what alternative), refusal_pattern (what declining), solidarity_level (what collective), recommendation (no_resistance_needed/mild_voice_strengthening/significant_resistance_organizing/major_intensive_liberation/emergency_dangerous_opposition)."""

EPISTEMIC_RESISTANCE_PROMPT = """Detect epistemic resistance:

Opposition form: {opposition_form}
Counter narrative: {counter_narrative}
Refusal pattern: {refusal_pattern}
Solidarity level: {solidarity_level}
Domain: {domain}
Context: {context}

Is there active opposition to illegitimate intellectual authority? Return ONLY valid JSON."""


class EpistemicResistanceService:
    """Detects epistemic resistance — active intellectual opposition."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        opposition_form: str,
        *,
        counter_narrative: str = "",
        refusal_pattern: str = "",
        solidarity_level: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic resistance."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_RESISTANCE_PROMPT.format(
                opposition_form=opposition_form,
                counter_narrative=counter_narrative or "Not specified",
                refusal_pattern=refusal_pattern or "Not specified",
                solidarity_level=solidarity_level or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_RESISTANCE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "opposition_form": opposition_form[:200],
            "resistance_detected": data.get("resistance_detected", False),
            "severity": data.get("severity", ""),
            "counter_narrative": data.get("counter_narrative", ""),
            "refusal_pattern": data.get("refusal_pattern", ""),
            "solidarity_level": data.get("solidarity_level", ""),
            "recommendation": data.get("recommendation", ""),
        }
