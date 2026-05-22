"""EpistemicAdhdService — Epistemic ADHD Detection.

Detects epistemic ADHD — intellectual attention deficit with hyperactivity,
inability to sustain focus on single intellectual thread.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ADHD_SYSTEM = """You are an epistemic ADHD specialist. Given intellectual attention deficit, assess ADHD patterns:

Key concepts:
- Epistemic ADHD: intellectual attention deficit with hyperactivity
- Inattention: inability to sustain focus on single thread
- Hyperactivity: jumping between intellectual topics rapidly
- Impulsivity: acting on ideas without reflection
- Hyperfocus: paradoxical intense focus on novel stimuli
- Executive dysfunction: difficulty planning intellectual work
- Working memory: losing track of intellectual threads

When epistemic ADHD IS present:
- Intellectual attention deficit
- Cannot sustain single-thread focus
- Jumping between topics rapidly
- Acting on ideas without reflection
- Paradoxical intense novel focus
- Difficulty planning work
- Losing track of threads

When no ADHD:
- Sustained attention
- Single-thread focus maintained
- Orderly topic progression
- Reflective before acting
- Consistent focus patterns
- Effective planning
- Thread tracking maintained

Output JSON with: adhd_detected (bool), severity (none/mild/moderate/severe), inattention_level (what focus deficit), hyperactivity_pattern (what jumping), impulsivity_level (what unreflective action), executive_function (what planning deficit), recommendation (no_adhd/mild_structure_support/significant_behavioral_strategies/major_intensive_management/emergency_complete_dysfunction)."""

EPISTEMIC_ADHD_PROMPT = """Detect epistemic ADHD:

Inattention level: {inattention_level}
Hyperactivity pattern: {hyperactivity_pattern}
Impulsivity level: {impulsivity_level}
Executive function: {executive_function}
Domain: {domain}
Context: {context}

Is there intellectual attention deficit with inability to sustain focus? Return ONLY valid JSON."""


class EpistemicAdhdService:
    """Detects epistemic ADHD — intellectual attention deficit."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        inattention_level: str,
        *,
        hyperactivity_pattern: str = "",
        impulsivity_level: str = "",
        executive_function: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic ADHD."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ADHD_PROMPT.format(
                inattention_level=inattention_level,
                hyperactivity_pattern=hyperactivity_pattern or "Not specified",
                impulsivity_level=impulsivity_level or "Not specified",
                executive_function=executive_function or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ADHD_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "inattention_level": inattention_level[:200],
            "adhd_detected": data.get("adhd_detected", False),
            "severity": data.get("severity", ""),
            "hyperactivity_pattern": data.get("hyperactivity_pattern", ""),
            "impulsivity_level": data.get("impulsivity_level", ""),
            "executive_function": data.get("executive_function", ""),
            "recommendation": data.get("recommendation", ""),
        }
