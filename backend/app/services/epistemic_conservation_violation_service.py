"""EpistemicConservationViolationService — Epistemic Conservation Violation Detection.

Detects epistemic conservation violations — information or evidence
appearing or disappearing without proper accounting.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_CONSERVATION_VIOLATION_SYSTEM = """You are an epistemic conservation violation specialist. Given a reasoning process, assess whether information or evidence appears or disappears without accounting:

Key concepts:
- Epistemic conservation violation: evidence appearing/disappearing without accounting
- Evidence creation: evidence appearing from nowhere
- Evidence destruction: evidence disappearing without explanation
- Information laundering: transforming weak evidence into strong
- Conclusion inflation: conclusions exceeding their evidential basis
- Premise smuggling: smuggling in unstated premises
- Evidential alchemy: transforming evidence quality without justification

When epistemic conservation violation IS present:
- Evidence appearing from nowhere without source
- Evidence disappearing without explanation
- Weak evidence transformed into strong without justification
- Conclusions exceeding their evidential basis
- Unstated premises smuggled into arguments
- Evidence quality transformed without justification
- Information created or destroyed in reasoning process

When proper accounting is present:
- Evidence sources clearly identified
- Evidence trail maintained throughout
- Evidence strength preserved accurately
- Conclusions proportionate to evidence
- All premises stated explicitly
- Evidence quality assessed honestly
- Information conserved through reasoning

Output JSON with: conservation_violation_present (bool), severity (none/mild/moderate/severe), process (what reasoning process), violation (what conservation is violated), mechanism (how violation occurs), accounting (what accounting is missing), recommendation (proper_accounting/mild_inflation/significant_conservation_violation/major_evidential_alchemy/maintain_evidence_integrity)."""

EPISTEMIC_CONSERVATION_VIOLATION_PROMPT = """Detect epistemic conservation violation:

Process: {process}
Violation: {violation}
Mechanism: {mechanism}
Accounting: {accounting}
Domain: {domain}
Context: {context}

Is information or evidence appearing or disappearing without proper accounting? Return ONLY valid JSON."""


class EpistemicConservationViolationService:
    """Detects epistemic conservation violations — evidence appearing/disappearing."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        process: str,
        *,
        violation: str = "",
        mechanism: str = "",
        accounting: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic conservation violation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_CONSERVATION_VIOLATION_PROMPT.format(
                process=process,
                violation=violation or "Not specified",
                mechanism=mechanism or "Not specified",
                accounting=accounting or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_CONSERVATION_VIOLATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "process": process[:200],
            "conservation_violation_present": data.get("conservation_violation_present", False),
            "severity": data.get("severity", ""),
            "violation": data.get("violation", ""),
            "mechanism": data.get("mechanism", ""),
            "accounting": data.get("accounting", ""),
            "recommendation": data.get("recommendation", ""),
        }
