"""UnknownUnknownsService — Unknown Unknowns Blindness Detection.

Detects unknown unknowns blindness — inability to recognize the
existence of things you don't know you don't know, treating the
known space as the complete space.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

UNKNOWN_UNKNOWNS_SYSTEM = """You are an unknown unknowns specialist. Given an assessment or plan, evaluate whether unknown unknowns are being adequately considered:

Key concepts:
- Unknown unknowns: things you don't know you don't know
- Rumsfeld matrix: known knowns, known unknowns, unknown unknowns
- Epistemic humility: acknowledging limits of knowledge
- Black swan blindness: not accounting for unforeseen events
- Map-territory gap: treating map as complete territory
- Completeness illusion: believing you've identified all factors
- Surprise budget: allocating resources for the unexpected

When unknown unknowns blindness IS present:
- Assessment treats known space as complete space
- No acknowledgment of potential unknown factors
- Plan has no contingency for unforeseen events
- Confidence assumes all relevant factors identified
- No surprise budget or margin for error
- Risk assessment only covers known risks
- Completeness assumed without justification

When assessment is appropriately bounded:
- Unknown unknowns explicitly acknowledged
- Contingency for unforeseen events included
- Confidence appropriately limited by unknowns
- Surprise budget allocated
- Assessment bounded by stated assumptions
- Humility about completeness of knowledge
- Mechanisms for detecting unknown unknowns in place

Output JSON with: blindness_present (bool), severity (none/mild/moderate/severe), assessment (what is assessed), known_space (what is treated as complete), potential_unknowns (what might be unknown), contingency (what contingency exists), recommendation (appropriate_bounded_assessment/mild_completeness_assumption/significant_unknown_unknowns_blindness/major_completeness_illusion/acknowledge_unknown_unknowns)."""

UNKNOWN_UNKNOWNS_PROMPT = """Detect unknown unknowns blindness:

Assessment: {assessment}
Factors considered: {factors}
Contingency: {contingency}
Confidence level: {confidence}
Domain: {domain}
Context: {context}

Is the assessment treating the known space as the complete space without acknowledging unknown unknowns? Return ONLY valid JSON."""


class UnknownUnknownsService:
    """Detects unknown unknowns blindness — treating known space as complete."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        assessment: str,
        *,
        factors: str = "",
        contingency: str = "",
        confidence: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect unknown unknowns blindness."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=UNKNOWN_UNKNOWNS_PROMPT.format(
                assessment=assessment,
                factors=factors or "Not specified",
                contingency=contingency or "Not specified",
                confidence=confidence or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=UNKNOWN_UNKNOWNS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "assessment": assessment[:200],
            "blindness_present": data.get("blindness_present", False),
            "severity": data.get("severity", ""),
            "known_space": data.get("known_space", ""),
            "potential_unknowns": data.get("potential_unknowns", ""),
            "contingency": data.get("contingency", ""),
            "recommendation": data.get("recommendation", ""),
        }
