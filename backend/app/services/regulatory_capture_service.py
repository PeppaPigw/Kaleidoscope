"""RegulatoryCaptureService — Regulatory Capture Detection.

Identifies when a regulatory body, standard-setting organization,
or oversight mechanism has been co-opted by the entities it's
supposed to regulate. The regulator ends up serving industry
interests over public interest — revolving doors, industry-funded
research, captured advisory boards.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

CAPTURE_SYSTEM = """You are a regulatory capture specialist. Given a regulatory situation, assess whether capture has occurred:
- Is the regulator serving industry interests over public interest?
- Are there revolving door patterns (regulators moving to/from industry)?
- Is the regulator's information primarily sourced from the regulated industry?
- Do regulations consistently benefit incumbents over new entrants?
- Has the regulator become dependent on industry cooperation to function?

Output JSON with: capture_detected (bool), severity (none/mild/moderate/severe/complete), regulator (the regulatory body or oversight mechanism), regulated_entity (who is being regulated), capture_mechanisms (list of: mechanism, evidence, severity), revolving_door (bool — personnel moving between regulator and industry), information_capture (bool — regulator depends on industry for data/expertise), funding_capture (bool — regulator funded by those it regulates), cultural_capture (bool — regulator adopts industry worldview), regulatory_outcomes (who actually benefits from recent regulations), barrier_to_entry_created (bool — do regulations protect incumbents?), public_interest_served (0-1 — how well is public interest being served), industry_interest_served (0-1 — how well is industry interest being served), counterfactual (what regulation would look like without capture), warning_signs (early indicators of capture), reform_options (how to reduce capture), recommendation (no_capture/monitor/reform_needed/replace_regulator/structural_change)."""

CAPTURE_PROMPT = """Detect regulatory capture:

Situation: {situation}
Regulator: {regulator}
Regulated industry: {industry}
Recent decisions: {decisions}
Domain: {domain}
Context: {context}

Is regulatory capture present? Return ONLY valid JSON."""


class RegulatoryCaptureService:
    """Detects regulatory capture and institutional co-option."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        regulator: str = "",
        industry: str = "",
        decisions: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect regulatory capture."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=CAPTURE_PROMPT.format(
                situation=situation,
                regulator=regulator or "Not specified",
                industry=industry or "Not specified",
                decisions=decisions or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=CAPTURE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "capture_detected": data.get("capture_detected", False),
            "severity": data.get("severity", ""),
            "regulator": data.get("regulator", ""),
            "regulated_entity": data.get("regulated_entity", ""),
            "capture_mechanisms": data.get("capture_mechanisms", []),
            "revolving_door": data.get("revolving_door", False),
            "information_capture": data.get("information_capture", False),
            "funding_capture": data.get("funding_capture", False),
            "cultural_capture": data.get("cultural_capture", False),
            "regulatory_outcomes": data.get("regulatory_outcomes", ""),
            "barrier_to_entry_created": data.get("barrier_to_entry_created", False),
            "public_interest_served": data.get("public_interest_served", 0),
            "industry_interest_served": data.get("industry_interest_served", 0),
            "counterfactual": data.get("counterfactual", ""),
            "warning_signs": data.get("warning_signs", []),
            "reform_options": data.get("reform_options", ""),
            "recommendation": data.get("recommendation", ""),
        }
