"""EpistemicInstitutionalBureaucraticEpistemologyService — Epistemic Institutional Bureaucratic Epistemology Detection.

Detects epistemic institutional bureaucratic epistemology — institutional
processes overriding evidence.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_INSTITUTIONAL_BUREAUCRATIC_EPISTEMOLOGY_SYSTEM = """You are an epistemic institutional bureaucratic epistemology specialist. Given process dominance, assess evidence displacement:

Key concepts:
- Epistemic bureaucratic epistemology: institutional processes overriding evidence
- Process over evidence: procedural compliance treated as more real than evidence
- Form over substance: correct forms valued over substantive truth
- Procedural truth: what the process records treated as true
- Documentation as reality: documented claims replacing observed reality

When epistemic bureaucratic epistemology IS present:
- Process overrides evidence
- Form displaces substance
- Procedural truth dominates
- Documentation replaces reality
- Institutional records outweigh observations

When no bureaucratic epistemology:
- Evidence can override process
- Substance matters more than form
- Procedures remain truth-seeking tools
- Documentation checked against reality
- Observations can correct records

Output JSON with: bureaucratic_epistemology_detected (bool), severity (none/mild/moderate/severe), form_over_substance (what form over substance), procedural_truth (what procedural truth), documentation_as_reality (what documentation as reality), recommendation (no_bureaucratic_epistemology/mild_evidence_check/significant_process_review/major_intensive_bureaucratic_reform/emergency_complete_bureaucratic_epistemology)."""

EPISTEMIC_INSTITUTIONAL_BUREAUCRATIC_EPISTEMOLOGY_PROMPT = """Detect epistemic institutional bureaucratic epistemology:

Process over evidence: {process_over_evidence}
Form over substance: {form_over_substance}
Procedural truth: {procedural_truth}
Documentation as reality: {documentation_as_reality}
Domain: {domain}
Context: {context}

Are institutional processes overriding evidence? Return ONLY valid JSON."""


class EpistemicInstitutionalBureaucraticEpistemologyService:
    """Detects epistemic bureaucratic epistemology — process over evidence."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        process_over_evidence: str,
        *,
        form_over_substance: str = "",
        procedural_truth: str = "",
        documentation_as_reality: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic institutional bureaucratic epistemology."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_INSTITUTIONAL_BUREAUCRATIC_EPISTEMOLOGY_PROMPT.format(
                process_over_evidence=process_over_evidence,
                form_over_substance=form_over_substance or "Not specified",
                procedural_truth=procedural_truth or "Not specified",
                documentation_as_reality=documentation_as_reality or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_INSTITUTIONAL_BUREAUCRATIC_EPISTEMOLOGY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "process_over_evidence": process_over_evidence[:200],
            "bureaucratic_epistemology_detected": data.get("bureaucratic_epistemology_detected", False),
            "severity": data.get("severity", ""),
            "form_over_substance": data.get("form_over_substance", ""),
            "procedural_truth": data.get("procedural_truth", ""),
            "documentation_as_reality": data.get("documentation_as_reality", ""),
            "recommendation": data.get("recommendation", ""),
        }
