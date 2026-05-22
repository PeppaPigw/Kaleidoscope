"""EpistemicSwarmIntelligenceService — Epistemic Swarm Intelligence Detection.

Detects epistemic swarm intelligence — collective intellectual behavior
emerging from many simple agents following simple rules.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SWARM_INTELLIGENCE_SYSTEM = """You are an epistemic swarm intelligence specialist. Given a collective thinking pattern, assess whether emergent intelligence arises from simple agents:

Key concepts:
- Epistemic swarm intelligence: collective intelligence from simple agents
- Emergence: complex behavior from simple individual rules
- Stigmergy: indirect coordination through environmental modification
- Pheromone trail: intellectual signals left for others to follow
- Colony optimization: collective finding optimal solutions
- Decentralized control: no central authority directing the swarm
- Self-organization: order emerging without external direction

When epistemic swarm intelligence IS present:
- Complex collective behavior emerging from simple individual actions
- Many simple agents following simple rules producing intelligence
- Indirect coordination through shared intellectual environment
- Intellectual signals left for others to follow and amplify
- Collective finding solutions no individual could find alone
- No central authority directing the collective behavior
- Order emerging spontaneously from interactions

When individual intelligence is present:
- Complex behavior from individual sophisticated reasoning
- Single agents using complex rules and strategies
- Direct coordination through explicit communication
- Deliberate signaling between specific individuals
- Solutions found through individual insight
- Central authority or hierarchy directing behavior
- Order imposed from above

Output JSON with: swarm_present (bool), severity (none/mild/moderate/severe), agents (what simple agents participate), rules (what simple rules they follow), emergence (what complex behavior emerges), stigmergy (what environmental signals coordinate), recommendation (individual_intelligence/mild_emergence/significant_swarm/major_collective_intelligence/harness_swarm_dynamics)."""

EPISTEMIC_SWARM_INTELLIGENCE_PROMPT = """Detect epistemic swarm intelligence:

Agents: {agents}
Rules: {rules}
Emergence: {emergence}
Stigmergy: {stigmergy}
Domain: {domain}
Context: {context}

Is collective intelligence emerging from many simple agents following simple rules? Return ONLY valid JSON."""


class EpistemicSwarmIntelligenceService:
    """Detects epistemic swarm intelligence — emergent collective behavior."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        agents: str,
        *,
        rules: str = "",
        emergence: str = "",
        stigmergy: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic swarm intelligence."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SWARM_INTELLIGENCE_PROMPT.format(
                agents=agents,
                rules=rules or "Not specified",
                emergence=emergence or "Not specified",
                stigmergy=stigmergy or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SWARM_INTELLIGENCE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "agents": agents[:200],
            "swarm_present": data.get("swarm_present", False),
            "severity": data.get("severity", ""),
            "rules": data.get("rules", ""),
            "emergence": data.get("emergence", ""),
            "stigmergy": data.get("stigmergy", ""),
            "recommendation": data.get("recommendation", ""),
        }
