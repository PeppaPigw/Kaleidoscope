"""EpistemicLanguageNominalizationService - Epistemic Language Nominalization Detection.

Detects epistemic language nominalization - turning actions into nouns
in ways that hide agency, causation, and responsibility.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_LANGUAGE_NOMINALIZATION_SYSTEM = """You are an epistemic language nominalization specialist. Given nominalization hiding agency and causation, assess nominalization:

Key concepts:
- Epistemic language nominalization: turning actions into nouns that hide agency
- Agency concealment: obscuring who acted
- Process reification: treating processes as things
- Responsibility diffusion: spreading responsibility until no actor remains
- Action to thing: converting verbs into inert nouns
- Causation hiding: making causes harder to trace
- Actor deletion: removing agents from descriptions

When nominalization IS present:
- Agency concealed
- Processes reified
- Responsibility diffused
- Actions converted to things
- Causation hidden
- Actors deleted
- Events seem agentless

When no nominalization distortion:
- Actors named
- Processes described as actions
- Responsibility clear
- Verbs preserve agency
- Causation traceable
- Agents visible
- Events remain situated

Output JSON with: nominalization_detected (bool), severity (none/mild/moderate/severe), agency_concealment (what agency concealed), process_reification (what process reified), responsibility_diffusion (what responsibility diffused), action_to_thing (what action converted), recommendation (no_nominalization/mild_agency_clarification/significant_verb_restoration/major_intensive_actor_mapping/emergency_complete_nominalization)."""

EPISTEMIC_LANGUAGE_NOMINALIZATION_PROMPT = """Detect epistemic language nominalization:

Agency concealment: {agency_concealment}
Process reification: {process_reification}
Responsibility diffusion: {responsibility_diffusion}
Action to thing: {action_to_thing}
Domain: {domain}
Context: {context}

Is nominalization hiding agency and causation? Return ONLY valid JSON."""


class EpistemicLanguageNominalizationService:
    """Detects epistemic language nominalization - hiding agency through nouns."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        agency_concealment: str,
        *,
        process_reification: str = "",
        responsibility_diffusion: str = "",
        action_to_thing: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic language nominalization."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_LANGUAGE_NOMINALIZATION_PROMPT.format(
                agency_concealment=agency_concealment,
                process_reification=process_reification or "Not specified",
                responsibility_diffusion=responsibility_diffusion or "Not specified",
                action_to_thing=action_to_thing or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_LANGUAGE_NOMINALIZATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "agency_concealment": agency_concealment[:200],
            "nominalization_detected": data.get("nominalization_detected", False),
            "severity": data.get("severity", ""),
            "process_reification": data.get("process_reification", ""),
            "responsibility_diffusion": data.get("responsibility_diffusion", ""),
            "action_to_thing": data.get("action_to_thing", ""),
            "recommendation": data.get("recommendation", ""),
        }
