"""ParkinsonLawService — Parkinson's Law Detection.

Detects Parkinson's Law — work expands to fill the time available
for its completion. C. Northcote Parkinson (1955). Also applies
to budgets (spending expands to consume available budget),
storage (data expands to fill available space), and bureaucracy
(staff grows regardless of work volume).
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

PARKINSON_SYSTEM = """You are a Parkinson's Law specialist. Given a project, budget, or organizational situation, assess whether Parkinson's Law is causing unnecessary expansion:

Key concepts (Parkinson, 1955):
- Parkinson's Law: work expands to fill the time available
- Budget variant: spending expands to consume available budget
- Storage variant: data/stuff expands to fill available space
- Bureaucracy variant: staff grows 5-7% per year regardless of work volume
- Gold-plating: adding unnecessary features because time/budget allows
- Artificial complexity: making things more complex than needed to justify resources
- Student syndrome: starting late because the deadline seems far away

When Parkinson's Law IS operating:
- Tasks take exactly as long as allocated (suspicious precision)
- Budgets are always fully spent regardless of actual needs
- Scope creeps to fill available time/resources
- Work that could be done in days takes weeks because weeks were allocated
- Bureaucracy grows without corresponding increase in output
- Artificial complexity is added to justify headcount/budget

When full utilization IS appropriate:
- The time/budget was carefully estimated based on actual requirements
- Additional time is used for genuine quality improvement
- Scope expansion reflects real discovered requirements
- Resources are being invested in valuable future capabilities

Output JSON with: parkinson_law_present (bool), severity (none/mild/moderate/severe), resource_type (time/budget/staff/space), allocated (what was allocated), actually_needed (what was actually needed), expansion_mechanism (how work/spending expanded), gold_plating (bool — unnecessary additions because resources allow?), artificial_complexity (bool — complexity added to justify resources?), student_syndrome (bool — delayed start because deadline seems far?), bureaucratic_growth (bool — staff growing without output growth?), utilization_vs_value (is full utilization creating value or just consuming resources?), tight_constraint_test (what would happen with 50% less time/budget?), genuine_requirements (what actually needs to be done), waste_estimate (how much resource is being consumed without value), recommendation (utilization_appropriate/mild_expansion/significant_parkinson_effect/major_resource_waste/constrain_resources)."""

PARKINSON_PROMPT = """Detect Parkinson's Law:

Situation: {situation}
Resources allocated: {resources}
Work completed: {work}
Timeline: {timeline}
Domain: {domain}
Context: {context}

Is Parkinson's Law causing unnecessary expansion? Return ONLY valid JSON."""


class ParkinsonLawService:
    """Detects Parkinson's Law — work expanding to fill available time/resources."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        resources: str = "",
        work: str = "",
        timeline: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect Parkinson's Law."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=PARKINSON_PROMPT.format(
                situation=situation,
                resources=resources or "Not specified",
                work=work or "Not specified",
                timeline=timeline or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=PARKINSON_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "parkinson_law_present": data.get("parkinson_law_present", False),
            "severity": data.get("severity", ""),
            "resource_type": data.get("resource_type", ""),
            "allocated": data.get("allocated", ""),
            "actually_needed": data.get("actually_needed", ""),
            "expansion_mechanism": data.get("expansion_mechanism", ""),
            "gold_plating": data.get("gold_plating", False),
            "artificial_complexity": data.get("artificial_complexity", False),
            "student_syndrome": data.get("student_syndrome", False),
            "bureaucratic_growth": data.get("bureaucratic_growth", False),
            "utilization_vs_value": data.get("utilization_vs_value", ""),
            "tight_constraint_test": data.get("tight_constraint_test", ""),
            "genuine_requirements": data.get("genuine_requirements", ""),
            "waste_estimate": data.get("waste_estimate", ""),
            "recommendation": data.get("recommendation", ""),
        }
