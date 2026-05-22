"""MoralHazardService — Moral Hazard & Perverse Incentive Detection.

Identifies when a system's incentive structure encourages risk-taking
because the costs of failure are borne by someone else. Detects
principal-agent problems, externalized risk, and perverse incentives.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

MORAL_HAZARD_SYSTEM = """You are a moral hazard specialist. Given a system or arrangement, assess whether moral hazard is present:
- Who bears the risk vs who makes the decisions?
- Are costs externalized (borne by someone other than the risk-taker)?
- Does insurance/protection encourage riskier behavior?
- Is there a principal-agent problem (misaligned interests)?
- What perverse incentives does the structure create?

Output JSON with: moral_hazard_present (bool), severity (none/mild/moderate/severe/systemic), risk_taker (who makes risky decisions), risk_bearer (who suffers if things go wrong), separation_of_risk_and_reward (0-1, how separated they are), perverse_incentives (list of: incentive, behavior_it_encourages, who_benefits, who_loses), principal_agent_problem (bool), information_asymmetry (what the risk-taker knows that the risk-bearer doesn't), historical_examples (similar moral hazard situations and their outcomes), mitigation_strategies (list of: strategy, effectiveness, tradeoff), monitoring_difficulty (easy/moderate/hard/impossible — how hard to detect the risky behavior), systemic_risk (bool — could this moral hazard cause system-wide failure?), recommendation (acceptable/needs_monitoring/needs_restructuring/dangerous)."""

MORAL_HAZARD_PROMPT = """Detect moral hazard:

System/Arrangement: {system}
Key actors: {actors}
Risk structure: {risk_structure}
Domain: {domain}
Context: {context}

Is there moral hazard? Return ONLY valid JSON."""


class MoralHazardService:
    """Detects moral hazard and perverse incentives."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        system: str,
        *,
        actors: str = "",
        risk_structure: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect moral hazard."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=MORAL_HAZARD_PROMPT.format(
                system=system,
                actors=actors or "Not specified",
                risk_structure=risk_structure or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=MORAL_HAZARD_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "system": system[:200],
            "moral_hazard_present": data.get("moral_hazard_present", False),
            "severity": data.get("severity", ""),
            "risk_taker": data.get("risk_taker", ""),
            "risk_bearer": data.get("risk_bearer", ""),
            "separation_of_risk_and_reward": data.get("separation_of_risk_and_reward", 0),
            "perverse_incentives": data.get("perverse_incentives", []),
            "principal_agent_problem": data.get("principal_agent_problem", False),
            "information_asymmetry": data.get("information_asymmetry", ""),
            "historical_examples": data.get("historical_examples", []),
            "mitigation_strategies": data.get("mitigation_strategies", []),
            "monitoring_difficulty": data.get("monitoring_difficulty", ""),
            "systemic_risk": data.get("systemic_risk", False),
            "recommendation": data.get("recommendation", ""),
        }
