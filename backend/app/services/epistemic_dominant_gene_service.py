"""EpistemicDominantGeneService — Epistemic Dominant Gene Detection.

Detects epistemic dominant genes — beliefs that always express
regardless of what other beliefs are present.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_DOMINANT_GENE_SYSTEM = """You are an epistemic dominant gene specialist. Given a belief system, assess whether certain beliefs always dominate expression regardless of context:

Key concepts:
- Epistemic dominant gene: belief always expressing regardless of context
- Expression dominance: always expressed over alternatives
- Suppression of alternatives: suppressing other valid beliefs
- Context independence: expressing regardless of appropriateness
- Override mechanism: overriding more appropriate beliefs
- Recessive suppression: suppressing more nuanced alternatives
- Phenotypic fixation: fixed expression regardless of environment

When epistemic dominant gene IS present:
- Belief always expressing regardless of context
- Always expressed over more appropriate alternatives
- Suppressing other valid beliefs from expression
- Expressing regardless of contextual appropriateness
- Overriding more appropriate beliefs in context
- Suppressing more nuanced alternatives
- Fixed expression regardless of intellectual environment

When appropriate expression is present:
- Beliefs expressed based on context
- Most appropriate belief expressed in each context
- Multiple beliefs available for expression
- Context-sensitive belief expression
- Appropriate beliefs selected for context
- Nuanced alternatives available
- Flexible expression matching environment

Output JSON with: dominant_gene_present (bool), severity (none/mild/moderate/severe), belief (what belief dominates), suppressed (what alternatives are suppressed), context_independence (how context-independent), override (what it overrides), recommendation (appropriate_expression/mild_dominance/significant_dominant_gene/major_expression_fixation/restore_context_sensitivity)."""

EPISTEMIC_DOMINANT_GENE_PROMPT = """Detect epistemic dominant gene:

Belief: {belief}
Suppressed: {suppressed}
Context independence: {context_independence}
Override: {override}
Domain: {domain}
Context: {context}

Does this belief always dominate expression regardless of context? Return ONLY valid JSON."""


class EpistemicDominantGeneService:
    """Detects epistemic dominant genes — beliefs always expressing regardless of context."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        belief: str,
        *,
        suppressed: str = "",
        context_independence: str = "",
        override: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic dominant gene."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_DOMINANT_GENE_PROMPT.format(
                belief=belief,
                suppressed=suppressed or "Not specified",
                context_independence=context_independence or "Not specified",
                override=override or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_DOMINANT_GENE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "belief": belief[:200],
            "dominant_gene_present": data.get("dominant_gene_present", False),
            "severity": data.get("severity", ""),
            "suppressed": data.get("suppressed", ""),
            "context_independence": data.get("context_independence", ""),
            "override": data.get("override", ""),
            "recommendation": data.get("recommendation", ""),
        }
