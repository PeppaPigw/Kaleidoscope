"""EpistemicStructuralFatigueService — Epistemic Structural Fatigue Detection.

Detects epistemic structural fatigue — knowledge structures weakening
from repeated stress without repair.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_STRUCTURAL_FATIGUE_SYSTEM = """You are an epistemic structural fatigue specialist. Given a knowledge structure, assess whether repeated stress is causing weakening:

Key concepts:
- Epistemic structural fatigue: weakening from repeated stress
- Stress accumulation: stress accumulating without repair
- Micro-damage: small damages accumulating over time
- Repair failure: failure to repair after stress
- Brittleness increase: structure becoming more brittle
- Failure threshold: approaching threshold of failure
- Invisible weakening: weakening not visible until failure

When epistemic structural fatigue IS present:
- Knowledge structures weakening from repeated stress
- Stress accumulating without repair
- Small damages accumulating over time
- Failure to repair after each stress event
- Structure becoming more brittle over time
- Approaching threshold of sudden failure
- Weakening not visible until catastrophic failure

When maintained resilience is present:
- Structures repaired after stress
- Stress not accumulating
- Damage repaired as it occurs
- Regular maintenance and repair
- Structure maintaining flexibility
- Well below failure threshold
- Health visible and monitored

Output JSON with: structural_fatigue_present (bool), severity (none/mild/moderate/severe), structure (what structure is affected), stress (what stress is applied), accumulation (how damage accumulates), threshold (how close to failure), recommendation (maintained_resilience/mild_wear/significant_fatigue/major_failure_risk/repair_and_reinforce)."""

EPISTEMIC_STRUCTURAL_FATIGUE_PROMPT = """Detect epistemic structural fatigue:

Structure: {structure}
Stress: {stress}
Accumulation: {accumulation}
Threshold: {threshold}
Domain: {domain}
Context: {context}

Are knowledge structures weakening from repeated stress without repair? Return ONLY valid JSON."""


class EpistemicStructuralFatigueService:
    """Detects epistemic structural fatigue — weakening from repeated stress."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        structure: str,
        *,
        stress: str = "",
        accumulation: str = "",
        threshold: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic structural fatigue."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_STRUCTURAL_FATIGUE_PROMPT.format(
                structure=structure,
                stress=stress or "Not specified",
                accumulation=accumulation or "Not specified",
                threshold=threshold or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_STRUCTURAL_FATIGUE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "structure": structure[:200],
            "structural_fatigue_present": data.get("structural_fatigue_present", False),
            "severity": data.get("severity", ""),
            "stress": data.get("stress", ""),
            "accumulation": data.get("accumulation", ""),
            "threshold": data.get("threshold", ""),
            "recommendation": data.get("recommendation", ""),
        }
