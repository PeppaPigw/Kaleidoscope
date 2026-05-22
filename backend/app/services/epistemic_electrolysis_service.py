"""EpistemicElectrolysisService — Epistemic Electrolysis Detection.

Detects epistemic electrolysis — applying external intellectual energy
to force ideas apart that would naturally stay bonded.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ELECTROLYSIS_SYSTEM = """You are an epistemic electrolysis specialist. Given an idea separation pattern, assess whether external energy forces naturally bonded ideas apart:

Key concepts:
- Epistemic electrolysis: external energy forcing bonded ideas apart
- Applied voltage: external intellectual force driving separation
- Electrode: point where separation occurs
- Decomposition: breaking compound ideas into elements
- Overpotential: extra energy needed beyond theoretical minimum
- Faraday's law: relationship between energy and separation amount
- Electrolyte: medium that allows ion movement

When epistemic electrolysis IS present:
- External energy forcing naturally bonded ideas apart
- External intellectual force driving the separation
- Specific points where separation occurs
- Compound ideas being broken into simpler elements
- Extra energy needed beyond what theory predicts
- Proportional relationship between energy and separation
- Medium allowing the separated components to move

When natural bonding is present:
- Ideas remaining in their natural bonded state
- No external force driving separation
- No specific separation points
- Compound ideas remaining intact
- No extra energy being applied
- No forced separation occurring
- No medium for separated movement

Output JSON with: electrolysis_present (bool), severity (none/mild/moderate/severe), voltage (what external force), electrode (where separation occurs), decomposition (what is broken apart), overpotential (what extra energy needed), recommendation (natural_bonding/mild_electrolysis/significant_electrolysis/major_forced_separation/reduce_applied_voltage)."""

EPISTEMIC_ELECTROLYSIS_PROMPT = """Detect epistemic electrolysis:

Voltage: {voltage}
Electrode: {electrode}
Decomposition: {decomposition}
Overpotential: {overpotential}
Domain: {domain}
Context: {context}

Is external intellectual energy being applied to force ideas apart that would naturally stay bonded? Return ONLY valid JSON."""


class EpistemicElectrolysisService:
    """Detects epistemic electrolysis — external energy forcing separation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        voltage: str,
        *,
        electrode: str = "",
        decomposition: str = "",
        overpotential: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic electrolysis."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ELECTROLYSIS_PROMPT.format(
                voltage=voltage,
                electrode=electrode or "Not specified",
                decomposition=decomposition or "Not specified",
                overpotential=overpotential or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ELECTROLYSIS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "voltage": voltage[:200],
            "electrolysis_present": data.get("electrolysis_present", False),
            "severity": data.get("severity", ""),
            "electrode": data.get("electrode", ""),
            "decomposition": data.get("decomposition", ""),
            "overpotential": data.get("overpotential", ""),
            "recommendation": data.get("recommendation", ""),
        }
