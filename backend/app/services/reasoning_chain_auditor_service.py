"""ReasoningChainAuditorService — Logical Inference Validation.

Validates multi-step reasoning chains by checking each inference step
for logical validity, evidential support, and inferential gaps. Identifies
where reasoning jumps occur and whether conclusions follow from premises.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

AUDIT_SYSTEM = """You are a reasoning chain auditor. Given a multi-step argument or reasoning chain, validate each inference step. For each step check:
- Logical validity: does the conclusion follow from the premises?
- Evidential support: is there evidence for this step?
- Inferential gap: how big is the leap from premises to conclusion?
- Hidden premises: what unstated assumptions bridge the gap?
- Alternative conclusions: could the same premises lead elsewhere?

Output JSON with: steps (list of: step_number, premise, conclusion, validity (valid/questionable/invalid), gap_size (none/small/moderate/large/chasm), hidden_premises (list), alternative_conclusions (list), confidence (0-1)), overall_validity (0-1), weakest_step (which step number and why), chain_type (deductive/inductive/abductive/mixed), logical_fallacies (list of: step, fallacy_name, explanation), verdict (sound/mostly_sound/flawed/broken)."""

AUDIT_PROMPT = """Audit this reasoning chain:

Argument: {argument}
Domain: {domain}

Validate each inference step. Return ONLY valid JSON."""


class ReasoningChainAuditorService:
    """Validates logical structure of multi-step reasoning."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def audit_chain(
        self,
        argument: str,
        *,
        domain: str = "",
    ) -> dict:
        """Audit a reasoning chain for logical validity."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=AUDIT_PROMPT.format(
                argument=argument,
                domain=domain or "general",
            ),
            system=AUDIT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        steps = data.get("steps", [])
        return {
            "argument": argument[:200],
            "steps_audited": len(steps),
            "steps": steps,
            "overall_validity": data.get("overall_validity", 0),
            "weakest_step": data.get("weakest_step", ""),
            "chain_type": data.get("chain_type", ""),
            "fallacies": data.get("logical_fallacies", []),
            "verdict": data.get("verdict", ""),
        }
