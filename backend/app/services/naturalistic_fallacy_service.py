"""NaturalisticFallacyService — Naturalistic Fallacy Detection.

Detects the naturalistic fallacy — deriving 'ought' from 'is',
claiming something is good or right because it is natural, or
inferring moral properties from natural properties.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

NATURALISTIC_FALLACY_SYSTEM = """You are a naturalistic fallacy specialist. Given an argument, assess whether moral conclusions are being derived from natural facts:

Key concepts:
- Naturalistic fallacy: inferring 'ought' from 'is'
- Appeal to nature: claiming natural = good
- Open question argument: 'good' not reducible to natural properties
- Hume's guillotine: no deriving values from facts alone
- Evolutionary ethics: claiming evolved = morally justified
- Natural law confusion: conflating descriptive and prescriptive law
- Genetic fallacy variant: origin determines value

When the naturalistic fallacy IS present:
- Moral conclusion derived solely from natural facts
- 'Natural' used as synonym for 'good' or 'right'
- Evolutionary origin cited as moral justification
- Statistical normality equated with moral normativity
- Biological facts treated as moral prescriptions
- 'That's just how things are' used to justify 'how they should be'
- Natural properties identified with moral properties

When naturalistic reasoning is appropriate:
- Natural facts cited as relevant evidence, not sole justification
- Distinction between is and ought maintained
- Normative premises made explicit
- Nature informs but doesn't determine moral conclusions
- Evolutionary context provides understanding, not justification
- Natural facts constrain what's possible, not what's good
- Bridge principles between facts and values stated

Output JSON with: fallacy_present (bool), severity (none/mild/moderate/severe), argument (what is argued), natural_fact (what natural fact is cited), moral_conclusion (what moral conclusion is drawn), missing_premise (what normative premise is unstated), recommendation (appropriate_naturalistic_reasoning/mild_is_ought_slide/significant_naturalistic_fallacy/major_nature_as_morality/separate_is_from_ought)."""

NATURALISTIC_FALLACY_PROMPT = """Detect naturalistic fallacy:

Argument: {argument}
Natural fact cited: {fact}
Moral conclusion: {conclusion}
Bridge principle: {bridge}
Domain: {domain}
Context: {context}

Is a moral conclusion being derived from natural facts without adequate normative premises? Return ONLY valid JSON."""


class NaturalisticFallacyService:
    """Detects naturalistic fallacy — deriving ought from is."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        argument: str,
        *,
        fact: str = "",
        conclusion: str = "",
        bridge: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect naturalistic fallacy."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=NATURALISTIC_FALLACY_PROMPT.format(
                argument=argument,
                fact=fact or "Not specified",
                conclusion=conclusion or "Not specified",
                bridge=bridge or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=NATURALISTIC_FALLACY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "argument": argument[:200],
            "fallacy_present": data.get("fallacy_present", False),
            "severity": data.get("severity", ""),
            "natural_fact": data.get("natural_fact", ""),
            "moral_conclusion": data.get("moral_conclusion", ""),
            "missing_premise": data.get("missing_premise", ""),
            "recommendation": data.get("recommendation", ""),
        }
