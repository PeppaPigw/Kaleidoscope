"""EpistemicDeliquesenceService — Epistemic Deliquescence Detection.

Detects epistemic deliquescence — solid ideas absorbing so much ambient
uncertainty that they dissolve into their own absorbed moisture.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_DELIQUESCENCE_SYSTEM = """You are an epistemic deliquescence specialist. Given an idea dissolution pattern, assess whether solid ideas dissolve from absorbing ambient uncertainty:

Key concepts:
- Epistemic deliquescence: solid ideas dissolving from absorbed uncertainty
- Hygroscopy: tendency to absorb ambient uncertainty
- Critical humidity: threshold where dissolution begins
- Self-dissolution: idea dissolving in its own absorbed moisture
- Saturated solution: fully dissolved state
- Humidity control: managing ambient uncertainty levels
- Desiccant: substance that removes ambient uncertainty

When epistemic deliquescence IS present:
- Solid ideas dissolving from absorbing too much ambient uncertainty
- Strong tendency to absorb surrounding uncertainty
- Threshold of ambient uncertainty triggering dissolution
- Ideas dissolving in their own absorbed doubt
- Fully dissolved state where no solid belief remains
- Need to manage ambient uncertainty levels
- Need for substances that remove ambient uncertainty

When humidity resistance is present:
- Ideas maintaining solidity despite ambient uncertainty
- No tendency to absorb surrounding uncertainty
- No threshold triggering dissolution
- Ideas stable regardless of ambient doubt
- Solid belief maintained
- No need to manage ambient uncertainty
- No desiccant needed

Output JSON with: deliquescence_present (bool), severity (none/mild/moderate/severe), hygroscopy (what tendency to absorb), critical_humidity (what threshold triggers), self_dissolution (what dissolves in own moisture), desiccant (what removes uncertainty), recommendation (humidity_resistance/mild_absorption/significant_deliquescence/major_self_dissolution/reduce_ambient_uncertainty)."""

EPISTEMIC_DELIQUESCENCE_PROMPT = """Detect epistemic deliquescence:

Hygroscopy: {hygroscopy}
Critical humidity: {critical_humidity}
Self-dissolution: {self_dissolution}
Desiccant: {desiccant}
Domain: {domain}
Context: {context}

Are solid ideas absorbing so much ambient uncertainty that they dissolve into their own absorbed moisture? Return ONLY valid JSON."""


class EpistemicDeliquesenceService:
    """Detects epistemic deliquescence — ideas dissolving from absorbed uncertainty."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        hygroscopy: str,
        *,
        critical_humidity: str = "",
        self_dissolution: str = "",
        desiccant: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic deliquescence."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_DELIQUESCENCE_PROMPT.format(
                hygroscopy=hygroscopy,
                critical_humidity=critical_humidity or "Not specified",
                self_dissolution=self_dissolution or "Not specified",
                desiccant=desiccant or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_DELIQUESCENCE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "hygroscopy": hygroscopy[:200],
            "deliquescence_present": data.get("deliquescence_present", False),
            "severity": data.get("severity", ""),
            "critical_humidity": data.get("critical_humidity", ""),
            "self_dissolution": data.get("self_dissolution", ""),
            "desiccant": data.get("desiccant", ""),
            "recommendation": data.get("recommendation", ""),
        }
