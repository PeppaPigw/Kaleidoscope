"""ParadigmShiftDetectorService — Kuhnian Anomaly Detection.

Identifies when evidence is accumulating that suggests the current
paradigm is inadequate and a shift may be needed. Detects anomalies,
ad-hoc patches, and signs of paradigm exhaustion.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

PARADIGM_SYSTEM = """You are a paradigm shift detection specialist. Given a field and its current paradigm, identify signs of paradigm stress:
- Anomalies: findings that don't fit the current framework
- Ad-hoc patches: modifications added to save the theory rather than explain new data
- Proliferation of epicycles: increasing complexity without increasing explanatory power
- Young researchers defecting: are newcomers attracted to alternative frameworks?
- Explanatory gaps: phenomena the paradigm can't address
- Alternative frameworks gaining traction

Output JSON with: paradigm_health (healthy/stressed/crisis/pre_revolutionary), anomalies (list of: anomaly, severity (minor/moderate/major), how_long_known, current_explanation_quality (good/strained/ad_hoc/none)), ad_hoc_patches (list of modifications that feel like epicycles), alternative_frameworks (list of: framework, traction (fringe/growing/serious_contender), strengths, weaknesses), crisis_indicators (list of signs the paradigm is failing), paradigm_age (young/mature/aging/exhausted), prediction (what happens next: consolidation/reform/revolution/fragmentation), confidence (0-1), timeline (when might a shift happen if one is coming)."""

PARADIGM_PROMPT = """Detect paradigm shift signals:

Field: {field}
Current paradigm: {paradigm}
Recent anomalies: {anomalies}
Domain: {domain}

Is the paradigm under stress? Return ONLY valid JSON."""


class ParadigmShiftDetectorService:
    """Detects signs of paradigm stress and potential shifts."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        field: str,
        *,
        paradigm: str = "",
        anomalies: str = "",
        domain: str = "",
    ) -> dict:
        """Detect paradigm shift signals."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=PARADIGM_PROMPT.format(
                field=field,
                paradigm=paradigm or "The dominant framework",
                anomalies=anomalies or "Not specified",
                domain=domain or field,
            ),
            system=PARADIGM_SYSTEM,
            max_tokens=4096,
            temperature=0.4,
        )
        data = parse_llm_json(raw)

        return {
            "field": field[:200],
            "paradigm_health": data.get("paradigm_health", ""),
            "anomalies": data.get("anomalies", []),
            "ad_hoc_patches": data.get("ad_hoc_patches", []),
            "alternative_frameworks": data.get("alternative_frameworks", []),
            "crisis_indicators": data.get("crisis_indicators", []),
            "paradigm_age": data.get("paradigm_age", ""),
            "prediction": data.get("prediction", ""),
            "confidence": data.get("confidence", 0),
            "timeline": data.get("timeline", ""),
        }
