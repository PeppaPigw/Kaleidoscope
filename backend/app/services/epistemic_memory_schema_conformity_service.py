"""EpistemicMemorySchemaConformityService — Epistemic Memory Schema Conformity Detection.

Detects epistemic memory schema conformity — memories conforming to schemas
and expectations rather than preserving actual experience.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_MEMORY_SCHEMA_CONFORMITY_SYSTEM = """You are an epistemic memory schema conformity specialist. Given schema-conforming memory, assess expectation-driven distortion:

Key concepts:
- Epistemic memory schema conformity: memories conforming to expectations
- Script-based filling: filling memory gaps with script-expected events
- Stereotype-consistent recall: remembering stereotype-consistent details
- Schema-driven intrusions: schema-expected events intruding into memory
- Expectation-based editing: editing memories to match expectations
- Cultural schema imposition: cultural schemas shaping what is remembered
- Professional schema bias: professional training schemas distorting recall

When epistemic memory schema conformity IS present:
- Memories conforming to schemas
- Scripts filling gaps
- Stereotypes biasing recall
- Schema intrusions present
- Expectations editing memories
- Cultural schemas imposed
- Professional schemas biasing

When no schema conformity:
- Memories preserve unexpected details
- Gaps acknowledged not filled
- Stereotypes not biasing
- Intrusions recognized
- Expectations distinguished from memory
- Cultural schemas acknowledged
- Professional bias recognized

Output JSON with: schema_conformity_detected (bool), severity (none/mild/moderate/severe), script_based_filling (what scripts filling), stereotype_consistent_recall (what stereotypes biasing), schema_driven_intrusions (what intrusions), expectation_based_editing (what expectations editing), recommendation (no_schema_conformity/mild_schema_awareness/significant_expectation_checking/major_intensive_memory_verification/emergency_complete_schema_conformity)."""

EPISTEMIC_MEMORY_SCHEMA_CONFORMITY_PROMPT = """Detect epistemic memory schema conformity:

Script based filling: {script_based_filling}
Stereotype consistent recall: {stereotype_consistent_recall}
Schema driven intrusions: {schema_driven_intrusions}
Expectation based editing: {expectation_based_editing}
Domain: {domain}
Context: {context}

Are memories conforming to schemas rather than preserving actual experience? Return ONLY valid JSON."""


class EpistemicMemorySchemaConformityService:
    """Detects epistemic memory schema conformity — expectation-driven distortion."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        script_based_filling: str,
        *,
        stereotype_consistent_recall: str = "",
        schema_driven_intrusions: str = "",
        expectation_based_editing: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic memory schema conformity."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_MEMORY_SCHEMA_CONFORMITY_PROMPT.format(
                script_based_filling=script_based_filling,
                stereotype_consistent_recall=stereotype_consistent_recall or "Not specified",
                schema_driven_intrusions=schema_driven_intrusions or "Not specified",
                expectation_based_editing=expectation_based_editing or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_MEMORY_SCHEMA_CONFORMITY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "script_based_filling": script_based_filling[:200],
            "schema_conformity_detected": data.get("schema_conformity_detected", False),
            "severity": data.get("severity", ""),
            "stereotype_consistent_recall": data.get("stereotype_consistent_recall", ""),
            "schema_driven_intrusions": data.get("schema_driven_intrusions", ""),
            "expectation_based_editing": data.get("expectation_based_editing", ""),
            "recommendation": data.get("recommendation", ""),
        }
