"""KafkaTrapService — Kafka Trap Detection.

Detects Kafka traps — unfalsifiable accusations where denial
is taken as proof of guilt. Named after Kafka's "The Trial."
"If you deny being racist, that proves you're racist." The
accusation is structured so that no response can exonerate
the accused. Any defense is reinterpreted as further evidence
of the charge.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

KAFKA_TRAP_SYSTEM = """You are a Kafka trap specialist. Given an accusation or argumentative structure, assess whether it's constructed so that denial serves as confirmation:

Key concepts:
- Kafka trap: denial of accusation taken as proof of guilt
- Unfalsifiability: no possible response can disprove the charge
- Catch-22 structure: damned if you do, damned if you don't
- Kafkaesque reasoning: guilt assumed, defense impossible
- Motte-and-bailey interaction: retreating to unfalsifiable version
- Thought-terminating cliché: "that's exactly what X would say"
- Epistemic coercion: forcing agreement through logical trap

When a Kafka trap IS present:
- "Your denial proves you're guilty"
- "If you weren't X, you wouldn't be so defensive"
- Accusations structured so no response can exonerate
- "The fact that you disagree shows you don't understand"
- Any defense reinterpreted as further evidence of the charge
- "Only someone who is X would say that"
- Unfalsifiable framing of accusations

When the reasoning IS legitimate:
- Denial is suspicious because of specific contradicting evidence
- The defense actually does reveal the thing being accused
- There's a genuine logical connection between response and charge
- The accusation is falsifiable — specific evidence could disprove it
- The person can articulate what would change their mind

Output JSON with: kafka_trap_present (bool), severity (none/mild/moderate/severe), accusation (what is being accused), trap_structure (how is denial used as proof), falsifiability (can the accusation be disproven), escape_route (what response would be accepted as exonerating), coercion_effect (what is the accused forced to accept), legitimate_concern (is there a legitimate underlying concern), recommendation (reasoning_legitimate/mild_unfalsifiable_framing/significant_kafka_trap/major_epistemic_coercion/make_accusation_falsifiable)."""

KAFKA_TRAP_PROMPT = """Detect Kafka trap:

Exchange: {exchange}
Accusation: {accusation}
Defense offered: {defense}
Response to defense: {response}
Domain: {domain}
Context: {context}

Is the accusation structured so that denial serves as confirmation of guilt? Return ONLY valid JSON."""


class KafkaTrapService:
    """Detects Kafka traps — unfalsifiable accusations where denial proves guilt."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        exchange: str,
        *,
        accusation: str = "",
        defense: str = "",
        response: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect Kafka trap."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=KAFKA_TRAP_PROMPT.format(
                exchange=exchange,
                accusation=accusation or "Not specified",
                defense=defense or "Not specified",
                response=response or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=KAFKA_TRAP_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "exchange": exchange[:200],
            "kafka_trap_present": data.get("kafka_trap_present", False),
            "severity": data.get("severity", ""),
            "trap_structure": data.get("trap_structure", ""),
            "falsifiability": data.get("falsifiability", ""),
            "escape_route": data.get("escape_route", ""),
            "coercion_effect": data.get("coercion_effect", ""),
            "legitimate_concern": data.get("legitimate_concern", ""),
            "recommendation": data.get("recommendation", ""),
        }
