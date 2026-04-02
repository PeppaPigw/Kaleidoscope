"""Figure/table intelligence service — extraction, classification, cross-paper aggregation.

P3 WS-3: §19 (#153-164) from FeasibilityAnalysis.md

MVP scope:
- Extract figure/table metadata from parsed paper
- Classify figures (architecture, results, comparison, illustration)
- Link claims to referenced figures/tables
- Cross-paper result table aggregation

Deferred: CLIP-based image search, supplementary material deep parsing.
"""

import json

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.paper import Paper

logger = structlog.get_logger(__name__)

FIGURE_ANALYSIS_PROMPT = """Analyze the figures and tables referenced in this paper.

**Title**: {title}
**Text**: {text}

For each figure/table mentioned in the text, extract:
1. ref: the reference ("Figure 1", "Table 2", etc.)
2. caption: the caption text if available
3. content_type: one of [architecture, results_chart, results_table, comparison, ablation, illustration, data_distribution, workflow, other]
4. key_finding: what does this figure/table show? (1 sentence)
5. related_claims: which claims does it support? (list of claim texts)

Return JSON array:
[{{
    "ref": "Figure 1",
    "caption": "...",
    "content_type": "architecture",
    "key_finding": "...",
    "related_claims": ["..."]
}}]

Return ONLY the JSON array."""

CROSS_PAPER_TABLE_PROMPT = """Create a unified comparison table from results reported in these papers.

{papers_section}

Rules:
1. Find the most common evaluation datasets and metrics across papers
2. Extract reported numbers for each method on each dataset/metric
3. Normalize metric names (e.g., "Acc" = "Accuracy")
4. Flag any non-comparable results (different splits, preprocessing)

Return JSON:
{{
    "datasets": ["..."],
    "metrics": ["..."],
    "results": [{{
        "paper": "...",
        "method": "...",
        "results": {{"dataset_name": {{"metric_name": value}}}}
    }}],
    "notes": ["any caveats about comparability"]
}}

Return ONLY the JSON."""


class FigureTableService:
    """Intelligence for figures, tables, and visual elements."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._llm_client = None

    async def _get_llm(self):
        if self._llm_client is None:
            from app.clients.llm_client import LLMClient

            self._llm_client = LLMClient()
        return self._llm_client

    async def analyze_figures(self, paper_id: str) -> dict:
        """
        Analyze all figures/tables in a paper.

        Classifies each by type and extracts key findings.
        """
        result = await self.db.execute(
            select(Paper).where(Paper.id == paper_id, Paper.deleted_at.is_(None))
        )
        paper = result.scalar_one_or_none()
        if not paper:
            return {"error": "Paper not found"}

        # Build text from paper
        parts = [paper.abstract or ""]
        if paper.parsed_sections:
            for sec in paper.parsed_sections:
                if sec.get("title"):
                    parts.append(f"\n## {sec['title']}\n")
                for p in sec.get("paragraphs", []):
                    parts.append(p)
        text = "\n".join(parts)
        if len(text) > 12000:
            text = text[:12000] + "\n[... truncated ...]"

        llm = await self._get_llm()
        prompt = FIGURE_ANALYSIS_PROMPT.format(
            title=paper.title,
            text=text,
        )

        try:
            response = await llm.complete(prompt=prompt, temperature=0.2)
            figures = json.loads(response)

            # Persist to paper's parsed_figures field
            paper.parsed_figures = figures
            await self.db.flush()

            return {
                "paper_id": paper_id,
                "title": paper.title,
                "figures": figures,
            }
        except Exception as e:
            logger.error("figure_analysis_failed", error=str(e))
            return {"paper_id": paper_id, "figures": [], "error": str(e)}

    async def get_figures(self, paper_id: str) -> dict:
        """Get previously extracted figures/tables for a paper."""
        result = await self.db.execute(
            select(Paper).where(Paper.id == paper_id, Paper.deleted_at.is_(None))
        )
        paper = result.scalar_one_or_none()
        if not paper:
            return {"error": "Paper not found"}

        return {
            "paper_id": paper_id,
            "title": paper.title,
            "figures": paper.parsed_figures or [],
        }

    async def aggregate_results(self, paper_ids: list[str]) -> dict:
        """
        Aggregate experimental results from multiple papers into a unified table.

        Cross-paper comparison with normalization and caveats.
        """
        result = await self.db.execute(
            select(Paper).where(Paper.id.in_(paper_ids), Paper.deleted_at.is_(None))
        )
        papers = list(result.scalars().all())
        if not papers:
            return {"error": "No papers found"}

        # Format papers for prompt
        sections = []
        for i, p in enumerate(papers, 1):
            block = f"**[{i}] {p.title}**\n"
            if p.abstract:
                block += f"Abstract: {p.abstract[:400]}\n"
            # Include parsed_figures if available (contains results tables)
            if p.parsed_figures:
                tables = [
                    f
                    for f in p.parsed_figures
                    if f.get("content_type")
                    in ("results_table", "comparison", "ablation")
                ]
                if tables:
                    block += f"Results tables: {json.dumps(tables[:3])}\n"
            sections.append(block)

        llm = await self._get_llm()
        prompt = CROSS_PAPER_TABLE_PROMPT.format(
            papers_section="\n".join(sections),
        )

        try:
            response = await llm.complete(
                prompt=prompt, temperature=0.2, max_tokens=4096
            )
            result_table = json.loads(response)
            return {
                "paper_count": len(papers),
                **result_table,
            }
        except Exception as e:
            logger.error("result_aggregation_failed", error=str(e))
            return {"error": str(e)}

    async def close(self):
        if self._llm_client:
            try:
                await self._llm_client.close()
            except Exception:
                pass
