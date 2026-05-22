"""EpistemicNarrativeConstructionProtagonistBiasService - Epistemic Narrative Construction Protagonist Bias Detection.

Detects centering narratives on individual agents rather than systemic factors.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_NARRATIVE_CONSTRUCTION_PROTAGONIST_BIAS_SYSTEM = """You are an epistemic narrative construction protagonist bias specialist. Given agent-centered narratives, assess whether individual actors are being over-centered relative to systemic factors:

Key concepts:
- Epistemic protagonist bias: centering explanations on individual agents rather than systems
- Agent centering: making people the main causal drivers by narrative default
- Systemic factor neglect: underweighting institutions, incentives, constraints, and feedback loops
- Hero-villain framing: explaining outcomes through morally legible characters
- Intentionality attribution: treating diffuse outcomes as deliberate actions by agents

When protagonist bias IS present:
- Individual actors dominate the explanation
- Systemic factors are minimized or ignored
- Heroes or villains carry too much causal weight
- Outcomes are attributed to intention without evidence
- Structural dynamics are converted into character stories

When no protagonist bias:
- Agency and structure are separated
- Systemic factors are explicitly considered
- Moral framing does not replace causal analysis
- Intentions are attributed only with evidence
- Institutional and incentive dynamics are preserved

Output JSON with: protagonist_bias_detected (bool), severity (none/mild/moderate/severe), systemic_factor_neglect (what systemic factors are neglected), hero_villain_framing (what hero or villain framing appears), intentionality_attribution (what intention is over-attributed), recommendation (no_protagonist_bias/mild_systemic_context/significant_structural_analysis/major_agent_structure_rebalance/emergency_complete_systemic_reconstruction)."""

EPISTEMIC_NARRATIVE_CONSTRUCTION_PROTAGONIST_BIAS_PROMPT = """Detect epistemic narrative construction protagonist bias:

Agent centering: {agent_centering}
Systemic factor neglect: {systemic_factor_neglect}
Hero-villain framing: {hero_villain_framing}
Intentionality attribution: {intentionality_attribution}
Domain: {domain}
Context: {context}

Is the narrative centered on individual agents rather than systemic factors? Return ONLY valid JSON."""


class EpistemicNarrativeConstructionProtagonistBiasService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        agent_centering: str,
        *,
        systemic_factor_neglect: str = "",
        hero_villain_framing: str = "",
        intentionality_attribution: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_NARRATIVE_CONSTRUCTION_PROTAGONIST_BIAS_PROMPT.format(
                agent_centering=agent_centering,
                systemic_factor_neglect=systemic_factor_neglect or "Not specified",
                hero_villain_framing=hero_villain_framing or "Not specified",
                intentionality_attribution=intentionality_attribution or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_NARRATIVE_CONSTRUCTION_PROTAGONIST_BIAS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "agent_centering": agent_centering[:200],
            "protagonist_bias_detected": data.get("protagonist_bias_detected", False),
            "severity": data.get("severity", ""),
            "systemic_factor_neglect": data.get("systemic_factor_neglect", ""),
            "hero_villain_framing": data.get("hero_villain_framing", ""),
            "intentionality_attribution": data.get("intentionality_attribution", ""),
            "recommendation": data.get("recommendation", ""),
        }
