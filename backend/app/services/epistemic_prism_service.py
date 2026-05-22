"""EpistemicPrismService — Epistemic Prism Detection.

Detects epistemic prism effects — knowledge split into components
that lose their holistic meaning when separated.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PRISM_SYSTEM = """You are an epistemic prism specialist. Given a knowledge decomposition pattern, assess whether splitting destroys holistic meaning:

Key concepts:
- Epistemic prism: splitting knowledge into components that lose holistic meaning
- Decomposition loss: meaning lost when knowledge is split apart
- Component isolation: isolated components losing context
- Holistic destruction: destroying the whole by separating parts
- Spectrum without synthesis: seeing parts but not the whole
- Reductive splitting: reducing complex knowledge to isolated components
- Integration loss: losing the integration that gave meaning

When epistemic prism IS present:
- Knowledge split into components losing holistic meaning
- Meaning lost when knowledge is decomposed
- Isolated components losing their context
- The whole destroyed by separating into parts
- Seeing individual parts but not the integrated whole
- Complex knowledge reduced to isolated components
- Integration that gave meaning is lost

When holistic preservation is present:
- Knowledge components maintaining holistic meaning
- Meaning preserved even when examining parts
- Components retaining their context
- The whole maintained while examining parts
- Both parts and integrated whole visible
- Complex knowledge examined without losing integration
- Integration preserved throughout analysis

Output JSON with: prism_present (bool), severity (none/mild/moderate/severe), knowledge (what knowledge is split), components (what components result), holistic_loss (what holistic meaning is lost), splitting (how splitting occurs), recommendation (holistic_preservation/mild_decomposition/significant_prism_effect/major_holistic_loss/reintegrate_components)."""

EPISTEMIC_PRISM_PROMPT = """Detect epistemic prism effect:

Knowledge: {knowledge}
Components: {components}
Holistic loss: {holistic_loss}
Splitting: {splitting}
Domain: {domain}
Context: {context}

Is knowledge being split into components that lose their holistic meaning? Return ONLY valid JSON."""


class EpistemicPrismService:
    """Detects epistemic prism — knowledge split losing holistic meaning."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        knowledge: str,
        *,
        components: str = "",
        holistic_loss: str = "",
        splitting: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic prism effect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PRISM_PROMPT.format(
                knowledge=knowledge,
                components=components or "Not specified",
                holistic_loss=holistic_loss or "Not specified",
                splitting=splitting or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PRISM_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "knowledge": knowledge[:200],
            "prism_present": data.get("prism_present", False),
            "severity": data.get("severity", ""),
            "components": data.get("components", ""),
            "holistic_loss": data.get("holistic_loss", ""),
            "splitting": data.get("splitting", ""),
            "recommendation": data.get("recommendation", ""),
        }
