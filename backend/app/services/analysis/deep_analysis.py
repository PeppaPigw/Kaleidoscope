"""Deep paper analysis — LLM-powered innovation, method, and validity analysis.

P2 WS-5: §11 (#81-88) from FeasibilityAnalysis.md

Provides:
- Innovation analysis: compare paper to its references → extract innovation points
- Method/dataset/metric extraction: structured experiment data
- Validity threat analysis: systematic checklist-based review
- Competitive work comparison: find similar methods, compare results
"""

import json
import re
from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.paper import Paper

logger = structlog.get_logger(__name__)

_SPACE_RE = re.compile(r"\s+")
_NON_WORD_RE = re.compile(r"[^a-z0-9]+")
_NUMBER_RE = re.compile(r"-?\d+(?:,\d{3})*(?:\.\d+)?")

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

    def _normalize_label(self, value: Any, fallback: str) -> str:
        if value is None:
            return fallback
        text = _SPACE_RE.sub(" ", str(value)).strip()
        return text or fallback

    def _slugify(self, value: str) -> str:
        text = value.lower().strip()
        slug = _NON_WORD_RE.sub("-", text).strip("-")
        return slug or "unknown"

    def _parse_numeric_value(self, value: Any) -> tuple[float | None, str]:
        if value is None:
            return None, "—"

        if isinstance(value, bool):
            return None, str(value)

        if isinstance(value, (int, float)):
            numeric = float(value)
            display = str(int(numeric)) if numeric.is_integer() else f"{numeric:g}"
            return numeric, display

        text = str(value).strip()
        if not text:
            return None, "—"

        match = _NUMBER_RE.search(text)
        if not match:
            return None, text

        try:
            numeric = float(match.group(0).replace(",", ""))
        except ValueError:
            return None, text
        return numeric, text

    def _infer_higher_is_better(self, metric: str) -> bool:
        text = metric.lower()
        lower_is_better_terms = (
            "error",
            "loss",
            "latency",
            "time",
            "memory",
            "perplexity",
            "mae",
            "mse",
            "rmse",
            "wer",
            "cer",
            "distance",
        )
        return not any(term in text for term in lower_is_better_terms)

    def _record_confidence(self, record: dict[str, Any]) -> float:
        checks = [
            bool(
                record.get("method_name") and record["method_name"] != "Unknown Method"
            ),
            bool(record.get("dataset") and record["dataset"] != "Unspecified"),
            bool(record.get("metric") and record["metric"] != "Unspecified"),
            record.get("value_numeric") is not None,
            bool(record.get("value_display") and record["value_display"] != "—"),
        ]
        return round(sum(1 for ok in checks if ok) / len(checks), 3)

    def _normalize_experiments(
        self,
        paper_id: str,
        paper: Paper,
        experiments: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        records: list[dict[str, Any]] = []
        methods_seen: dict[str, dict[str, Any]] = {}

        for index, item in enumerate(experiments):
            method_name = self._normalize_label(
                item.get("method"),
                "Unknown Method",
            )
            dataset = self._normalize_label(item.get("dataset"), "Unspecified")
            metric = self._normalize_label(item.get("metric"), "Unspecified")
            value_numeric, value_display = self._parse_numeric_value(item.get("value"))
            method_key = self._slugify(method_name)
            dataset_key = self._slugify(dataset)
            metric_key = self._slugify(metric)
            column_key = f"{dataset} · {metric}" if dataset != "Unspecified" else metric

            record = {
                "id": f"{paper_id}:record:{index}",
                "paper_id": paper_id,
                "paper_title": paper.title,
                "paper_year": paper.published_at.year if paper.published_at else None,
                "source": (
                    f"{paper.title} ({paper.published_at.year})"
                    if paper.published_at
                    else paper.title
                ),
                "method_name": method_name,
                "method_key": method_key,
                "dataset": dataset,
                "dataset_key": dataset_key,
                "metric": metric,
                "metric_key": metric_key,
                "column_key": column_key,
                "value_raw": item.get("value"),
                "value_display": value_display,
                "value_numeric": value_numeric,
                "is_main_result": bool(item.get("is_main_result", False)),
                "comparison": item.get("comparison"),
                "split": item.get("split"),
                "higher_is_better": self._infer_higher_is_better(metric),
                "comparable": dataset != "Unspecified" and metric != "Unspecified",
            }
            record["confidence"] = self._record_confidence(record)
            records.append(record)

            if method_key not in methods_seen:
                methods_seen[method_key] = {
                    "id": f"{paper_id}:method:{method_key}",
                    "name": method_name,
                    "paper_id": paper_id,
                    "paper_title": paper.title,
                    "datasets": set(),
                    "metrics": set(),
                    "record_count": 0,
                    "main_result_count": 0,
                }

            method_meta = methods_seen[method_key]
            if dataset != "Unspecified":
                method_meta["datasets"].add(dataset)
            if metric != "Unspecified":
                method_meta["metrics"].add(metric)
            method_meta["record_count"] += 1
            if record["is_main_result"]:
                method_meta["main_result_count"] += 1

        methods = []
        for meta in methods_seen.values():
            methods.append(
                {
                    **meta,
                    "datasets": sorted(meta["datasets"]),
                    "metrics": sorted(meta["metrics"]),
                }
            )
        methods.sort(key=lambda item: item["name"].lower())
        return records, methods

    def _build_matrix_ready(
        self,
        records: list[dict[str, Any]],
    ) -> dict[str, Any]:
        if not records:
            return {
                "columns": [],
                "metric_names": [],
                "rows": [],
                "best_by_column": {},
            }

        column_meta: dict[str, dict[str, Any]] = {}
        rows_map: dict[str, dict[str, Any]] = {}
        best_candidates: dict[str, tuple[str, float, bool]] = {}

        for record in records:
            column_key = record["column_key"]
            column_meta.setdefault(
                column_key,
                {
                    "key": column_key,
                    "dataset": record["dataset"],
                    "metric": record["metric"],
                    "higher_is_better": record["higher_is_better"],
                },
            )

            row_id = f"{record['paper_id']}:{record['method_key']}"
            row = rows_map.setdefault(
                row_id,
                {
                    "id": row_id,
                    "paper_id": record["paper_id"],
                    "paper_title": record["paper_title"],
                    "method": record["method_name"],
                    "source": record["source"],
                    "metrics": {},
                    "numeric_metrics": {},
                    "best_metrics": [],
                    "is_best": False,
                    "record_ids": [],
                    "confidence_values": [],
                },
            )
            row["metrics"][column_key] = record["value_display"]
            row["numeric_metrics"][column_key] = record.get("value_numeric")
            row["record_ids"].append(record["id"])
            if isinstance(record.get("confidence"), (int, float)):
                row["confidence_values"].append(float(record["confidence"]))

            numeric_value = record.get("value_numeric")
            if numeric_value is None:
                continue

            higher_is_better = record.get("higher_is_better", True)
            current_best = best_candidates.get(column_key)
            if current_best is None:
                best_candidates[column_key] = (
                    row_id,
                    float(numeric_value),
                    higher_is_better,
                )
                continue

            _, current_value, current_higher_is_better = current_best
            if current_higher_is_better:
                if float(numeric_value) > current_value:
                    best_candidates[column_key] = (
                        row_id,
                        float(numeric_value),
                        higher_is_better,
                    )
            elif float(numeric_value) < current_value:
                best_candidates[column_key] = (
                    row_id,
                    float(numeric_value),
                    higher_is_better,
                )

        best_by_column = {key: value[0] for key, value in best_candidates.items()}
        rows = []
        for row in rows_map.values():
            confidence_values = row.pop("confidence_values")
            row["confidence"] = (
                round(sum(confidence_values) / len(confidence_values), 3)
                if confidence_values
                else None
            )
            row["best_metrics"] = sorted(
                [
                    column_key
                    for column_key, row_id in best_by_column.items()
                    if row_id == row["id"]
                ]
            )
            row["is_best"] = bool(row["best_metrics"])
            rows.append(row)

        rows.sort(key=lambda item: item["method"].lower())
        columns = sorted(
            column_meta.values(),
            key=lambda item: (
                str(item.get("dataset") or "").lower(),
                str(item.get("metric") or "").lower(),
            ),
        )

        return {
            "columns": columns,
            "metric_names": [column["key"] for column in columns],
            "rows": rows,
            "best_by_column": best_by_column,
        }

    def _build_coverage(
        self,
        records: list[dict[str, Any]],
        methods: list[dict[str, Any]],
    ) -> dict[str, Any]:
        total = len(records)
        if total == 0:
            return {
                "total_records": 0,
                "main_result_records": 0,
                "methods": 0,
                "datasets": 0,
                "metrics": 0,
                "field_completion": {
                    "method": 0.0,
                    "dataset": 0.0,
                    "metric": 0.0,
                    "numeric_value": 0.0,
                },
                "overall": 0.0,
            }

        with_method = sum(
            1
            for record in records
            if record.get("method_name") and record["method_name"] != "Unknown Method"
        )
        with_dataset = sum(
            1
            for record in records
            if record.get("dataset") and record["dataset"] != "Unspecified"
        )
        with_metric = sum(
            1
            for record in records
            if record.get("metric") and record["metric"] != "Unspecified"
        )
        with_numeric = sum(
            1 for record in records if record.get("value_numeric") is not None
        )
        field_completion = {
            "method": round(with_method / total, 3),
            "dataset": round(with_dataset / total, 3),
            "metric": round(with_metric / total, 3),
            "numeric_value": round(with_numeric / total, 3),
        }
        overall = round(sum(field_completion.values()) / len(field_completion), 3)

        return {
            "total_records": total,
            "main_result_records": sum(
                1 for record in records if record.get("is_main_result")
            ),
            "methods": len(methods),
            "datasets": len(
                {
                    record["dataset"]
                    for record in records
                    if record.get("dataset") and record["dataset"] != "Unspecified"
                }
            ),
            "metrics": len(
                {
                    record["metric"]
                    for record in records
                    if record.get("metric") and record["metric"] != "Unspecified"
                }
            ),
            "field_completion": field_completion,
            "overall": overall,
        }

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
            records, methods = self._normalize_experiments(
                paper_id=paper_id,
                paper=paper,
                experiments=experiments,
            )
            matrix_ready = self._build_matrix_ready(records)
            coverage = self._build_coverage(records, methods)
            confidence = {
                "overall": coverage["overall"],
                "records": {record["id"]: record["confidence"] for record in records},
            }
            log.info("experiment_extraction_complete", count=len(experiments))
            return {
                "paper_id": paper_id,
                "title": paper.title,
                "paper": {
                    "id": paper_id,
                    "title": paper.title,
                    "year": paper.published_at.year if paper.published_at else None,
                    "source": (
                        f"{paper.title} ({paper.published_at.year})"
                        if paper.published_at
                        else paper.title
                    ),
                },
                "experiments": experiments,
                "methods": methods,
                "records": records,
                "matrix_ready": matrix_ready,
                "coverage": coverage,
                "confidence": confidence,
            }
        except (json.JSONDecodeError, Exception) as e:
            log.error("experiment_extraction_failed", error=str(e))
            return {
                "paper_id": paper_id,
                "title": paper.title,
                "experiments": [],
                "methods": [],
                "records": [],
                "matrix_ready": {
                    "columns": [],
                    "metric_names": [],
                    "rows": [],
                    "best_by_column": {},
                },
                "coverage": self._build_coverage([], []),
                "confidence": {"overall": 0.0, "records": {}},
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
            log.info(
                "validity_analysis_complete",
                threats=len(result.get("threats", [])),
                score=result.get("overall_score"),
            )
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

    async def compare_papers(self, paper_id_a: str, paper_id_b: str) -> dict:
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
