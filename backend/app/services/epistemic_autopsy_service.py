"""EpistemicAutopsyService — Epistemic Autopsy Detection.

Detects need for epistemic autopsy — systematic examination of why an
intellectual system died, revealing hidden causes of failure.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_AUTOPSY_SYSTEM = """You are an epistemic autopsy specialist. Given a failed intellectual system, assess what systematic examination reveals:

Key concepts:
- Epistemic autopsy: systematic examination of intellectual system death
- Gross findings: visible large-scale pathology
- Microscopic findings: subtle cellular-level damage
- Toxicology: poisonous influences contributing to death
- Histology: tissue-level changes revealing disease process
- Chain of causation: sequence of events leading to death
- Contributing factors: conditions that hastened death

When epistemic autopsy findings ARE present:
- Systematic examination reveals cause of intellectual death
- Visible large-scale pathology identified
- Subtle damage at detailed level found
- Poisonous influences identified
- Tissue-level changes revealing disease process
- Clear sequence of events leading to failure
- Multiple contributing factors identified

When no autopsy needed:
- System still alive and functioning
- No death to examine
- No pathology present
- No toxic influences
- Healthy tissue throughout
- No causal chain of failure
- No contributing factors

Output JSON with: autopsy_findings_present (bool), severity (none/mild/moderate/severe), gross_findings (what visible pathology), microscopic_findings (what subtle damage), toxicology (what poisonous influences), chain_of_causation (what sequence), recommendation (no_autopsy_needed/mild_findings/significant_autopsy_findings/major_systemic_failure/comprehensive_intellectual_post_mortem)."""

EPISTEMIC_AUTOPSY_PROMPT = """Detect epistemic autopsy findings:

Gross findings: {gross_findings}
Microscopic findings: {microscopic_findings}
Toxicology: {toxicology}
Chain of causation: {chain_of_causation}
Domain: {domain}
Context: {context}

What does systematic examination reveal about why this intellectual system failed? Return ONLY valid JSON."""


class EpistemicAutopsyService:
    """Detects epistemic autopsy findings — why intellectual systems died."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        gross_findings: str,
        *,
        microscopic_findings: str = "",
        toxicology: str = "",
        chain_of_causation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic autopsy findings."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_AUTOPSY_PROMPT.format(
                gross_findings=gross_findings,
                microscopic_findings=microscopic_findings or "Not specified",
                toxicology=toxicology or "Not specified",
                chain_of_causation=chain_of_causation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_AUTOPSY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "gross_findings": gross_findings[:200],
            "autopsy_findings_present": data.get("autopsy_findings_present", False),
            "severity": data.get("severity", ""),
            "microscopic_findings": data.get("microscopic_findings", ""),
            "toxicology": data.get("toxicology", ""),
            "chain_of_causation": data.get("chain_of_causation", ""),
            "recommendation": data.get("recommendation", ""),
        }
