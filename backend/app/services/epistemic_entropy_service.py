"""EpistemicEntropyService — Epistemic Entropy Detection.

Detects epistemic entropy — knowledge systems trending toward
disorder and incoherence over time.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ENTROPY_SYSTEM = """You are an epistemic entropy specialist. Given a knowledge system, assess whether it is trending toward disorder and incoherence:

Key concepts:
- Epistemic entropy: knowledge trending toward disorder
- Coherence decay: loss of coherence over time
- Framework fragmentation: unified frameworks breaking apart
- Meaning dissipation: meaning becoming diluted or lost
- Conceptual drift: concepts drifting from original definitions
- Knowledge degradation: quality of knowledge declining
- Organizational decay: organizational structure of knowledge failing

When epistemic entropy IS present:
- Knowledge system trending toward disorder
- Coherence decaying over time
- Unified frameworks fragmenting
- Meaning becoming diluted or lost
- Concepts drifting from clear definitions
- Quality of knowledge declining
- Organizational structure failing

When healthy evolution is present:
- Knowledge evolving while maintaining coherence
- Changes improving rather than degrading understanding
- Frameworks adapting while staying unified
- Meaning deepening over time
- Concepts refined rather than degraded
- Quality maintained or improved
- Organization adapting to new knowledge

Output JSON with: entropy_present (bool), severity (none/mild/moderate/severe), system (what knowledge system), disorder (what disorder manifests), decay (how coherence decays), trajectory (where system is heading), recommendation (healthy_evolution/mild_drift/significant_entropy/major_incoherence/restore_coherence)."""

EPISTEMIC_ENTROPY_PROMPT = """Detect epistemic entropy:

System: {system}
Disorder: {disorder}
Decay: {decay}
Trajectory: {trajectory}
Domain: {domain}
Context: {context}

Is the knowledge system trending toward disorder and incoherence? Return ONLY valid JSON."""


class EpistemicEntropyService:
    """Detects epistemic entropy — knowledge trending toward disorder."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        system: str,
        *,
        disorder: str = "",
        decay: str = "",
        trajectory: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic entropy."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ENTROPY_PROMPT.format(
                system=system,
                disorder=disorder or "Not specified",
                decay=decay or "Not specified",
                trajectory=trajectory or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ENTROPY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "system": system[:200],
            "entropy_present": data.get("entropy_present", False),
            "severity": data.get("severity", ""),
            "disorder": data.get("disorder", ""),
            "decay": data.get("decay", ""),
            "trajectory": data.get("trajectory", ""),
            "recommendation": data.get("recommendation", ""),
        }
