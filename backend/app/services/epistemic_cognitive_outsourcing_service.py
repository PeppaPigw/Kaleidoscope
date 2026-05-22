"""EpistemicCognitiveOutsourcingService — Epistemic Cognitive Outsourcing Detection.

Detects epistemic cognitive outsourcing — outsourcing all cognitive work
to tools/others without engagement.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_COGNITIVE_OUTSOURCING_SYSTEM = """You are an epistemic cognitive outsourcing specialist. Given outsourcing cognitive work without engagement, assess cognitive outsourcing:

Key concepts:
- Epistemic cognitive outsourcing: outsourcing all thinking without engagement
- Tool dependency: relying on tools without understanding
- Thinking delegation: having others do all intellectual work
- Comprehension bypass: getting answers without understanding
- Intellectual atrophy: thinking skills degrading from disuse
- AI dependency: relying on AI without developing own judgment
- Calculator mind: can get answers but can't reason

When epistemic cognitive outsourcing IS present:
- Outsourcing all thinking
- Relying on tools without understanding
- Having others do intellectual work
- Getting answers without understanding
- Thinking skills degrading
- Relying on AI without judgment
- Getting answers can't reason

When no cognitive outsourcing:
- Engaged thinking
- Understanding tools used
- Doing own intellectual work
- Understanding answers
- Thinking skills maintained
- AI as supplement not replacement
- Can reason independently

Output JSON with: cognitive_outsourcing_detected (bool), severity (none/mild/moderate/severe), tool_dependency (what relying on without understanding), thinking_delegation (what having others do), comprehension_bypass (what getting answers without understanding), intellectual_atrophy (what skills degrading from), recommendation (no_cognitive_outsourcing/mild_engagement_practice/significant_independence_recovery/major_intensive_thinking_rebuilding/emergency_complete_cognitive_outsourcing)."""

EPISTEMIC_COGNITIVE_OUTSOURCING_PROMPT = """Detect epistemic cognitive outsourcing:

Tool dependency: {tool_dependency}
Thinking delegation: {thinking_delegation}
Comprehension bypass: {comprehension_bypass}
Intellectual atrophy: {intellectual_atrophy}
Domain: {domain}
Context: {context}

Is there outsourcing all cognitive work to tools/others without engagement? Return ONLY valid JSON."""


class EpistemicCognitiveOutsourcingService:
    """Detects epistemic cognitive outsourcing — outsourcing thinking without engagement."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        tool_dependency: str,
        *,
        thinking_delegation: str = "",
        comprehension_bypass: str = "",
        intellectual_atrophy: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic cognitive outsourcing."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_COGNITIVE_OUTSOURCING_PROMPT.format(
                tool_dependency=tool_dependency,
                thinking_delegation=thinking_delegation or "Not specified",
                comprehension_bypass=comprehension_bypass or "Not specified",
                intellectual_atrophy=intellectual_atrophy or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_COGNITIVE_OUTSOURCING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "tool_dependency": tool_dependency[:200],
            "cognitive_outsourcing_detected": data.get("cognitive_outsourcing_detected", False),
            "severity": data.get("severity", ""),
            "thinking_delegation": data.get("thinking_delegation", ""),
            "comprehension_bypass": data.get("comprehension_bypass", ""),
            "intellectual_atrophy": data.get("intellectual_atrophy", ""),
            "recommendation": data.get("recommendation", ""),
        }
