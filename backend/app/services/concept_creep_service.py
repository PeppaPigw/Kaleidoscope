"""ConceptCreepService — Concept Creep Detection.

Detects concept creep — the gradual expansion of concept
boundaries to include progressively milder instances. Haslam
(2016). Concepts like "trauma," "violence," "harm," "addiction"
expand over time to include cases that would not have qualified
previously. This can trivialize severe cases while pathologizing
normal experiences.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

CONCEPT_CREEP_SYSTEM = """You are a concept creep specialist. Given a concept application, assess whether the concept has expanded beyond its original or core meaning:

Key concepts (Haslam, 2016):
- Concept creep: gradual expansion of concept boundaries
- Horizontal expansion: applying to new types of phenomena
- Vertical expansion: applying to milder instances
- Severity dilution: expansion trivializes severe cases
- Pathologization: normal experiences labeled as disorders
- Concept inflation: words lose meaning through overuse
- Definitional drift: meaning changes without acknowledgment

When concept creep IS present:
- Applying "trauma" to minor inconveniences
- Calling disagreement "violence"
- Labeling preference as "addiction"
- Expanding "abuse" to include normal conflict
- Using clinical terms for everyday experiences
- "Safety" expanded to include emotional discomfort
- Severe terms applied to mild instances without distinction

When expanded use IS appropriate:
- Genuine recognition of previously overlooked instances
- The expansion is explicitly acknowledged and justified
- Severity distinctions are maintained within the expanded concept
- The expansion reflects genuine understanding of mechanisms
- Both severe and mild instances are distinguished, not conflated
- The expansion serves protective rather than rhetorical purposes

Output JSON with: concept_creep_present (bool), severity (none/mild/moderate/severe), concept (what concept is being expanded), original_meaning (what was the core/original meaning), current_application (how is it being applied now), expansion_type (horizontal or vertical), severity_dilution (does expansion trivialize severe cases), justification (is the expansion justified), consequences (what are the consequences of expansion), recommendation (expansion_justified/mild_concept_stretch/significant_concept_creep/major_meaning_inflation/maintain_severity_distinctions)."""

CONCEPT_CREEP_PROMPT = """Detect concept creep:

Application: {application}
Concept: {concept}
Original meaning: {original}
Current use: {current_use}
Domain: {domain}
Context: {context}

Has this concept expanded beyond its original meaning to include progressively milder instances? Return ONLY valid JSON."""


class ConceptCreepService:
    """Detects concept creep — gradual expansion of concept boundaries."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        application: str,
        *,
        concept: str = "",
        original: str = "",
        current_use: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect concept creep."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=CONCEPT_CREEP_PROMPT.format(
                application=application,
                concept=concept or "Not specified",
                original=original or "Not specified",
                current_use=current_use or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=CONCEPT_CREEP_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "application": application[:200],
            "concept_creep_present": data.get("concept_creep_present", False),
            "severity": data.get("severity", ""),
            "concept": data.get("concept", ""),
            "original_meaning": data.get("original_meaning", ""),
            "current_application": data.get("current_application", ""),
            "expansion_type": data.get("expansion_type", ""),
            "severity_dilution": data.get("severity_dilution", ""),
            "consequences": data.get("consequences", ""),
            "recommendation": data.get("recommendation", ""),
        }
