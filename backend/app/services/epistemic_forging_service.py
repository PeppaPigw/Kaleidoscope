"""EpistemicForgingService — Epistemic Forging Detection.

Detects epistemic forging — knowledge shaped by force (authority,
pressure, ideology) rather than by evidence and reasoning.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_FORGING_SYSTEM = """You are an epistemic forging specialist. Given a knowledge formation pattern, assess whether knowledge is shaped by force rather than evidence:

Key concepts:
- Epistemic forging: shaping knowledge through force rather than evidence
- Forced shape: conclusions hammered into predetermined form
- Authority pressure: authority forcing knowledge into shape
- Ideological mold: ideology providing the mold for conclusions
- Evidence ignored: evidence subordinated to force
- Predetermined form: conclusions shaped before evidence examined
- Hammer marks: visible signs of forced shaping

When epistemic forging IS present:
- Knowledge shaped by authority rather than evidence
- Conclusions hammered into predetermined form
- Authority pressure forcing specific conclusions
- Ideology providing the mold for knowledge
- Evidence subordinated to external force
- Conclusions predetermined before evidence examined
- Visible signs of forced shaping in reasoning

When evidence-shaped knowledge is present:
- Knowledge shaped by evidence and reasoning
- Conclusions emerging from evidence naturally
- No authority pressure distorting conclusions
- No ideological mold constraining knowledge
- Evidence driving conclusion formation
- Conclusions following from evidence examination
- No signs of forced shaping

Output JSON with: forging_present (bool), severity (none/mild/moderate/severe), knowledge (what knowledge is forged), force (what force shapes it), mold (what predetermined form), evidence_ignored (what evidence is ignored), recommendation (evidence_shaped/mild_pressure/significant_forging/major_forced_conclusion/let_evidence_shape)."""

EPISTEMIC_FORGING_PROMPT = """Detect epistemic forging:

Knowledge: {knowledge}
Force: {force}
Mold: {mold}
Evidence ignored: {evidence_ignored}
Domain: {domain}
Context: {context}

Is knowledge being shaped by force rather than evidence? Return ONLY valid JSON."""


class EpistemicForgingService:
    """Detects epistemic forging — knowledge shaped by force rather than evidence."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        knowledge: str,
        *,
        force: str = "",
        mold: str = "",
        evidence_ignored: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic forging."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_FORGING_PROMPT.format(
                knowledge=knowledge,
                force=force or "Not specified",
                mold=mold or "Not specified",
                evidence_ignored=evidence_ignored or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_FORGING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "knowledge": knowledge[:200],
            "forging_present": data.get("forging_present", False),
            "severity": data.get("severity", ""),
            "force": data.get("force", ""),
            "mold": data.get("mold", ""),
            "evidence_ignored": data.get("evidence_ignored", ""),
            "recommendation": data.get("recommendation", ""),
        }
