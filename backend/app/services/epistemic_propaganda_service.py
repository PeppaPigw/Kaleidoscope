"""EpistemicPropagandaService — Epistemic Propaganda Detection.

Detects epistemic propaganda — systematic manipulation of belief
formation through controlled information environments.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PROPAGANDA_SYSTEM = """You are an epistemic propaganda specialist. Given an information environment, assess whether systematic manipulation of belief formation occurs:

Key concepts:
- Epistemic propaganda: systematic manipulation of belief formation
- Controlled environment: controlling information environment
- Narrative control: controlling dominant narratives
- Repetition effect: using repetition to create belief
- Emotional manipulation: manipulating emotions to shape beliefs
- Source control: controlling what sources are available
- Reality construction: constructing alternative reality

When epistemic propaganda IS present:
- Systematic manipulation of belief formation
- Information environment deliberately controlled
- Dominant narratives controlled and managed
- Repetition used to create beliefs without evidence
- Emotions manipulated to shape beliefs
- Available sources controlled and curated
- Alternative reality constructed through information control

When free information is present:
- Belief formation based on free information access
- Information environment open and diverse
- Multiple narratives available and competing
- Beliefs formed through evidence not repetition
- Emotions engaged honestly not manipulatively
- Diverse sources freely available
- Reality based on evidence not construction

Output JSON with: propaganda_present (bool), severity (none/mild/moderate/severe), system (what system propagandizes), method (what methods are used), control (what is controlled), manipulation (what manipulation occurs), recommendation (free_information/mild_bias/significant_propaganda/major_systematic_manipulation/restore_information_freedom)."""

EPISTEMIC_PROPAGANDA_PROMPT = """Detect epistemic propaganda:

System: {system}
Method: {method}
Control: {control}
Manipulation: {manipulation}
Domain: {domain}
Context: {context}

Is systematic manipulation of belief formation occurring through controlled information? Return ONLY valid JSON."""


class EpistemicPropagandaService:
    """Detects epistemic propaganda — systematic manipulation of belief formation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        system: str,
        *,
        method: str = "",
        control: str = "",
        manipulation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic propaganda."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PROPAGANDA_PROMPT.format(
                system=system,
                method=method or "Not specified",
                control=control or "Not specified",
                manipulation=manipulation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PROPAGANDA_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "system": system[:200],
            "propaganda_present": data.get("propaganda_present", False),
            "severity": data.get("severity", ""),
            "method": data.get("method", ""),
            "control": data.get("control", ""),
            "manipulation": data.get("manipulation", ""),
            "recommendation": data.get("recommendation", ""),
        }
