"""EpistemicExcavationService — Epistemic Excavation Assessment.

Assesses epistemic excavation needs — identifying what buried
knowledge should be recovered and how.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_EXCAVATION_SYSTEM = """You are an epistemic excavation specialist. Given a knowledge recovery need, assess what buried knowledge should be recovered:

Key concepts:
- Epistemic excavation: recovering buried knowledge
- Recovery priority: what should be recovered first
- Excavation method: how to recover buried knowledge
- Preservation state: how well preserved the knowledge is
- Context reconstruction: reconstructing lost context
- Reintegration: reintegrating recovered knowledge
- Value assessment: assessing value of buried knowledge

When excavation IS needed:
- Important knowledge buried and needing recovery
- High-priority knowledge inaccessible
- Methods available for recovery
- Knowledge likely preserved enough to recover
- Context can be reconstructed
- Recovered knowledge can be reintegrated
- Buried knowledge has significant value

When excavation is NOT needed:
- Knowledge accessible and available
- No important buried knowledge
- Current knowledge sufficient
- Nothing of value buried
- Context already available
- No reintegration needed
- No significant buried value

Output JSON with: excavation_needed (bool), priority (none/low/medium/high), target (what knowledge to excavate), method (how to excavate), preservation (how well preserved), value (value of recovery), recommendation (no_excavation_needed/low_priority_recovery/medium_priority_excavation/high_priority_urgent_recovery/immediate_excavation_required)."""

EPISTEMIC_EXCAVATION_PROMPT = """Assess epistemic excavation need:

Target: {target}
Method: {method}
Preservation: {preservation}
Value: {value}
Domain: {domain}
Context: {context}

What buried knowledge should be recovered and how? Return ONLY valid JSON."""


class EpistemicExcavationService:
    """Assesses epistemic excavation needs — what buried knowledge to recover."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        target: str,
        *,
        method: str = "",
        preservation: str = "",
        value: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Assess epistemic excavation need."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_EXCAVATION_PROMPT.format(
                target=target,
                method=method or "Not specified",
                preservation=preservation or "Not specified",
                value=value or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_EXCAVATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "target": target[:200],
            "excavation_needed": data.get("excavation_needed", False),
            "priority": data.get("priority", ""),
            "method": data.get("method", ""),
            "preservation": data.get("preservation", ""),
            "value": data.get("value", ""),
            "recommendation": data.get("recommendation", ""),
        }
