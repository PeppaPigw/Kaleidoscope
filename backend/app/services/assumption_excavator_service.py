"""AssumptionExcavatorService — Hidden Assumption Discovery.

Surfaces hidden, implicit, or unstated assumptions in arguments and claims.
Identifies which assumptions are load-bearing (if wrong, the conclusion
collapses) vs decorative (wrong but inconsequential). Critical for
identifying fragile reasoning.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EXCAVATE_SYSTEM = """You are an assumption excavation specialist. Given an argument or claim, identify ALL hidden assumptions — things that must be true for the conclusion to hold but are never explicitly stated. For each assumption, assess:
- How hidden is it? (obvious/subtle/deeply_buried)
- How load-bearing is it? (decorative/supporting/critical/foundational)
- How likely is it to be wrong? (very_unlikely/unlikely/possible/likely/very_likely)
- What happens if it's wrong? (minor_adjustment/weakened_conclusion/invalidated/catastrophic)

Output JSON with: assumptions (list of: assumption, hiddenness, load_bearing, wrong_probability (0-1), if_wrong_impact, domain_of_assumption, testable (bool), test_method), most_dangerous (which assumption and why), assumption_count, reasoning_fragility (0-1, where 1 means many critical hidden assumptions), meta_assumptions (assumptions about the analysis itself)."""

EXCAVATE_PROMPT = """Excavate hidden assumptions in this argument:

Argument/Claim: {argument}
Domain: {domain}
Context: {context}

What must be true (but isn't stated) for this to hold? Return ONLY valid JSON."""

STRESS_SYSTEM = """You are an assumption stress-tester. Given a specific assumption, explore what happens when it fails. Consider:
- Partial failure: what if the assumption is only partially true?
- Gradual failure: what if it was true but is becoming less true?
- Context-dependent failure: where does it hold and where doesn't it?
- Cascading effects: what other assumptions depend on this one?

Output JSON with: stress_test.assumption, stress_test.failure_modes (list of: mode, probability (0-1), consequence, severity), stress_test.partial_truth_range (what range of truth values is plausible), stress_test.temporal_stability (stable/eroding/volatile), stress_test.context_boundaries (where it holds, where it fails), stress_test.dependent_assumptions (list), stress_test.overall_risk (low/medium/high/critical), stress_test.mitigation (how to reduce dependence on this assumption)."""

STRESS_PROMPT = """Stress-test this assumption:

Assumption: {assumption}
Original argument: {argument}
Domain: {domain}

What happens when this assumption fails? Return ONLY valid JSON."""


class AssumptionExcavatorService:
    """Surfaces and stress-tests hidden assumptions in arguments."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def excavate(
        self,
        argument: str,
        *,
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Surface hidden assumptions in an argument."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EXCAVATE_PROMPT.format(
                argument=argument,
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EXCAVATE_SYSTEM,
            max_tokens=4096,
            temperature=0.4,
        )
        data = parse_llm_json(raw)

        assumptions = data.get("assumptions", [])
        return {
            "argument": argument[:200],
            "assumption_count": len(assumptions),
            "assumptions": assumptions,
            "most_dangerous": data.get("most_dangerous", ""),
            "reasoning_fragility": data.get("reasoning_fragility", 0),
            "meta_assumptions": data.get("meta_assumptions", []),
        }

    async def stress_test(
        self,
        assumption: str,
        *,
        argument: str = "",
        domain: str = "",
    ) -> dict:
        """Stress-test a specific assumption."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=STRESS_PROMPT.format(
                assumption=assumption,
                argument=argument or "Not specified",
                domain=domain or "general",
            ),
            system=STRESS_SYSTEM,
            max_tokens=4096,
            temperature=0.4,
        )
        data = parse_llm_json(raw)
        test = data.get("stress_test", data)

        return {
            "assumption": assumption,
            "failure_modes": test.get("failure_modes", []),
            "partial_truth_range": test.get("partial_truth_range", ""),
            "temporal_stability": test.get("temporal_stability", ""),
            "context_boundaries": test.get("context_boundaries", {}),
            "dependent_assumptions": test.get("dependent_assumptions", []),
            "overall_risk": test.get("overall_risk", ""),
            "mitigation": test.get("mitigation", ""),
        }
