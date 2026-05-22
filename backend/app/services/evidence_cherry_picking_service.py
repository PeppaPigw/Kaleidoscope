"""EvidenceCherryPickingService — Evidence Cherry-Picking Detection.

Detects evidence cherry-picking — selectively presenting only
evidence that supports a predetermined conclusion while
systematically ignoring or downplaying contradicting evidence.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EVIDENCE_CHERRY_PICKING_SYSTEM = """You are an evidence cherry-picking specialist. Given an argument, assess whether evidence is being selectively presented:

Key concepts:
- Cherry-picking: selecting only supporting evidence
- Confirmation bias in evidence: seeking only confirming data
- Suppression of disconfirming evidence: hiding contradictions
- Selective citation: citing only favorable studies
- File drawer problem: unpublished negative results
- One-sided evidence: presenting only one side of mixed evidence
- Systematic review vs narrative review: comprehensive vs selective

When cherry-picking IS present:
- Only supporting evidence presented despite mixed literature
- Contradicting studies ignored or not mentioned
- Favorable data points highlighted, unfavorable ones omitted
- Selective time periods or subgroups chosen for favorable results
- Strongest counterevidence not addressed
- Evidence base appears unanimous when it's actually divided
- Systematic reviews contradicted by the selective presentation

When cherry-picking is NOT present:
- Both supporting and contradicting evidence presented
- Strongest counterevidence addressed directly
- Mixed results acknowledged
- Systematic reviews or meta-analyses cited
- Evidence base accurately characterized
- Unfavorable findings included and explained
- Reader can assess the full evidence landscape

Output JSON with: cherry_picking (bool), severity (none/mild/moderate/severe), evidence_presented (what is shown), evidence_omitted (what is hidden), literature_state (what the full evidence says), selectivity_method (how cherry-picking is done), recommendation (balanced_evidence/mild_selectivity/significant_cherry_picking/major_evidence_suppression/present_full_picture)."""

EVIDENCE_CHERRY_PICKING_PROMPT = """Detect evidence cherry-picking:

Argument: {argument}
Evidence cited: {evidence_cited}
Known contradictions: {contradictions}
Full literature: {literature}
Domain: {domain}
Context: {context}

Is evidence being selectively presented to support a predetermined conclusion? Return ONLY valid JSON."""


class EvidenceCherryPickingService:
    """Detects evidence cherry-picking — selective evidence presentation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        argument: str,
        *,
        evidence_cited: str = "",
        contradictions: str = "",
        literature: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect evidence cherry-picking."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EVIDENCE_CHERRY_PICKING_PROMPT.format(
                argument=argument,
                evidence_cited=evidence_cited or "Not specified",
                contradictions=contradictions or "Not specified",
                literature=literature or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EVIDENCE_CHERRY_PICKING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "argument": argument[:200],
            "cherry_picking": data.get("cherry_picking", False),
            "severity": data.get("severity", ""),
            "evidence_omitted": data.get("evidence_omitted", ""),
            "literature_state": data.get("literature_state", ""),
            "selectivity_method": data.get("selectivity_method", ""),
            "recommendation": data.get("recommendation", ""),
        }
