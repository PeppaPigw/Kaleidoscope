"""Deep paper analysis — LLM-powered innovation, method, and validity analysis.

P2 WS-5: §11 (#81-88) from FeasibilityAnalysis.md

Provides:
- Innovation analysis: compare paper to its references → extract innovation points
- Method/dataset/metric extraction: structured experiment data
- Validity threat analysis: systematic checklist-based review
- Competitive work comparison: find similar methods, compare results
"""

import json
from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.paper import Paper

logger = structlog.get_logger(__name__)

# ─── LLM Prompt Templates ────────────────────────────────────────

INNOVATION_PROMPT = """Analyze this paper and identify its key innovation points compared to prior work.

**Paper title**: {title}
**Abstract**: {abstract}
**Full text (truncated)**: {text}

For each innovation point, provide:
1. The specific claim or contribution
2. What prior approach it improves upon
3. The type of novelty (architectural, methodological, theoretical, empirical, application)
4. Evidence strength (strong/moderate/weak)

Return a JSON array of innovation points:
[{{"claim": "...", "prior_work": "...", "novelty_type": "...", "evidence_strength": "...", "evidence_text": "..."}}]

Return ONLY the JSON array, no other text."""

EXPERIMENT_EXTRACTION_PROMPT = """Extract all experimental results from this paper into a structured format.

**Paper title**: {title}
**Text**: {text}

For each experiment/result, extract:
- method: the model/method name
- dataset: the evaluation dataset
- metric: the evaluation metric name
- value: the metric value (number)
- is_main_result: true if from the main results table, false if ablation/appendix
- comparison: "better"/"worse"/"same" vs previous SOTA if mentioned

Return a JSON array:
[{{"method": "...", "dataset": "...", "metric": "...", "value": ..., "is_main_result": true, "comparison": "better"}}]

Return ONLY the JSON array, no other text."""

VALIDITY_PROMPT = """Analyze this paper for potential validity threats and methodological concerns.

**Paper title**: {title}
**Abstract**: {abstract}
**Text**: {text}

Evaluate against this checklist:
1. Statistical rigor (appropriate tests, effect sizes, confidence intervals)
2. Sample size adequacy
3. Baseline comparisons (fair, recent, strong baselines)
4. Ablation studies (sufficient component analysis)
5. Reproducibility (code/data availability, implementation details)
6. Generalization (tested on multiple datasets/domains)
7. Evaluation metrics (appropriate, comprehensive)
8. Potential confounders

For each concern found, provide:
- category: one of the checklist items above
- description: specific concern
- severity: "low", "medium", "high"
- suggestion: how to address it

Also provide an overall methodology score (0-1).

Return JSON:
{{"threats": [{{"category": "...", "description": "...", "severity": "...", "suggestion": "..."}}], "overall_score": 0.8, "overall_assessment": "..."}}

Return ONLY the JSON, no other text."""

COMPARISON_PROMPT = """Compare these papers on their methods, datasets, and results.

**Paper A**: {paper_a_title}
{paper_a_text}

**Paper B**: {paper_b_title}
{paper_b_text}

Analyze:
1. Shared methods/approaches
2. Unique methods in each paper
3. Result differences on common benchmarks
4. Key architectural/methodological differences
5. Which paper shows stronger results and why

Return JSON:
{{"shared_methods": [...], "unique_to_a": [...], "unique_to_b": [...], "result_comparison": [...], "key_differences": "...", "stronger_paper": "A"/"B"/"tie", "reason": "..."}}

Return ONLY the JSON, no other text."""


class DeepAnalysisService:
    """LLM-powered deep paper analysis."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._llm_client = None

    async def _get_llm_client(self):
        """Lazy-load LLM client."""
        if self._llm_client is None:
            from app.clients.llm_client import LLMClient
            self._llm_client = LLMClient()
        return self._llm_client

    async def _get_paper_text(self, paper_id: str) -> tuple[Paper, str]:
        """Get paper and its text content."""
        result = await self.db.execute(
            select(Paper).where(Paper.id == paper_id, Paper.deleted_at.is_(None))
        )
        paper = result.scalar_one_or_none()
        if not paper:
            raise ValueError(f"Paper not found: {paper_id}")

        # Build text from available sources (prefer full markdown)
        text_parts = []
        if paper.full_text_markdown:
            text = paper.full_text_markdown
        else:
            if paper.abstract:
                text_parts.append(paper.abstract)

            # Use parsed sections if available
            if paper.parsed_sections:
                for section in paper.parsed_sections:
                    if section.get("title"):
                        text_parts.append(f"\n## {section['title']}\n")
                    for para in section.get("paragraphs", []):
                        text_parts.append(para)

            # Fallback to raw metadata
            elif paper.raw_metadata and paper.raw_metadata.get("parsed_sections"):
                for section in paper.raw_metadata["parsed_sections"]:
                    if section.get("title"):
                        text_parts.append(f"\n## {section['title']}\n")
                    for para in section.get("paragraphs", []):
                        text_parts.append(para)

            text = "\n".join(text_parts)

        # Truncate to ~12k chars for LLM context
        if len(text) > 12000:
            text = text[:12000] + "\n[... truncated ...]"

        return paper, text

    async def _call_llm(self, prompt: str) -> str:
        """Call LLM and return response text."""
        client = await self._get_llm_client()
        return await client.complete(prompt=prompt, temperature=0.2)

    async def analyze_innovation(self, paper_id: str) -> dict:
        """
        Analyze a paper's innovation points vs. prior work.

        Returns: {innovation_points: [{claim, prior_work, novelty_type, evidence_strength}]}
        """
        log = logger.bind(paper_id=paper_id, analysis="innovation")
        paper, text = await self._get_paper_text(paper_id)

        prompt = INNOVATION_PROMPT.format(
            title=paper.title,
            abstract=paper.abstract or "",
            text=text,
        )

        try:
            response = await self._call_llm(prompt)
            points = json.loads(response)
            log.info("innovation_analysis_complete", points=len(points))
            return {
                "paper_id": paper_id,
                "title": paper.title,
                "innovation_points": points,
            }
        except (json.JSONDecodeError, Exception) as e:
            log.error("innovation_analysis_failed", error=str(e))
            return {
                "paper_id": paper_id,
                "title": paper.title,
                "innovation_points": [],
                "error": str(e),
            }

    async def extract_experiments(self, paper_id: str) -> dict:
        """
        Extract structured experiment data (methods, datasets, metrics, results).

        Returns: {experiments: [{method, dataset, metric, value, is_main_result}]}
        """
        log = logger.bind(paper_id=paper_id, analysis="experiments")
        paper, text = await self._get_paper_text(paper_id)

        prompt = EXPERIMENT_EXTRACTION_PROMPT.format(
            title=paper.title,
            text=text,
        )

        try:
            response = await self._call_llm(prompt)
            experiments = json.loads(response)
            log.info("experiment_extraction_complete", count=len(experiments))
            return {
                "paper_id": paper_id,
                "title": paper.title,
                "experiments": experiments,
            }
        except (json.JSONDecodeError, Exception) as e:
            log.error("experiment_extraction_failed", error=str(e))
            return {
                "paper_id": paper_id,
                "title": paper.title,
                "experiments": [],
                "error": str(e),
            }

    async def analyze_validity(self, paper_id: str) -> dict:
        """
        Analyze validity threats and methodological rigor.

        Returns: {threats: [...], overall_score: float, overall_assessment: str}
        """
        log = logger.bind(paper_id=paper_id, analysis="validity")
        paper, text = await self._get_paper_text(paper_id)

        prompt = VALIDITY_PROMPT.format(
            title=paper.title,
            abstract=paper.abstract or "",
            text=text,
        )

        try:
            response = await self._call_llm(prompt)
            result = json.loads(response)
            log.info("validity_analysis_complete",
                     threats=len(result.get("threats", [])),
                     score=result.get("overall_score"))
            return {
                "paper_id": paper_id,
                "title": paper.title,
                **result,
            }
        except (json.JSONDecodeError, Exception) as e:
            log.error("validity_analysis_failed", error=str(e))
            return {
                "paper_id": paper_id,
                "title": paper.title,
                "threats": [],
                "overall_score": None,
                "error": str(e),
            }

    async def compare_papers(
        self, paper_id_a: str, paper_id_b: str
    ) -> dict:
        """
        Compare two papers on methods, results, and approaches.

        Returns: {shared_methods, unique_to_a, unique_to_b, result_comparison, ...}
        """
        log = logger.bind(paper_a=paper_id_a, paper_b=paper_id_b)
        paper_a, text_a = await self._get_paper_text(paper_id_a)
        paper_b, text_b = await self._get_paper_text(paper_id_b)

        # Truncate each to ~6k chars for combined context
        if len(text_a) > 6000:
            text_a = text_a[:6000] + "\n[... truncated ...]"
        if len(text_b) > 6000:
            text_b = text_b[:6000] + "\n[... truncated ...]"

        prompt = COMPARISON_PROMPT.format(
            paper_a_title=paper_a.title,
            paper_a_text=text_a,
            paper_b_title=paper_b.title,
            paper_b_text=text_b,
        )

        try:
            response = await self._call_llm(prompt)
            result = json.loads(response)
            log.info("comparison_complete")
            return {
                "paper_a": {"id": paper_id_a, "title": paper_a.title},
                "paper_b": {"id": paper_id_b, "title": paper_b.title},
                **result,
            }
        except (json.JSONDecodeError, Exception) as e:
            log.error("comparison_failed", error=str(e))
            return {
                "paper_a": {"id": paper_id_a, "title": paper_a.title},
                "paper_b": {"id": paper_id_b, "title": paper_b.title},
                "error": str(e),
            }

    async def close(self):
        """Close LLM client resources."""
        if self._llm_client:
            try:
                await self._llm_client.close()
            except Exception:
                pass
