"""EpistemicContagionService — Epistemic Contagion Detection.

Detects epistemic contagion — harmful beliefs spreading through
social contact without critical evaluation.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_CONTAGION_SYSTEM = """You are an epistemic contagion specialist. Given a belief spread pattern, assess whether harmful beliefs spread through social contact without evaluation:

Key concepts:
- Epistemic contagion: harmful beliefs spreading through social contact
- Uncritical adoption: adopting beliefs without evaluation
- Social transmission: beliefs spreading via social mechanisms
- Emotional contagion: beliefs spreading via emotional resonance
- Authority contagion: beliefs spreading via authority proximity
- Proximity effect: beliefs adopted due to social proximity
- Viral spread: beliefs spreading rapidly without scrutiny

When epistemic contagion IS present:
- Harmful beliefs spreading through social contact
- Beliefs adopted without critical evaluation
- Social mechanisms driving belief adoption
- Emotional resonance spreading beliefs uncritically
- Authority proximity causing uncritical adoption
- Social proximity driving belief adoption
- Rapid spread without appropriate scrutiny

When informed adoption is present:
- Beliefs adopted after critical evaluation
- Social sharing accompanied by evidence
- Emotional engagement combined with reasoning
- Authority claims verified independently
- Proximity combined with independent assessment
- Spread accompanied by appropriate scrutiny
- Adoption based on evidence not social pressure

Output JSON with: contagion_present (bool), severity (none/mild/moderate/severe), belief (what belief spreads), mechanism (how it spreads), evaluation_bypass (how evaluation is bypassed), population (who is affected), recommendation (informed_adoption/mild_social_influence/significant_contagion/major_uncritical_spread/restore_critical_evaluation)."""

EPISTEMIC_CONTAGION_PROMPT = """Detect epistemic contagion:

Belief: {belief}
Mechanism: {mechanism}
Evaluation bypass: {evaluation_bypass}
Population: {population}
Domain: {domain}
Context: {context}

Are harmful beliefs spreading through social contact without critical evaluation? Return ONLY valid JSON."""


class EpistemicContagionService:
    """Detects epistemic contagion — harmful beliefs spreading without evaluation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        belief: str,
        *,
        mechanism: str = "",
        evaluation_bypass: str = "",
        population: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic contagion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_CONTAGION_PROMPT.format(
                belief=belief,
                mechanism=mechanism or "Not specified",
                evaluation_bypass=evaluation_bypass or "Not specified",
                population=population or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_CONTAGION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "belief": belief[:200],
            "contagion_present": data.get("contagion_present", False),
            "severity": data.get("severity", ""),
            "mechanism": data.get("mechanism", ""),
            "evaluation_bypass": data.get("evaluation_bypass", ""),
            "population": data.get("population", ""),
            "recommendation": data.get("recommendation", ""),
        }
