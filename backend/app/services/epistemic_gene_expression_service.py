"""EpistemicGeneExpressionService — Epistemic Gene Expression Detection.

Detects epistemic gene expression patterns — which intellectual genes are
active vs silenced, determining what potential is realized.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_GENE_EXPRESSION_SYSTEM = """You are an epistemic gene expression specialist. Given intellectual potential, assess which genes are active vs silenced:

Key concepts:
- Epistemic gene expression: which intellectual genes are active vs silenced
- Promoter: region controlling when gene activates
- Silencer: region preventing gene activation
- Transcription factor: protein enabling gene reading
- Housekeeping gene: always-on essential function
- Tissue-specific: only active in certain contexts
- Inducible: activated only by specific signals

When epistemic gene expression IS abnormal:
- Intellectual genes inappropriately active or silenced
- Promoter regions malfunctioning
- Silencer regions failing or overactive
- Transcription factors missing or excessive
- Essential functions turned off
- Context-specific genes active everywhere
- Signal-responsive genes stuck on or off

When normal expression is present:
- Appropriate gene activation patterns
- Functional promoter regions
- Proper silencer function
- Correct transcription factor levels
- Essential functions always on
- Context-specific activation
- Proper signal responsiveness

Output JSON with: expression_abnormal (bool), severity (none/mild/moderate/severe), promoter_dysfunction (what activation control failure), silencer_failure (what prevention failure), transcription_factor (what enabler problem), tissue_specificity (what context error), recommendation (normal_expression/mild_dysregulation/significant_expression_abnormality/major_gene_silencing/restore_intellectual_expression_pattern)."""

EPISTEMIC_GENE_EXPRESSION_PROMPT = """Detect epistemic gene expression abnormality:

Promoter dysfunction: {promoter_dysfunction}
Silencer failure: {silencer_failure}
Transcription factor: {transcription_factor}
Tissue specificity: {tissue_specificity}
Domain: {domain}
Context: {context}

Are intellectual genes inappropriately active or silenced? Return ONLY valid JSON."""


class EpistemicGeneExpressionService:
    """Detects epistemic gene expression — active vs silenced intellectual genes."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        promoter_dysfunction: str,
        *,
        silencer_failure: str = "",
        transcription_factor: str = "",
        tissue_specificity: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic gene expression abnormality."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_GENE_EXPRESSION_PROMPT.format(
                promoter_dysfunction=promoter_dysfunction,
                silencer_failure=silencer_failure or "Not specified",
                transcription_factor=transcription_factor or "Not specified",
                tissue_specificity=tissue_specificity or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_GENE_EXPRESSION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "promoter_dysfunction": promoter_dysfunction[:200],
            "expression_abnormal": data.get("expression_abnormal", False),
            "severity": data.get("severity", ""),
            "silencer_failure": data.get("silencer_failure", ""),
            "transcription_factor": data.get("transcription_factor", ""),
            "tissue_specificity": data.get("tissue_specificity", ""),
            "recommendation": data.get("recommendation", ""),
        }
