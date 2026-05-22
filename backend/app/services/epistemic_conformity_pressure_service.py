"""EpistemicConformityPressureService — Epistemic Conformity Pressure Detection.

Detects epistemic conformity pressure — social pressure to believe
what the group believes regardless of evidence, where dissent is
punished and conformity rewarded.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_CONFORMITY_PRESSURE_SYSTEM = """You are an epistemic conformity pressure specialist. Given a group knowledge situation, assess whether conformity pressure is distorting beliefs:

Key concepts:
- Epistemic conformity pressure: social pressure to believe with group
- Belief coercion: punishment for dissenting beliefs
- Conformity reward: benefits for agreeing with group
- Social epistemology distortion: social pressure overriding evidence
- Dissent punishment: costs of disagreeing
- Orthodoxy enforcement: maintaining approved beliefs
- Epistemic peer pressure: pressure to match group beliefs

When epistemic conformity pressure IS present:
- Social pressure to adopt group beliefs
- Dissent punished socially or professionally
- Conformity rewarded regardless of evidence
- Evidence-based disagreement treated as disloyalty
- Orthodoxy enforced through social mechanisms
- Peer pressure overrides individual judgment
- Belief conformity required for membership

When shared understanding is appropriate:
- Agreement based on shared evidence
- Dissent welcomed and engaged with
- Conformity earned through persuasion
- Disagreement treated as contribution
- Standards based on evidence not loyalty
- Individual judgment respected
- Consensus genuine not coerced

Output JSON with: pressure_present (bool), severity (none/mild/moderate/severe), group (what group), mechanism (how pressure operates), dissent_cost (what dissent costs), conformity_reward (what conformity gains), recommendation (appropriate_shared_understanding/mild_social_influence/significant_conformity_pressure/major_belief_coercion/protect_epistemic_dissent)."""

EPISTEMIC_CONFORMITY_PRESSURE_PROMPT = """Detect epistemic conformity pressure:

Group: {group}
Belief at issue: {belief}
Dissent treatment: {dissent}
Conformity incentives: {incentives}
Domain: {domain}
Context: {context}

Is social pressure forcing belief conformity regardless of evidence? Return ONLY valid JSON."""


class EpistemicConformityPressureService:
    """Detects epistemic conformity pressure — social pressure overriding evidence."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        group: str,
        *,
        belief: str = "",
        dissent: str = "",
        incentives: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic conformity pressure."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_CONFORMITY_PRESSURE_PROMPT.format(
                group=group,
                belief=belief or "Not specified",
                dissent=dissent or "Not specified",
                incentives=incentives or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_CONFORMITY_PRESSURE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "group": group[:200],
            "pressure_present": data.get("pressure_present", False),
            "severity": data.get("severity", ""),
            "mechanism": data.get("mechanism", ""),
            "dissent_cost": data.get("dissent_cost", ""),
            "conformity_reward": data.get("conformity_reward", ""),
            "recommendation": data.get("recommendation", ""),
        }
