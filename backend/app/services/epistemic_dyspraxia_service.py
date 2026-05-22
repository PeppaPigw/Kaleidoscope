"""EpistemicDyspraxiaService — Epistemic Dyspraxia Detection.

Detects epistemic dyspraxia — difficulty coordinating intellectual
actions, planning sequences, and executing complex thought operations.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_DYSPRAXIA_SYSTEM = """You are an epistemic dyspraxia specialist. Given intellectual coordination difficulty, assess dyspraxia patterns:

Key concepts:
- Epistemic dyspraxia: difficulty coordinating intellectual actions
- Motor planning: struggling to sequence intellectual operations
- Coordination: poor integration of multiple thought streams
- Ideational: difficulty conceiving what to do intellectually
- Ideomotor: knowing what to do but unable to execute
- Sequencing: steps performed out of order
- Automaticity: inability to make intellectual skills automatic

When epistemic dyspraxia IS present:
- Difficulty coordinating actions
- Struggling to sequence operations
- Poor thought stream integration
- Difficulty conceiving what to do
- Knowing but unable to execute
- Steps out of order
- Cannot make skills automatic

When no dyspraxia:
- Smooth coordination
- Natural sequencing
- Integrated thought streams
- Clear conception
- Smooth execution
- Correct ordering
- Skills become automatic

Output JSON with: dyspraxia_detected (bool), severity (none/mild/moderate/severe), coordination_level (what integration difficulty), sequencing_ability (what ordering), ideational_capacity (what conception), automaticity_status (what skill automation), recommendation (no_dyspraxia/mild_structured_practice/significant_occupational_support/major_intensive_coordination/emergency_complete_dysfunction)."""

EPISTEMIC_DYSPRAXIA_PROMPT = """Detect epistemic dyspraxia:

Coordination level: {coordination_level}
Sequencing ability: {sequencing_ability}
Ideational capacity: {ideational_capacity}
Automaticity status: {automaticity_status}
Domain: {domain}
Context: {context}

Is there difficulty coordinating intellectual actions and planning sequences? Return ONLY valid JSON."""


class EpistemicDyspraxiaService:
    """Detects epistemic dyspraxia — intellectual coordination difficulty."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        coordination_level: str,
        *,
        sequencing_ability: str = "",
        ideational_capacity: str = "",
        automaticity_status: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic dyspraxia."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_DYSPRAXIA_PROMPT.format(
                coordination_level=coordination_level,
                sequencing_ability=sequencing_ability or "Not specified",
                ideational_capacity=ideational_capacity or "Not specified",
                automaticity_status=automaticity_status or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_DYSPRAXIA_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "coordination_level": coordination_level[:200],
            "dyspraxia_detected": data.get("dyspraxia_detected", False),
            "severity": data.get("severity", ""),
            "sequencing_ability": data.get("sequencing_ability", ""),
            "ideational_capacity": data.get("ideational_capacity", ""),
            "automaticity_status": data.get("automaticity_status", ""),
            "recommendation": data.get("recommendation", ""),
        }
