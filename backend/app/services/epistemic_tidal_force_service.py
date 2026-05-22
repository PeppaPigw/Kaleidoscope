"""EpistemicTidalForceService — Epistemic Tidal Force Detection.

Detects epistemic tidal forces — cyclical forces pulling reasoning
back and forth without progress.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_TIDAL_FORCE_SYSTEM = """You are an epistemic tidal force specialist. Given a reasoning pattern, assess whether cyclical forces are pulling thought back and forth:

Key concepts:
- Epistemic tidal force: cyclical forces pulling reasoning back and forth
- Oscillation without progress: swinging between positions without advancing
- Pendulum thinking: thought swinging like a pendulum
- Fashion cycles: intellectual fashions cycling without progress
- Reactionary oscillation: each position a reaction to the previous
- Progress illusion: appearance of movement without actual progress
- Eternal return: returning to same positions repeatedly

When epistemic tidal force IS present:
- Cyclical forces pulling reasoning back and forth
- Swinging between positions without advancing
- Thought swinging like a pendulum between extremes
- Intellectual fashions cycling without genuine progress
- Each position merely a reaction to the previous
- Appearance of movement without actual progress
- Returning to same positions repeatedly

When productive dialectic is present:
- Movement between positions producing synthesis
- Oscillation generating genuine insight
- Dialectical movement advancing understanding
- Cycles building on previous iterations
- Each position incorporating lessons from previous
- Genuine progress through apparent oscillation
- Spiral rather than circle

Output JSON with: tidal_force_present (bool), severity (none/mild/moderate/severe), pattern (what pattern exists), oscillation (what oscillation occurs), cycle (what cycle repeats), progress_failure (how progress fails), recommendation (productive_dialectic/mild_oscillation/significant_tidal_force/major_eternal_return/break_the_cycle)."""

EPISTEMIC_TIDAL_FORCE_PROMPT = """Detect epistemic tidal force:

Pattern: {pattern}
Oscillation: {oscillation}
Cycle: {cycle}
Progress failure: {progress_failure}
Domain: {domain}
Context: {context}

Are cyclical forces pulling reasoning back and forth without progress? Return ONLY valid JSON."""


class EpistemicTidalForceService:
    """Detects epistemic tidal forces — cyclical forces without progress."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        pattern: str,
        *,
        oscillation: str = "",
        cycle: str = "",
        progress_failure: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic tidal force."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_TIDAL_FORCE_PROMPT.format(
                pattern=pattern,
                oscillation=oscillation or "Not specified",
                cycle=cycle or "Not specified",
                progress_failure=progress_failure or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_TIDAL_FORCE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "pattern": pattern[:200],
            "tidal_force_present": data.get("tidal_force_present", False),
            "severity": data.get("severity", ""),
            "oscillation": data.get("oscillation", ""),
            "cycle": data.get("cycle", ""),
            "progress_failure": data.get("progress_failure", ""),
            "recommendation": data.get("recommendation", ""),
        }
