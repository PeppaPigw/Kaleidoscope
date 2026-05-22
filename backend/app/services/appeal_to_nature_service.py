"""AppealToNatureService — Appeal to Nature Detection.

Detects appeal to nature — arguing that something is good because
it is 'natural' or bad because it is 'unnatural'. This conflates
the descriptive (what is natural) with the normative (what is good),
committing the naturalistic fallacy.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

APPEAL_NATURE_SYSTEM = """You are an appeal to nature specialist. Given an argument, assess whether it fallaciously equates 'natural' with 'good' or 'unnatural' with 'bad':

Key concepts:
- Naturalistic fallacy: deriving 'ought' from 'is' (what's natural = what's good)
- Is-ought gap: descriptive facts don't entail normative conclusions
- Natural vs artificial: this distinction doesn't map to good vs bad
- Selective naturalism: cherry-picking which natural things are "good"
- Appeal to tradition: related fallacy (old = good)
- Genetic fallacy: judging by origin rather than merit
- Romanticism: idealizing nature as inherently benevolent

When appeal to nature IS present:
- "X is natural, therefore X is good/healthy/right"
- "Y is artificial/synthetic, therefore Y is bad/harmful/wrong"
- Using "natural" as a synonym for "good" without justification
- "Our ancestors did X, so X must be better"
- Ignoring that many natural things are harmful (arsenic, disease)
- Ignoring that many artificial things are beneficial (medicine, sanitation)
- Treating "natural" as self-evidently positive

When appeal to nature is NOT present:
- Empirical claims about natural vs synthetic properties (testable)
- Ecological arguments about ecosystem disruption (specific mechanism)
- Arguments that happen to favor natural options for independent reasons
- Acknowledging that "natural" doesn't automatically mean "better"
- Using "natural" descriptively, not normatively
- Arguments about sustainability or environmental impact (specific harms)
- Preference for natural stated as preference, not as logical argument

Output JSON with: appeal_to_nature_present (bool), severity (none/mild/moderate/severe), claim (what is argued), natural_equated (what natural thing is called good), normative_leap (how is-ought gap is crossed), counterexamples (natural things that are bad or artificial things that are good), recommendation (no_appeal_to_nature/mild_naturalism/significant_appeal_to_nature/major_naturalistic_fallacy/evaluate_on_merits)."""

APPEAL_NATURE_PROMPT = """Detect appeal to nature:

Argument: {argument}
Claim: {claim}
Natural basis: {natural_basis}
Normative conclusion: {normative_conclusion}
Domain: {domain}
Context: {context}

Does this argue something is good because it's natural or bad because it's unnatural? Return ONLY valid JSON."""


class AppealToNatureService:
    """Detects appeal to nature — equating natural with good."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        argument: str,
        *,
        claim: str = "",
        natural_basis: str = "",
        normative_conclusion: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect appeal to nature."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=APPEAL_NATURE_PROMPT.format(
                argument=argument,
                claim=claim or "Not specified",
                natural_basis=natural_basis or "Not specified",
                normative_conclusion=normative_conclusion or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=APPEAL_NATURE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "argument": argument[:200],
            "appeal_to_nature_present": data.get("appeal_to_nature_present", False),
            "severity": data.get("severity", ""),
            "claim": data.get("claim", ""),
            "natural_equated": data.get("natural_equated", ""),
            "normative_leap": data.get("normative_leap", ""),
            "recommendation": data.get("recommendation", ""),
        }
