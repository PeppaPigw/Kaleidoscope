"""EpistemicPlasticityFailureService — Epistemic Plasticity Failure Detection.

Detects epistemic plasticity failure — inability to form new
belief connections or update existing belief structures.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PLASTICITY_FAILURE_SYSTEM = """You are an epistemic plasticity failure specialist. Given a belief system, assess whether it has lost the ability to form new connections or update:

Key concepts:
- Epistemic plasticity failure: inability to form new belief connections
- Rigidification: belief system becoming rigid and inflexible
- Connection failure: inability to form new associations
- Update resistance: resistance to updating existing beliefs
- Learning disability: inability to learn from new information
- Structural fixation: belief structure fixed and unchangeable
- Adaptation failure: failure to adapt to new evidence

When epistemic plasticity failure IS present:
- Inability to form new belief connections
- Belief system becoming rigid and inflexible
- Inability to form new intellectual associations
- Resistance to updating existing beliefs with new evidence
- Inability to learn from new information
- Belief structure fixed and unchangeable
- Failure to adapt to new evidence or circumstances

When healthy plasticity is present:
- Readily forming new belief connections
- Belief system flexible and adaptive
- New associations formed easily
- Beliefs updated with new evidence
- Learning from new information
- Belief structure adaptable
- Adapting to new evidence and circumstances

Output JSON with: plasticity_failure_present (bool), severity (none/mild/moderate/severe), system (what system is rigid), rigidity (what rigidity exists), connection_failure (what connections fail), update_resistance (what updates are resisted), recommendation (healthy_plasticity/mild_rigidity/significant_plasticity_failure/major_rigidification/restore_flexibility)."""

EPISTEMIC_PLASTICITY_FAILURE_PROMPT = """Detect epistemic plasticity failure:

System: {system}
Rigidity: {rigidity}
Connection failure: {connection_failure}
Update resistance: {update_resistance}
Domain: {domain}
Context: {context}

Has this belief system lost the ability to form new connections or update? Return ONLY valid JSON."""


class EpistemicPlasticityFailureService:
    """Detects epistemic plasticity failure — inability to update belief structures."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        system: str,
        *,
        rigidity: str = "",
        connection_failure: str = "",
        update_resistance: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic plasticity failure."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PLASTICITY_FAILURE_PROMPT.format(
                system=system,
                rigidity=rigidity or "Not specified",
                connection_failure=connection_failure or "Not specified",
                update_resistance=update_resistance or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PLASTICITY_FAILURE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "system": system[:200],
            "plasticity_failure_present": data.get("plasticity_failure_present", False),
            "severity": data.get("severity", ""),
            "rigidity": data.get("rigidity", ""),
            "connection_failure": data.get("connection_failure", ""),
            "update_resistance": data.get("update_resistance", ""),
            "recommendation": data.get("recommendation", ""),
        }
