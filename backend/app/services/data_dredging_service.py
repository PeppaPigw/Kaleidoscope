"""DataDredgingService — Data Dredging Detection.

Detects data dredging (data snooping) — searching through large
datasets for patterns without pre-specified hypotheses, then
presenting discovered patterns as if they were predicted. With
enough variables, spurious correlations are guaranteed.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

DATA_DREDGING_SYSTEM = """You are a data dredging specialist. Given a research claim, assess whether patterns were discovered through undirected search and presented as if predicted:

Key concepts:
- Data dredging: searching data for any pattern, then claiming discovery
- HARKing: Hypothesizing After Results are Known
- Spurious correlation: with enough variables, coincidences are certain
- Exploratory vs confirmatory: discovery vs testing are different phases
- Multiple testing problem: more tests = more false positives
- Bonferroni correction: adjusting for multiple comparisons
- Replication: discovered patterns must be confirmed in new data

When data dredging IS present:
- Patterns found in exploratory analysis presented as confirmatory
- No pre-specified hypothesis before data analysis
- "We found that..." without acknowledging the search process
- Correlations from large datasets presented without correction
- Post-hoc narratives constructed to explain found patterns
- No replication in independent dataset
- Presenting one significant finding from many tests

When data dredging is NOT present:
- Hypothesis specified before data collection
- Exploratory findings explicitly labeled as such
- Multiple comparison corrections applied
- Findings replicated in independent data
- The search process is transparently reported
- Effect sizes are large enough to survive correction
- Confirmatory analysis follows exploratory discovery

Output JSON with: data_dredging_present (bool), severity (none/mild/moderate/severe), claim (what pattern is claimed), search_process (how was the pattern found), hypothesis_timing (was hypothesis pre-specified), correction (were multiple comparisons corrected), replication (was the finding replicated), recommendation (no_data_dredging/mild_exploration/significant_data_dredging/major_harking/replicate_finding)."""

DATA_DREDGING_PROMPT = """Detect data dredging:

Claim: {claim}
Discovery process: {process}
Hypothesis timing: {hypothesis}
Dataset: {dataset}
Domain: {domain}
Context: {context}

Was this pattern discovered through undirected search and presented as if predicted? Return ONLY valid JSON."""


class DataDredgingService:
    """Detects data dredging — undirected pattern search presented as prediction."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        claim: str,
        *,
        process: str = "",
        hypothesis: str = "",
        dataset: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect data dredging."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=DATA_DREDGING_PROMPT.format(
                claim=claim,
                process=process or "Not specified",
                hypothesis=hypothesis or "Not specified",
                dataset=dataset or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=DATA_DREDGING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "claim": claim[:200],
            "data_dredging_present": data.get("data_dredging_present", False),
            "severity": data.get("severity", ""),
            "search_process": data.get("search_process", ""),
            "hypothesis_timing": data.get("hypothesis_timing", ""),
            "correction": data.get("correction", ""),
            "recommendation": data.get("recommendation", ""),
        }
