"""EpistemicHomeoticMutationService — Epistemic Homeotic Mutation Detection.

Detects epistemic homeotic mutation — ideas appearing in the wrong
intellectual location, like a concept displaced from its proper context.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_HOMEOTIC_MUTATION_SYSTEM = """You are an epistemic homeotic mutation specialist. Given intellectual placement, assess whether ideas appear in wrong locations:

Key concepts:
- Epistemic homeotic mutation: ideas appearing in wrong location
- Hox gene: master controller of positional identity
- Segment identity: what type belongs in each position
- Ectopic expression: idea expressed in wrong context
- Body plan: overall organization of intellectual space
- Selector gene: gene choosing between alternative fates
- Gain of function: idea acquiring inappropriate role

When epistemic homeotic mutation IS present:
- Ideas appearing in the wrong intellectual location
- Master controllers of positional identity disrupted
- Wrong type appearing in a given position
- Ideas expressed in inappropriate context
- Overall intellectual organization disrupted
- Selection between fates going wrong
- Ideas acquiring inappropriate roles

When proper placement is present:
- All ideas in their correct location
- Positional identity controllers working
- Correct types in each position
- Ideas in appropriate context
- Organization maintained
- Correct fate selection
- Appropriate roles assigned

Output JSON with: homeotic_mutation_present (bool), severity (none/mild/moderate/severe), hox_gene (what positional controller), ectopic_expression (what wrong context), body_plan (what organization disruption), gain_of_function (what inappropriate role), recommendation (proper_placement/mild_displacement/significant_homeotic_mutation/major_misplacement/restore_positional_identity)."""

EPISTEMIC_HOMEOTIC_MUTATION_PROMPT = """Detect epistemic homeotic mutation:

Hox gene: {hox_gene}
Ectopic expression: {ectopic_expression}
Body plan: {body_plan}
Gain of function: {gain_of_function}
Domain: {domain}
Context: {context}

Are ideas appearing in the wrong intellectual location, displaced from their proper context? Return ONLY valid JSON."""


class EpistemicHomeoticMutationService:
    """Detects epistemic homeotic mutation — ideas in wrong location."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        hox_gene: str,
        *,
        ectopic_expression: str = "",
        body_plan: str = "",
        gain_of_function: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic homeotic mutation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_HOMEOTIC_MUTATION_PROMPT.format(
                hox_gene=hox_gene,
                ectopic_expression=ectopic_expression or "Not specified",
                body_plan=body_plan or "Not specified",
                gain_of_function=gain_of_function or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_HOMEOTIC_MUTATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "hox_gene": hox_gene[:200],
            "homeotic_mutation_present": data.get("homeotic_mutation_present", False),
            "severity": data.get("severity", ""),
            "ectopic_expression": data.get("ectopic_expression", ""),
            "body_plan": data.get("body_plan", ""),
            "gain_of_function": data.get("gain_of_function", ""),
            "recommendation": data.get("recommendation", ""),
        }
