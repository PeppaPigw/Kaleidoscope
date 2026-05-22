"""EpistemicCultDynamicsService — Epistemic Cult Dynamics Detection.

Detects epistemic cult dynamics — systematic thought control through
isolation, love-bombing, loaded language, and demand for absolute loyalty.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_CULT_DYNAMICS_SYSTEM = """You are an epistemic cult dynamics specialist. Given systematic thought control, assess cult dynamics:

Key concepts:
- Epistemic cult dynamics: systematic thought control
- Thought-stopping: techniques to prevent critical thinking
- Loaded language: special vocabulary that constrains thought
- Demand for purity: impossible standards creating guilt
- Sacred science: doctrine cannot be questioned
- Milieu control: controlling all information
- Dispensing of existence: only members have truth/value

When epistemic cult dynamics IS present:
- Systematic thought control
- Preventing critical thinking
- Special constraining vocabulary
- Impossible standards
- Doctrine unquestionable
- Information controlled
- Only members have truth

When no cult dynamics:
- Free thought
- Critical thinking encouraged
- Open language
- Reasonable standards
- Doctrine questionable
- Information accessible
- Truth available to all

Output JSON with: cult_dynamics_detected (bool), severity (none/mild/moderate/severe), thought_stopping (what preventing), loaded_language (what constraining), milieu_control (what controlling), sacred_science (what unquestionable), recommendation (no_cult_dynamics/mild_critical_thinking_recovery/significant_exit_counseling/major_intensive_deprogramming/emergency_complete_control)."""

EPISTEMIC_CULT_DYNAMICS_PROMPT = """Detect epistemic cult dynamics:

Thought stopping: {thought_stopping}
Loaded language: {loaded_language}
Milieu control: {milieu_control}
Sacred science: {sacred_science}
Domain: {domain}
Context: {context}

Is there systematic thought control through isolation and demand for absolute loyalty? Return ONLY valid JSON."""


class EpistemicCultDynamicsService:
    """Detects epistemic cult dynamics — systematic thought control."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        thought_stopping: str,
        *,
        loaded_language: str = "",
        milieu_control: str = "",
        sacred_science: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic cult dynamics."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_CULT_DYNAMICS_PROMPT.format(
                thought_stopping=thought_stopping,
                loaded_language=loaded_language or "Not specified",
                milieu_control=milieu_control or "Not specified",
                sacred_science=sacred_science or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_CULT_DYNAMICS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "thought_stopping": thought_stopping[:200],
            "cult_dynamics_detected": data.get("cult_dynamics_detected", False),
            "severity": data.get("severity", ""),
            "loaded_language": data.get("loaded_language", ""),
            "milieu_control": data.get("milieu_control", ""),
            "sacred_science": data.get("sacred_science", ""),
            "recommendation": data.get("recommendation", ""),
        }
