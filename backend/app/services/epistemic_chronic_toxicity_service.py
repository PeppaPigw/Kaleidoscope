"""EpistemicChronicToxicityService — Epistemic Chronic Toxicity Detection.

Detects epistemic chronic toxicity — slow accumulation of intellectual toxins
over time, causing gradual degradation without acute symptoms.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_CHRONIC_TOXICITY_SYSTEM = """You are an epistemic chronic toxicity specialist. Given intellectual exposure history, assess whether slow toxic accumulation is occurring:

Key concepts:
- Epistemic chronic toxicity: slow accumulation of intellectual toxins
- Bioaccumulation: toxins building up faster than elimination
- Subclinical damage: harm below symptom threshold
- Latency period: time between exposure and symptoms
- Threshold effect: damage appearing only after accumulation
- Organ reserve depletion: gradual loss of functional capacity
- Irreversibility: point of no return for accumulated damage

When epistemic chronic toxicity IS present:
- Slow accumulation of intellectual toxins over time
- Toxins building up faster than elimination
- Harm occurring below symptom threshold
- Long latency between exposure and visible damage
- Damage appearing only after critical accumulation
- Gradual loss of intellectual functional capacity
- Approaching irreversible damage threshold

When healthy state is present:
- No toxic accumulation
- Elimination exceeds intake
- No subclinical damage
- No latent harm
- Well below thresholds
- Full functional capacity
- Fully reversible state

Output JSON with: chronic_toxicity_present (bool), severity (none/mild/moderate/severe), bioaccumulation (what building up), subclinical_damage (what hidden harm), latency_period (what delay), organ_reserve (what capacity loss), recommendation (healthy_state/mild_toxicity/significant_chronic_toxicity/major_accumulation/halt_intellectual_toxic_exposure)."""

EPISTEMIC_CHRONIC_TOXICITY_PROMPT = """Detect epistemic chronic toxicity:

Bioaccumulation: {bioaccumulation}
Subclinical damage: {subclinical_damage}
Latency period: {latency_period}
Organ reserve: {organ_reserve}
Domain: {domain}
Context: {context}

Is there slow accumulation of intellectual toxins causing gradual degradation? Return ONLY valid JSON."""


class EpistemicChronicToxicityService:
    """Detects epistemic chronic toxicity — slow intellectual toxin accumulation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        bioaccumulation: str,
        *,
        subclinical_damage: str = "",
        latency_period: str = "",
        organ_reserve: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic chronic toxicity."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_CHRONIC_TOXICITY_PROMPT.format(
                bioaccumulation=bioaccumulation,
                subclinical_damage=subclinical_damage or "Not specified",
                latency_period=latency_period or "Not specified",
                organ_reserve=organ_reserve or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_CHRONIC_TOXICITY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "bioaccumulation": bioaccumulation[:200],
            "chronic_toxicity_present": data.get("chronic_toxicity_present", False),
            "severity": data.get("severity", ""),
            "subclinical_damage": data.get("subclinical_damage", ""),
            "latency_period": data.get("latency_period", ""),
            "organ_reserve": data.get("organ_reserve", ""),
            "recommendation": data.get("recommendation", ""),
        }
