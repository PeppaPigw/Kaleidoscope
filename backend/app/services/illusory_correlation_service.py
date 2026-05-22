"""IllusoryCorrelationService — Illusory Correlation Detection.

Detects illusory correlation — perceiving a relationship
between variables where none exists, or overestimating the
strength of a weak relationship. Chapman (1967). Seeing
patterns in randomness. Leads to stereotyping, superstition,
and false causal beliefs.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

ILLUSORY_CORRELATION_SYSTEM = """You are an illusory correlation specialist. Given a claimed relationship between variables, assess whether the correlation is real or illusory:

Key concepts (Chapman, 1967):
- Illusory correlation: perceiving relationships that don't exist
- Distinctive co-occurrence: rare events paired together seem related
- Confirmation bias interaction: noticing confirming cases, ignoring disconfirming
- Availability heuristic interaction: memorable co-occurrences seem frequent
- Base rate neglect: ignoring how often each variable occurs independently
- Stereotyping mechanism: minority group + negative behavior = illusory correlation
- Apophenia: tendency to perceive meaningful patterns in random data

When illusory correlation IS present:
- "Every time X happens, Y follows" without systematic data
- Stereotypes based on memorable but rare co-occurrences
- Superstitious beliefs linking unrelated events
- "I always get sick when..." based on selective memory
- Seeing patterns in random sequences
- Confusing co-occurrence with correlation

When the correlation IS real:
- Systematic data collection confirms the relationship
- The correlation survives controlling for confounds
- A plausible causal mechanism exists
- The relationship replicates across samples
- Base rates are properly accounted for
- Effect size is meaningful, not just statistically significant

Output JSON with: illusory_correlation_present (bool), severity (none/mild/moderate/severe), claimed_relationship (what relationship is claimed), variable_a (first variable), variable_b (second variable), evidence_for (what evidence supports the correlation?), evidence_against (what evidence contradicts it?), base_rates_considered (bool — are base rates accounted for?), confounds (what confounding variables exist?), selective_attention (bool — is attention biased toward confirming cases?), sample_size (how much data supports the claim?), causal_mechanism (is there a plausible mechanism?), recommendation (correlation_supported/mild_overestimation/significant_illusory_correlation/major_false_pattern/collect_systematic_data)."""

ILLUSORY_CORRELATION_PROMPT = """Detect illusory correlation:

Claimed relationship: {relationship}
Evidence: {evidence}
Data: {data}
Alternative explanations: {alternatives}
Domain: {domain}
Context: {context}

Is the perceived relationship real or illusory? Return ONLY valid JSON."""


class IllusoryCorrelationService:
    """Detects illusory correlation — perceiving relationships that don't exist."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        relationship: str,
        *,
        evidence: str = "",
        data: str = "",
        alternatives: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect illusory correlation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=ILLUSORY_CORRELATION_PROMPT.format(
                relationship=relationship,
                evidence=evidence or "Not specified",
                data=data or "Not specified",
                alternatives=alternatives or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=ILLUSORY_CORRELATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data_result = parse_llm_json(raw)

        return {
            "relationship": relationship[:200],
            "illusory_correlation_present": data_result.get("illusory_correlation_present", False),
            "severity": data_result.get("severity", ""),
            "variable_a": data_result.get("variable_a", ""),
            "variable_b": data_result.get("variable_b", ""),
            "evidence_for": data_result.get("evidence_for", ""),
            "evidence_against": data_result.get("evidence_against", ""),
            "base_rates_considered": data_result.get("base_rates_considered", True),
            "confounds": data_result.get("confounds", ""),
            "selective_attention": data_result.get("selective_attention", False),
            "sample_size": data_result.get("sample_size", ""),
            "causal_mechanism": data_result.get("causal_mechanism", ""),
            "recommendation": data_result.get("recommendation", ""),
        }
