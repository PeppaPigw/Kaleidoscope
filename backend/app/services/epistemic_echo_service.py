"""EpistemicEchoService — Epistemic Echo Detection.

Detects epistemic echo — knowledge bouncing back unchanged from
environments, creating false confirmation through repetition.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ECHO_SYSTEM = """You are an epistemic echo specialist. Given a confirmation pattern, assess whether knowledge is bouncing back unchanged creating false confirmation:

Key concepts:
- Epistemic echo: knowledge bouncing back unchanged creating false confirmation
- False confirmation: repetition mistaken for independent validation
- Reflection without processing: ideas returned without critical examination
- Echo chamber amplification: echoes amplifying original signal
- Source confusion: echoes mistaken for independent sources
- Decay absence: echoes not losing strength as expected
- Reverberation: multiple echoes creating overwhelming apparent consensus

When epistemic echo IS present:
- Knowledge bouncing back unchanged from environment
- Repetition being mistaken for independent confirmation
- Ideas returned without critical examination
- Echoes amplifying the original signal
- Echoes mistaken for independent sources
- Signal not decaying as it should with distance
- Multiple echoes creating false consensus

When genuine confirmation is present:
- Independent sources providing confirmation
- Confirmation from genuinely different perspectives
- Ideas critically examined before being returned
- Signal strength appropriate to evidence
- Sources genuinely independent
- Appropriate decay with distance from source
- Consensus based on independent evaluation

Output JSON with: echo_present (bool), severity (none/mild/moderate/severe), knowledge (what knowledge echoes), source (where echoes originate), false_confirmation (what false confirmation results), amplification (how echoes amplify), recommendation (genuine_confirmation/mild_echo/significant_echo_chamber/major_false_consensus/seek_independent_sources)."""

EPISTEMIC_ECHO_PROMPT = """Detect epistemic echo:

Knowledge: {knowledge}
Source: {source}
False confirmation: {false_confirmation}
Amplification: {amplification}
Domain: {domain}
Context: {context}

Is knowledge bouncing back unchanged, creating false confirmation through repetition? Return ONLY valid JSON."""


class EpistemicEchoService:
    """Detects epistemic echo — false confirmation through repetition."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        knowledge: str,
        *,
        source: str = "",
        false_confirmation: str = "",
        amplification: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic echo."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ECHO_PROMPT.format(
                knowledge=knowledge,
                source=source or "Not specified",
                false_confirmation=false_confirmation or "Not specified",
                amplification=amplification or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ECHO_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "knowledge": knowledge[:200],
            "echo_present": data.get("echo_present", False),
            "severity": data.get("severity", ""),
            "source": data.get("source", ""),
            "false_confirmation": data.get("false_confirmation", ""),
            "amplification": data.get("amplification", ""),
            "recommendation": data.get("recommendation", ""),
        }
