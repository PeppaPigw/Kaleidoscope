"""EpistemicIntellectualCodependencyService — Epistemic Intellectual Codependency Detection.

Detects epistemic intellectual codependency — codependent intellectual
relationships where one can't think independently.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_INTELLECTUAL_CODEPENDENCY_SYSTEM = """You are an epistemic intellectual codependency specialist. Given codependent intellectual relationships, assess codependency:

Key concepts:
- Epistemic intellectual codependency: can't think independently
- Thought outsourcing: delegating all thinking to another
- Validation addiction: needing constant intellectual approval
- Intellectual caretaking: managing another's thinking at expense of own
- Enabling ignorance: supporting another's avoidance of thinking
- Rescue thinking: always solving another's intellectual problems
- Mutual intellectual disability: both parties unable to think alone

When epistemic intellectual codependency IS present:
- Can't think independently
- Delegating all thinking
- Needing constant approval
- Managing another's thinking
- Supporting avoidance of thinking
- Always solving for another
- Both unable to think alone

When no intellectual codependency:
- Independent thinking
- Self-directed thought
- Self-validated
- Own thinking prioritized
- Encouraging independence
- Supporting self-solving
- Both capable alone

Output JSON with: intellectual_codependency_detected (bool), severity (none/mild/moderate/severe), thought_outsourcing (what delegating to another), validation_addiction (what needing approval for), intellectual_caretaking (what managing for another), rescue_thinking (what always solving for), recommendation (no_intellectual_codependency/mild_independence_practice/significant_autonomy_building/major_intensive_separation_work/emergency_complete_intellectual_dependency)."""

EPISTEMIC_INTELLECTUAL_CODEPENDENCY_PROMPT = """Detect epistemic intellectual codependency:

Thought outsourcing: {thought_outsourcing}
Validation addiction: {validation_addiction}
Intellectual caretaking: {intellectual_caretaking}
Rescue thinking: {rescue_thinking}
Domain: {domain}
Context: {context}

Is there codependent intellectual relationships where one can't think independently? Return ONLY valid JSON."""


class EpistemicIntellectualCodependencyService:
    """Detects epistemic intellectual codependency — can't think independently."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        thought_outsourcing: str,
        *,
        validation_addiction: str = "",
        intellectual_caretaking: str = "",
        rescue_thinking: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic intellectual codependency."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_INTELLECTUAL_CODEPENDENCY_PROMPT.format(
                thought_outsourcing=thought_outsourcing,
                validation_addiction=validation_addiction or "Not specified",
                intellectual_caretaking=intellectual_caretaking or "Not specified",
                rescue_thinking=rescue_thinking or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_INTELLECTUAL_CODEPENDENCY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "thought_outsourcing": thought_outsourcing[:200],
            "intellectual_codependency_detected": data.get("intellectual_codependency_detected", False),
            "severity": data.get("severity", ""),
            "validation_addiction": data.get("validation_addiction", ""),
            "intellectual_caretaking": data.get("intellectual_caretaking", ""),
            "rescue_thinking": data.get("rescue_thinking", ""),
            "recommendation": data.get("recommendation", ""),
        }
