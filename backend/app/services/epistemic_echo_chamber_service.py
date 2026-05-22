"""EpistemicEchoChamberService — Epistemic Echo Chamber Detection.

Detects epistemic echo chambers — closed loops that amplify beliefs
without external input or correction.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ECHO_CHAMBER_SYSTEM = """You are an epistemic echo chamber specialist. Given a belief environment, assess whether closed amplification loops exist:

Key concepts:
- Epistemic echo chamber: closed loop amplifying without external input
- Belief amplification: beliefs amplified through repetition
- Closed information loop: information circulating without external check
- Self-reinforcing bubble: bubble that reinforces its own beliefs
- External input exclusion: excluding disconfirming external information
- Amplification without correction: amplifying without error correction
- Homogeneous information diet: consuming only confirming information

When epistemic echo chamber IS present:
- Closed loop amplifying beliefs without external input
- Beliefs amplified through repetition not evidence
- Information circulating without external verification
- Self-reinforcing bubble excluding disconfirmation
- External input systematically excluded
- Amplification occurring without error correction
- Information diet homogeneous and confirming

When healthy discourse is present:
- Open to external input and correction
- Beliefs tested against diverse perspectives
- Information verified through external sources
- Disconfirming evidence considered
- External input welcomed and integrated
- Error correction mechanisms functioning
- Information diet diverse and challenging

Output JSON with: echo_chamber_present (bool), severity (none/mild/moderate/severe), environment (what environment is analyzed), amplification (what is amplified), exclusion (what is excluded), closed_loop (how the loop closes), recommendation (healthy_discourse/mild_homogeneity/significant_echo_chamber/major_closed_loop/open_to_external_input)."""

EPISTEMIC_ECHO_CHAMBER_PROMPT = """Detect epistemic echo chamber:

Environment: {environment}
Amplification: {amplification}
External input: {external}
Diversity: {diversity}
Domain: {domain}
Context: {context}

Is a closed loop amplifying beliefs without external input? Return ONLY valid JSON."""


class EpistemicEchoChamberService:
    """Detects epistemic echo chambers — closed amplification loops."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        environment: str,
        *,
        amplification: str = "",
        external: str = "",
        diversity: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic echo chamber."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ECHO_CHAMBER_PROMPT.format(
                environment=environment,
                amplification=amplification or "Not specified",
                external=external or "Not specified",
                diversity=diversity or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ECHO_CHAMBER_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "environment": environment[:200],
            "echo_chamber_present": data.get("echo_chamber_present", False),
            "severity": data.get("severity", ""),
            "amplification": data.get("amplification", ""),
            "exclusion": data.get("exclusion", ""),
            "closed_loop": data.get("closed_loop", ""),
            "recommendation": data.get("recommendation", ""),
        }
