"""EpistemicCategoryPrototypeService — Epistemic Category Prototype Detection.

Detects epistemic category prototype bias — judging category membership
by similarity to prototype rather than by actual criteria.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_CATEGORY_PROTOTYPE_SYSTEM = """You are an epistemic category prototype specialist. Given prototype-based category judgments, assess category prototype bias:

Key concepts:
- Epistemic category prototype: judging membership by prototype similarity
- Typicality bias: judging atypical members as non-members
- Prototype fixation: fixating on prototypical examples
- Peripheral member exclusion: excluding peripheral but valid members
- Family resemblance blindness: missing family resemblance structure
- Exemplar dominance: letting salient exemplars dominate category
- Representativeness as membership: using representativeness as membership criterion

When epistemic category prototype IS present:
- Membership judged by prototype similarity
- Atypical members excluded
- Prototypes fixated on
- Peripheral members excluded
- Family resemblance missed
- Salient exemplars dominating
- Representativeness as criterion

When no category prototype bias:
- Membership judged by criteria
- Atypical members included
- Diversity of examples considered
- Peripheral members acknowledged
- Family resemblance recognized
- Exemplars balanced
- Criteria-based judgment

Output JSON with: category_prototype_detected (bool), severity (none/mild/moderate/severe), typicality_bias (what typicality bias), prototype_fixation (what prototype fixated), peripheral_exclusion (what peripheral members excluded), exemplar_dominance (what exemplars dominating), recommendation (no_category_prototype/mild_criteria_awareness/significant_diversity_inclusion/major_intensive_criteria_application/emergency_complete_category_prototype)."""

EPISTEMIC_CATEGORY_PROTOTYPE_PROMPT = """Detect epistemic category prototype bias:

Typicality bias: {typicality_bias}
Prototype fixation: {prototype_fixation}
Peripheral exclusion: {peripheral_exclusion}
Exemplar dominance: {exemplar_dominance}
Domain: {domain}
Context: {context}

Is category membership being judged by prototype similarity rather than criteria? Return ONLY valid JSON."""


class EpistemicCategoryPrototypeService:
    """Detects epistemic category prototype — similarity over criteria."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        typicality_bias: str,
        *,
        prototype_fixation: str = "",
        peripheral_exclusion: str = "",
        exemplar_dominance: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic category prototype bias."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_CATEGORY_PROTOTYPE_PROMPT.format(
                typicality_bias=typicality_bias,
                prototype_fixation=prototype_fixation or "Not specified",
                peripheral_exclusion=peripheral_exclusion or "Not specified",
                exemplar_dominance=exemplar_dominance or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_CATEGORY_PROTOTYPE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "typicality_bias": typicality_bias[:200],
            "category_prototype_detected": data.get("category_prototype_detected", False),
            "severity": data.get("severity", ""),
            "prototype_fixation": data.get("prototype_fixation", ""),
            "peripheral_exclusion": data.get("peripheral_exclusion", ""),
            "exemplar_dominance": data.get("exemplar_dominance", ""),
            "recommendation": data.get("recommendation", ""),
        }
