"""MapTerritoryConfusionService — Map-Territory Confusion Detection.

Detects map-territory confusion — confusing the model/map/theory
with the reality it represents. Korzybski (1933): "The map is
not the territory." Models are useful simplifications, but when
we forget they're simplifications, we make decisions based on
model properties that don't exist in reality.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

MAP_TERRITORY_SYSTEM = """You are a map-territory confusion specialist. Given a reasoning process, assess whether a model or representation is being confused with the reality it represents:

Key concepts (Korzybski, 1933):
- Map-territory confusion: confusing the model with reality
- Model realism: treating model properties as real properties
- Menu-meal confusion: the description is not the thing
- Abstraction leak: model simplifications treated as real constraints
- Metric-reality gap: the measurement is not the thing measured
- Category-instance confusion: the category is not the member
- Word-thing confusion: the name is not the named

When map-territory confusion IS present:
- Treating model predictions as certain outcomes
- Confusing the organizational chart with actual power structures
- Treating economic models as if they ARE the economy
- Assuming reality must conform to the theory
- "The model says X, therefore X will happen"
- Treating categories as having sharp boundaries in reality
- Confusing the job description with the actual job

When model-based reasoning IS appropriate:
- The model is acknowledged as a simplification
- Model limitations are explicitly stated
- Predictions are treated as probabilistic, not certain
- The model is regularly validated against reality
- Decisions account for model-reality gaps
- Multiple models are used to triangulate

Output JSON with: map_territory_confusion_present (bool), severity (none/mild/moderate/severe), model (what model/map is being used), reality (what reality it represents), confusion_point (where does model diverge from reality), model_property (what model property is being treated as real), real_property (what is the actual property of reality), consequences (what decisions are affected), recommendation (model_use_appropriate/mild_model_realism/significant_map_territory_confusion/major_model_reality_conflation/distinguish_model_from_reality)."""

MAP_TERRITORY_PROMPT = """Detect map-territory confusion:

Reasoning: {reasoning}
Model used: {model}
Reality: {reality}
Assumption: {assumption}
Domain: {domain}
Context: {context}

Is a model or representation being confused with the reality it represents? Return ONLY valid JSON."""


class MapTerritoryConfusionService:
    """Detects map-territory confusion — confusing models with reality."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        reasoning: str,
        *,
        model: str = "",
        reality: str = "",
        assumption: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect map-territory confusion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=MAP_TERRITORY_PROMPT.format(
                reasoning=reasoning,
                model=model or "Not specified",
                reality=reality or "Not specified",
                assumption=assumption or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=MAP_TERRITORY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "reasoning": reasoning[:200],
            "map_territory_confusion_present": data.get("map_territory_confusion_present", False),
            "severity": data.get("severity", ""),
            "model": data.get("model", ""),
            "reality": data.get("reality", ""),
            "confusion_point": data.get("confusion_point", ""),
            "model_property": data.get("model_property", ""),
            "real_property": data.get("real_property", ""),
            "consequences": data.get("consequences", ""),
            "recommendation": data.get("recommendation", ""),
        }
