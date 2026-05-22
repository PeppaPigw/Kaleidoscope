"""SampleBiasService — Sample Bias Detection.

Detects sample bias — when the sample used to draw conclusions
doesn't represent the population being generalized to. This
includes self-selection, convenience sampling, and systematic
exclusion of relevant subgroups.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

SAMPLE_BIAS_SYSTEM = """You are a sample bias specialist. Given a generalization, assess whether the sample represents the target population:

Key concepts:
- Sample bias: sample doesn't represent the population
- Self-selection: participants choose to be in the study
- Convenience sampling: using whoever is available
- WEIRD samples: Western, Educated, Industrialized, Rich, Democratic
- Systematic exclusion: certain groups consistently left out
- Response bias: who responds vs who doesn't
- External validity: can results generalize beyond the sample

When sample bias IS present:
- Sample systematically differs from target population
- Self-selection creating non-representative group
- Convenience sample generalized to broader population
- Key subgroups excluded from the sample
- Response rate low with likely non-random non-response
- WEIRD sample generalized to all humans
- Generalization beyond what sample supports

When sample is representative:
- Sample drawn to represent target population
- Selection method minimizes systematic bias
- Key subgroups proportionally represented
- Response rate adequate or non-response analyzed
- Limitations of sample acknowledged
- Generalization limited to what sample supports
- External validity explicitly assessed

Output JSON with: bias_present (bool), severity (none/mild/moderate/severe), sample (who is in the sample), population (who is being generalized to), mismatch (how sample differs from population), exclusions (who is systematically excluded), recommendation (representative_sample/mild_bias/significant_sample_bias/major_generalization_error/limit_generalization)."""

SAMPLE_BIAS_PROMPT = """Detect sample bias:

Generalization: {generalization}
Sample: {sample}
Population: {population}
Selection method: {method}
Domain: {domain}
Context: {context}

Does the sample represent the population being generalized to? Return ONLY valid JSON."""


class SampleBiasService:
    """Detects sample bias — non-representative samples."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        generalization: str,
        *,
        sample: str = "",
        population: str = "",
        method: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect sample bias."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=SAMPLE_BIAS_PROMPT.format(
                generalization=generalization,
                sample=sample or "Not specified",
                population=population or "Not specified",
                method=method or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=SAMPLE_BIAS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "generalization": generalization[:200],
            "bias_present": data.get("bias_present", False),
            "severity": data.get("severity", ""),
            "mismatch": data.get("mismatch", ""),
            "exclusions": data.get("exclusions", ""),
            "sample": data.get("sample", ""),
            "recommendation": data.get("recommendation", ""),
        }
