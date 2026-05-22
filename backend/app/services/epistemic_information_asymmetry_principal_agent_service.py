"""EpistemicInformationAsymmetryPrincipalAgentService — Epistemic Information Asymmetry Principal-Agent Detection.

Detects principal-agent problems in knowledge delegation.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_INFORMATION_ASYMMETRY_PRINCIPAL_AGENT_SYSTEM = """You are an epistemic information asymmetry principal-agent specialist. Given delegation distortion, assess principal-agent problems in knowledge delegation:

Key concepts:
- Epistemic principal-agent problem: delegated knowledge work drifts from the principal's truth-seeking goals
- Delegation distortion: errors or bias introduced when inquiry, evaluation, or explanation is delegated
- Agent self-interest: incentives for the agent to optimize status, convenience, reward, or persuasion
- Information withholding: selective non-disclosure by the agent about uncertainty, methods, failures, or limits
- Goal divergence: mismatch between the principal's epistemic goals and the agent's operational goals

When principal-agent problems ARE present:
- Delegation changes epistemic incentives
- Agent interests diverge from truth-seeking
- Critical information is withheld or filtered
- Principal cannot adequately evaluate agent work
- Knowledge outcomes reflect agent goals more than principal goals

When no principal-agent problem:
- Delegated goals are aligned and auditable
- Agent incentives support truth-seeking
- Information is disclosed transparently
- Principal can evaluate quality and limits

Output JSON with: principal_agent_problem_detected (bool), severity (none/mild/moderate/severe), agent_self_interest (what agent incentives distort), information_withholding (what information is withheld), goal_divergence (what goals diverge), recommendation (no_principal_agent_problem/mild_alignment_check/significant_transparency_improvement/major_delegation_redesign/emergency_agent_control_failure)."""

EPISTEMIC_INFORMATION_ASYMMETRY_PRINCIPAL_AGENT_PROMPT = """Detect epistemic information asymmetry principal-agent problems:

Delegation distortion: {delegation_distortion}
Agent self-interest: {agent_self_interest}
Information withholding: {information_withholding}
Goal divergence: {goal_divergence}
Domain: {domain}
Context: {context}

Are principal-agent problems distorting knowledge delegation? Return ONLY valid JSON."""


class EpistemicInformationAsymmetryPrincipalAgentService:
    """Detects epistemic information asymmetry principal-agent problems."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        delegation_distortion: str,
        *,
        agent_self_interest: str = "",
        information_withholding: str = "",
        goal_divergence: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic information asymmetry principal-agent problems."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_INFORMATION_ASYMMETRY_PRINCIPAL_AGENT_PROMPT.format(
                delegation_distortion=delegation_distortion,
                agent_self_interest=agent_self_interest or "Not specified",
                information_withholding=information_withholding or "Not specified",
                goal_divergence=goal_divergence or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_INFORMATION_ASYMMETRY_PRINCIPAL_AGENT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "delegation_distortion": delegation_distortion[:200],
            "principal_agent_problem_detected": data.get("principal_agent_problem_detected", False),
            "severity": data.get("severity", ""),
            "agent_self_interest": data.get("agent_self_interest", ""),
            "information_withholding": data.get("information_withholding", ""),
            "goal_divergence": data.get("goal_divergence", ""),
            "recommendation": data.get("recommendation", ""),
        }
