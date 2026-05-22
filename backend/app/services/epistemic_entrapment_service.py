"""EpistemicEntrapmentService — Epistemic Entrapment Detection.

Detects epistemic entrapment — trapping someone in unfalsifiable
belief systems where no evidence could possibly change their mind.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ENTRAPMENT_SYSTEM = """You are an epistemic entrapment specialist. Given a belief system, assess whether it traps adherents in unfalsifiable positions:

Key concepts:
- Epistemic entrapment: trapping in unfalsifiable belief systems
- Unfalsifiable framing: framing beliefs so nothing could disprove them
- Exit cost inflation: making belief exit prohibitively costly
- Doubt as confirmation: interpreting doubt as confirming the belief
- Evidence immunity: belief immune to any possible evidence
- Circular justification: belief justified only by itself
- Epistemic isolation: cutting off from disconfirming information

When epistemic entrapment IS present:
- Belief system unfalsifiable by design
- No possible evidence could change the belief
- Doubt reinterpreted as confirmation
- Exit from belief system made prohibitively costly
- Circular justification preventing escape
- Disconfirming information systematically excluded
- Belief immune to revision by construction

When robust belief is present:
- Belief well-supported but revisable
- Evidence could in principle change the belief
- Doubt taken seriously and addressed
- Belief held with appropriate confidence
- Justification grounded in evidence
- Disconfirming information considered
- Belief updated when evidence warrants

Output JSON with: entrapment_present (bool), severity (none/mild/moderate/severe), belief_system (what belief system is involved), trap_mechanism (how entrapment works), unfalsifiability (how belief is made unfalsifiable), exit_cost (what makes exit costly), recommendation (robust_belief/mild_rigidity/significant_epistemic_entrapment/major_unfalsifiable_trap/maintain_revisability)."""

EPISTEMIC_ENTRAPMENT_PROMPT = """Detect epistemic entrapment:

Belief system: {belief_system}
Trap mechanism: {mechanism}
Unfalsifiability: {unfalsifiability}
Exit costs: {exit_costs}
Domain: {domain}
Context: {context}

Is someone trapped in an unfalsifiable belief system? Return ONLY valid JSON."""


class EpistemicEntrapmentService:
    """Detects epistemic entrapment — trapping in unfalsifiable belief systems."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        belief_system: str,
        *,
        mechanism: str = "",
        unfalsifiability: str = "",
        exit_costs: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic entrapment."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ENTRAPMENT_PROMPT.format(
                belief_system=belief_system,
                mechanism=mechanism or "Not specified",
                unfalsifiability=unfalsifiability or "Not specified",
                exit_costs=exit_costs or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ENTRAPMENT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "belief_system": belief_system[:200],
            "entrapment_present": data.get("entrapment_present", False),
            "severity": data.get("severity", ""),
            "trap_mechanism": data.get("trap_mechanism", ""),
            "unfalsifiability": data.get("unfalsifiability", ""),
            "exit_cost": data.get("exit_cost", ""),
            "recommendation": data.get("recommendation", ""),
        }
