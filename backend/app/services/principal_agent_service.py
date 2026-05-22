"""PrincipalAgentService — Principal-Agent Problem Detection.

Identifies when an agent (someone acting on behalf of another) has
incentives misaligned with their principal. Lawyers billing by hour,
fund managers taking fees regardless of performance, politicians
serving donors over constituents — the agent's interests diverge
from those they're supposed to serve.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

PRINCIPAL_AGENT_SYSTEM = """You are a principal-agent problem specialist. Given a relationship or arrangement, assess whether principal-agent misalignment exists:
- Does the agent have different incentives than the principal?
- Can the agent's actions be fully observed by the principal?
- Is the agent's compensation aligned with the principal's outcomes?
- Are there mechanisms to detect or prevent shirking/self-dealing?
- Would the agent behave differently if perfectly monitored?

Output JSON with: misalignment_present (bool), severity (none/mild/moderate/severe/critical), principal (who is being served), agent (who is acting on their behalf), principal_goal (what the principal actually wants), agent_incentive (what the agent is actually optimized for), divergence_point (where interests split), observability (0-1 — how well can the principal monitor the agent?), information_asymmetry (what the agent knows that the principal doesn't), shirking_risk (0-1 — risk of agent doing less than agreed), self_dealing_risk (0-1 — risk of agent serving themselves at principal's expense), alignment_mechanisms (existing mechanisms to align interests), missing_mechanisms (mechanisms that should exist but don't), compensation_structure_flaw (how pay structure creates misalignment), who_bears_risk (who suffers when things go wrong), who_captures_upside (who benefits when things go right), recommendation (aligned/add_monitoring/restructure_incentives/replace_agent/accept_risk)."""

PRINCIPAL_AGENT_PROMPT = """Detect principal-agent problems:

Relationship/Arrangement: {arrangement}
Principal: {principal}
Agent: {agent}
Compensation structure: {compensation}
Domain: {domain}
Context: {context}

Is there a principal-agent problem? Return ONLY valid JSON."""


class PrincipalAgentService:
    """Detects principal-agent misalignment."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        arrangement: str,
        *,
        principal: str = "",
        agent: str = "",
        compensation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect principal-agent problems."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=PRINCIPAL_AGENT_PROMPT.format(
                arrangement=arrangement,
                principal=principal or "Not specified",
                agent=agent or "Not specified",
                compensation=compensation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=PRINCIPAL_AGENT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "arrangement": arrangement[:200],
            "misalignment_present": data.get("misalignment_present", False),
            "severity": data.get("severity", ""),
            "principal": data.get("principal", ""),
            "agent": data.get("agent", ""),
            "principal_goal": data.get("principal_goal", ""),
            "agent_incentive": data.get("agent_incentive", ""),
            "divergence_point": data.get("divergence_point", ""),
            "observability": data.get("observability", 0),
            "information_asymmetry": data.get("information_asymmetry", ""),
            "shirking_risk": data.get("shirking_risk", 0),
            "self_dealing_risk": data.get("self_dealing_risk", 0),
            "alignment_mechanisms": data.get("alignment_mechanisms", ""),
            "missing_mechanisms": data.get("missing_mechanisms", ""),
            "compensation_structure_flaw": data.get("compensation_structure_flaw", ""),
            "who_bears_risk": data.get("who_bears_risk", ""),
            "who_captures_upside": data.get("who_captures_upside", ""),
            "recommendation": data.get("recommendation", ""),
        }
