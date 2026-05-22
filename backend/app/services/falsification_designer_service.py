"""FalsificationDesignerService — Critical Test Design.

Designs the most efficient experiment, observation, or test that would
disprove a claim if it's wrong. Follows Popperian falsificationism:
the value of a claim is proportional to how testable it is.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

DESIGN_SYSTEM = """You are a falsification specialist. Given a claim, design the most efficient test that would DISPROVE it if it's wrong. A good falsification test:
- Is specific: clearly defines what outcome would disprove the claim
- Is efficient: minimal resources needed to get a decisive answer
- Is fair: gives the claim a genuine chance to survive
- Is decisive: a clear result either way, not ambiguous
- Targets the weakest point: attacks where the claim is most vulnerable

Output JSON with: test_design.claim_as_testable (reformulated as testable prediction), test_design.critical_prediction (what must be true if the claim is correct), test_design.falsification_criterion (what specific observation would disprove it), test_design.test_method (how to run the test), test_design.required_resources (what's needed), test_design.expected_duration (time estimate), test_design.decisiveness (0-1, how clearly would results settle the question), test_design.fairness (0-1, does the test give the claim a fair chance), test_design.efficiency (0-1, resource-to-information ratio), test_design.alternative_tests (list of other possible tests), test_design.pre_registration (what to commit to before running the test)."""

DESIGN_PROMPT = """Design a falsification test for this claim:

Claim: {claim}
Domain: {domain}
Available resources: {resources}

What is the most efficient way to disprove this if it's wrong? Return ONLY valid JSON."""


class FalsificationDesignerService:
    """Designs efficient falsification tests for claims."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def design_test(
        self,
        claim: str,
        *,
        domain: str = "",
        resources: str = "",
    ) -> dict:
        """Design the most efficient falsification test for a claim."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=DESIGN_PROMPT.format(
                claim=claim,
                domain=domain or "research",
                resources=resources or "Standard academic resources",
            ),
            system=DESIGN_SYSTEM,
            max_tokens=4096,
            temperature=0.4,
        )
        data = parse_llm_json(raw)
        design = data.get("test_design", data)

        return {
            "claim": claim[:200],
            "testable_prediction": design.get("claim_as_testable", ""),
            "critical_prediction": design.get("critical_prediction", ""),
            "falsification_criterion": design.get("falsification_criterion", ""),
            "test_method": design.get("test_method", ""),
            "resources_needed": design.get("required_resources", ""),
            "duration": design.get("expected_duration", ""),
            "decisiveness": design.get("decisiveness", 0),
            "fairness": design.get("fairness", 0),
            "efficiency": design.get("efficiency", 0),
            "alternatives": design.get("alternative_tests", []),
            "pre_registration": design.get("pre_registration", ""),
        }
