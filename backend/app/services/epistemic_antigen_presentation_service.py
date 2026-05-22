"""EpistemicAntigenPresentationService — Epistemic Antigen Presentation Detection.

Detects epistemic antigen presentation — ideas being displayed for evaluation
by the intellectual immune system to determine friend or foe.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ANTIGEN_PRESENTATION_SYSTEM = """You are an epistemic antigen presentation specialist. Given an intellectual evaluation, assess whether ideas are displayed for immune judgment:

Key concepts:
- Epistemic antigen presentation: ideas displayed for immune evaluation
- MHC complex: framework for displaying idea fragments
- Dendritic cell: professional presenter of ideas
- T-cell activation: immune response triggered by presentation
- Cross-presentation: presenting external ideas on self-framework
- Costimulation: additional signal needed for full activation
- Anergy: failure to respond despite presentation

When epistemic antigen presentation IS present:
- Ideas being displayed for evaluation
- Framework for presenting idea fragments
- Professional presenters of ideas to evaluators
- Immune response triggered by the presentation
- External ideas presented on internal framework
- Additional signals needed for full response
- Possible failure to respond despite presentation

When no presentation is present:
- Ideas not displayed for evaluation
- No presentation framework
- No professional presenters
- No triggered immune response
- No cross-presentation
- No costimulation needed
- No anergy possible

Output JSON with: antigen_presentation_present (bool), severity (none/mild/moderate/severe), mhc_complex (what display framework), dendritic_cell (what professional presenter), t_cell_activation (what triggered response), anergy (what response failure), recommendation (no_presentation/mild_presentation/significant_antigen_presentation/major_immune_display/improve_presentation_accuracy)."""

EPISTEMIC_ANTIGEN_PRESENTATION_PROMPT = """Detect epistemic antigen presentation:

MHC complex: {mhc_complex}
Dendritic cell: {dendritic_cell}
T-cell activation: {t_cell_activation}
Anergy: {anergy}
Domain: {domain}
Context: {context}

Are ideas being displayed for evaluation by the intellectual immune system to determine friend or foe? Return ONLY valid JSON."""


class EpistemicAntigenPresentationService:
    """Detects epistemic antigen presentation — ideas displayed for immune evaluation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        mhc_complex: str,
        *,
        dendritic_cell: str = "",
        t_cell_activation: str = "",
        anergy: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic antigen presentation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ANTIGEN_PRESENTATION_PROMPT.format(
                mhc_complex=mhc_complex,
                dendritic_cell=dendritic_cell or "Not specified",
                t_cell_activation=t_cell_activation or "Not specified",
                anergy=anergy or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ANTIGEN_PRESENTATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "mhc_complex": mhc_complex[:200],
            "antigen_presentation_present": data.get("antigen_presentation_present", False),
            "severity": data.get("severity", ""),
            "dendritic_cell": data.get("dendritic_cell", ""),
            "t_cell_activation": data.get("t_cell_activation", ""),
            "anergy": data.get("anergy", ""),
            "recommendation": data.get("recommendation", ""),
        }
