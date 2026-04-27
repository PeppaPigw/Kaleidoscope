"""Evidence Lab service — cross-paper method and result aggregation.

Builds a thin orchestration layer on top of existing analysis, vector search,
paper QA, and local RAG capabilities so the Evidence Lab page can render a
real comparison matrix across a paper subset.
"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.collection import DEFAULT_USER_ID
from app.models.paper import Paper
from app.services.analysis.deep_analysis import DeepAnalysisService
from app.services.collection_service import CollectionService
from app.services.extraction.paper_qa_service import PaperQAService
from app.services.local_rag_service import LocalRAGService
from app.services.vector_search_service import VectorSearchService

logger = structlog.get_logger(__name__)


class EvidenceLabService:
    """Aggregate methods, results, and supporting evidence across papers."""

    READY_STATUSES = ("parsed", "indexed", "index_partial")
    DEFAULT_SCOPE_LIMIT = 8
    MAX_SCOPE_LIMIT = 24
    VECTOR_MIN_SIMILARITY = 0.12
    PAPER_QA_PROMPT = (
        "Extract the main method, datasets, evaluation metrics, baselines, "
        "and strongest quantitative results from this paper. Focus on the "
        "research question: {research_question}"
    )
    VECTOR_PROMPT_SUFFIX = (
        "Focus on the method, datasets, evaluation metrics, baselines, and "
        "the strongest numerical results."
    )

    def __init__(
        self,
        db: AsyncSession,
        user_id: str = DEFAULT_USER_ID,
    ) -> None:
        self.db = db
        self.user_id = user_id
        self.deep_analysis = DeepAnalysisService(db)
        self.vector_search = VectorSearchService(db)
        self.collection_service = CollectionService(db, user_id)
        self.local_rag = LocalRAGService(db)
        self.paper_qa = PaperQAService(db)

    async def analyze_methods(
        self,
        paper_ids: list[str] | None = None,
        collection_id: str | None = None,
        research_question: str | None = None,
        filters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Analyze methods across a scope of papers and build matrix-ready data."""
        warnings: list[str] = []
        filters = filters or {}

        papers, scope = await self._resolve_scope(
            paper_ids=paper_ids,
            collection_id=collection_id,
            warnings=warnings,
        )
        if not papers:
            return {
                "scope": scope,
                "research_question": research_question or "",
                "papers": [],
                "methods": [],
                "datasets": [],
                "metrics": [],
                "matrix": {
                    "columns": [],
                    "metric_names": [],
                    "rows": [],
                    "best_by_column": {},
                },
                "filters_applied": filters,
                "cross_paper_summary": None,
                "evidence": {"scope_hits": [], "paper_hits": {}},
                "contradiction_candidates": [],
                "coverage": {"overall": 0.0, "papers_total": 0},
                "warnings": warnings or ["No analysis-ready papers found for scope."],
            }

        selected_ids = [str(paper.id) for paper in papers]
        question = self._resolve_research_question(research_question, papers)

        scope_hits = await self._get_scope_vector_hits(
            paper_ids=selected_ids,
            research_question=question,
            warnings=warnings,
        )
        cross_paper_summary = await self._get_cross_paper_summary(
            collection_id=collection_id,
            research_question=question,
            warnings=warnings,
        )

        paper_payloads = await asyncio.gather(
            *(self._analyze_single_paper(paper, question) for paper in papers)
        )

        all_records: list[dict[str, Any]] = []
        paper_hits: dict[str, list[dict[str, Any]]] = {}
        papers_output: list[dict[str, Any]] = []
        for payload in paper_payloads:
            warnings.extend(payload["warnings"])
            paper_id = payload["paper"]["id"]
            paper_hits[paper_id] = payload["vector_hits"]
            all_records.extend(payload["extract_result"].get("records", []))
            papers_output.append(
                {
                    **payload["paper"],
                    "coverage": payload["extract_result"].get("coverage", {}),
                    "confidence": payload["extract_result"].get("confidence", {}),
                    "record_count": len(payload["extract_result"].get("records", [])),
                    "qa_support": payload["qa_support"],
                }
            )

        filtered_records = self._apply_filters(all_records, filters)
        if filters.get("main_results_only") and not filtered_records:
            warnings.append("Filters removed all main-result records.")
        elif not filtered_records and all_records:
            warnings.append("Filters removed all comparable records.")

        matrix = self._build_matrix(filtered_records)
        methods = self._build_method_summaries(matrix["rows"], filtered_records)
        contradiction_candidates = self._build_contradiction_candidates(
            filtered_records
        )

        unique_datasets = sorted(
            {
                record["dataset"]
                for record in filtered_records
                if record.get("dataset") and record["dataset"] != "Unspecified"
            }
        )
        unique_metrics = sorted(
            {
                record["metric"]
                for record in filtered_records
                if record.get("metric") and record["metric"] != "Unspecified"
            }
        )

        coverage = self._build_scope_coverage(
            papers_output=papers_output,
            all_records=all_records,
            filtered_records=filtered_records,
            scope_hits=scope_hits,
        )

        return {
            "scope": scope,
            "research_question": question,
            "papers": papers_output,
            "methods": methods,
            "datasets": unique_datasets,
            "metrics": unique_metrics,
            "matrix": matrix,
            "filters_applied": filters,
            "cross_paper_summary": cross_paper_summary,
            "evidence": {
                "scope_hits": scope_hits,
                "paper_hits": paper_hits,
            },
            "contradiction_candidates": contradiction_candidates,
            "coverage": coverage,
            "warnings": self._dedupe_preserve_order(warnings),
        }

    async def _resolve_scope(
        self,
        paper_ids: list[str] | None,
        collection_id: str | None,
        warnings: list[str],
    ) -> tuple[list[Paper], dict[str, Any]]:
        if paper_ids:
            deduped = self._dedupe_preserve_order(
                [paper_id for paper_id in paper_ids if paper_id]
            )
            papers = await self._load_papers(deduped)
            papers = self._preserve_requested_order(papers, deduped)
            ready, skipped = self._split_analysis_ready_papers(papers)
            if skipped:
                warnings.append(
                    f"Skipped {len(skipped)} paper(s) without parsed/full-text content."
                )
            return ready, {
                "type": "paper_ids",
                "paper_ids": [str(p.id) for p in ready],
                "paper_count": len(ready),
                "requested_count": len(deduped),
                "collection_id": None,
                "default_scope": False,
            }

        if collection_id:
            collection_rows = await self.collection_service.get_collection_papers(
                collection_id,
                limit=self.MAX_SCOPE_LIMIT + 1,
            )
            collection_paper_ids = [
                str(row["paper_id"]) for row in collection_rows if row.get("paper_id")
            ]
            truncated = len(collection_paper_ids) > self.MAX_SCOPE_LIMIT
            if truncated:
                collection_paper_ids = collection_paper_ids[: self.MAX_SCOPE_LIMIT]
                warnings.append(
                    f"Collection scope truncated to the first {self.MAX_SCOPE_LIMIT} papers for real-time analysis."
                )

            papers = await self._load_papers(collection_paper_ids)
            papers = self._preserve_requested_order(papers, collection_paper_ids)
            ready, skipped = self._split_analysis_ready_papers(papers)
            if skipped:
                warnings.append(
                    f"Skipped {len(skipped)} collection paper(s) without parsed/full-text content."
                )
            return ready, {
                "type": "collection",
                "paper_ids": [str(p.id) for p in ready],
                "paper_count": len(ready),
                "requested_count": len(collection_paper_ids),
                "collection_id": collection_id,
                "default_scope": False,
            }

        recent_papers = await self._get_recent_analysis_ready_papers(
            limit=self.DEFAULT_SCOPE_LIMIT
        )
        return recent_papers, {
            "type": "recent",
            "paper_ids": [str(p.id) for p in recent_papers],
            "paper_count": len(recent_papers),
            "requested_count": len(recent_papers),
            "collection_id": None,
            "default_scope": True,
        }

    async def _analyze_single_paper(
        self,
        paper: Paper,
        research_question: str,
    ) -> dict[str, Any]:
        paper_id = str(paper.id)
        log = logger.bind(paper_id=paper_id, stage="evidence_lab_single")
        warnings: list[str] = []

        extract_result = await self.deep_analysis.extract_experiments(paper_id)
        if extract_result.get("error"):
            warnings.append(
                f"Experiment extraction failed for '{paper.title}': {extract_result['error']}"
            )

        vector_hits = await self._get_paper_vector_hits(
            paper_id=paper_id,
            research_question=research_question,
            warnings=warnings,
        )

        qa_support: dict[str, Any] | None = None
        if self._needs_qa_support(extract_result):
            qa_support = await self._get_paper_qa_support(
                paper_id=paper_id,
                research_question=research_question,
                warnings=warnings,
            )

        log.info(
            "paper_analysis_complete",
            records=len(extract_result.get("records", [])),
            vector_hits=len(vector_hits),
            qa_used=qa_support is not None,
        )

        return {
            "paper": self._serialize_paper(paper),
            "extract_result": extract_result,
            "vector_hits": vector_hits,
            "qa_support": qa_support,
            "warnings": warnings,
        }

    async def _get_scope_vector_hits(
        self,
        paper_ids: list[str],
        research_question: str,
        warnings: list[str],
    ) -> list[dict[str, Any]]:
        if not paper_ids:
            return []

        query = f"{research_question}\n{self.VECTOR_PROMPT_SUFFIX}"
        try:
            hits = await self.vector_search.search_by_text(
                query_text=query,
                paper_ids=paper_ids,
                top_k=8,
                min_similarity=self.VECTOR_MIN_SIMILARITY,
            )
        except Exception as exc:
            warnings.append(f"Vector search unavailable for scope evidence: {exc}")
            return []

        return [self._format_vector_hit(hit) for hit in hits]

    async def _get_paper_vector_hits(
        self,
        paper_id: str,
        research_question: str,
        warnings: list[str],
    ) -> list[dict[str, Any]]:
        query = f"{research_question}\n{self.VECTOR_PROMPT_SUFFIX}"
        try:
            hits = await self.vector_search.search_by_text(
                query_text=query,
                paper_ids=[paper_id],
                top_k=4,
                min_similarity=self.VECTOR_MIN_SIMILARITY,
            )
        except Exception as exc:
            warnings.append(f"Vector search unavailable for paper {paper_id}: {exc}")
            return []
        return [self._format_vector_hit(hit) for hit in hits]

    async def _get_paper_qa_support(
        self,
        paper_id: str,
        research_question: str,
        warnings: list[str],
    ) -> dict[str, Any] | None:
        try:
            status = await self.paper_qa.get_status(paper_id)
        except Exception as exc:
            warnings.append(f"Paper QA status unavailable for {paper_id}: {exc}")
            return None

        qa_result: dict[str, Any] = {
            "status": status.get("status", "unknown"),
            "queued": False,
            "answer": None,
            "sources": [],
        }

        if status.get("status") != "completed":
            if status.get("status") in {"not_started", "failed"}:
                try:
                    await self.paper_qa.prepare(paper_id)
                    qa_result["queued"] = True
                    warnings.append(
                        f"Paper QA embeddings queued for {paper_id}; QA support will improve after indexing completes."
                    )
                except Exception as exc:
                    warnings.append(f"Paper QA prepare failed for {paper_id}: {exc}")
            return qa_result

        try:
            answer = await self.paper_qa.ask(
                paper_id=paper_id,
                question=self.PAPER_QA_PROMPT.format(
                    research_question=research_question
                ),
            )
        except Exception as exc:
            warnings.append(f"Paper QA ask failed for {paper_id}: {exc}")
            return qa_result

        qa_result.update(
            {
                "status": "completed",
                "answer": answer.get("answer"),
                "sources": answer.get("sources", []),
                "latency_ms": answer.get("latency_ms"),
            }
        )
        return qa_result

    async def _get_cross_paper_summary(
        self,
        collection_id: str | None,
        research_question: str,
        warnings: list[str],
    ) -> dict[str, Any] | None:
        if not collection_id:
            return None

        try:
            result = await self.local_rag.ask_collection(
                collection_id=collection_id,
                question=research_question,
                top_k=8,
                min_similarity=0.2,
            )
        except Exception as exc:
            warnings.append(f"Collection-level local RAG failed: {exc}")
            return None

        return {
            "answer": result.get("answer"),
            "sources": result.get("sources", []),
            "chunks_found": result.get("chunks_found", 0),
            "latency_ms": result.get("latency_ms"),
        }

    async def _load_papers(self, paper_ids: list[str]) -> list[Paper]:
        if not paper_ids:
            return []
        result = await self.db.execute(
            select(Paper).where(Paper.id.in_(paper_ids), Paper.deleted_at.is_(None))
        )
        return list(result.scalars().all())

    async def _get_recent_analysis_ready_papers(self, limit: int) -> list[Paper]:
        query = (
            select(Paper)
            .where(
                Paper.deleted_at.is_(None),
                Paper.ingestion_status.in_(self.READY_STATUSES),
            )
            .order_by(Paper.created_at.desc())
            .limit(limit * 3)
        )
        result = await self.db.execute(query)
        papers = list(result.scalars().all())
        ready, _ = self._split_analysis_ready_papers(papers)
        return ready[:limit]

    def _split_analysis_ready_papers(
        self,
        papers: list[Paper],
    ) -> tuple[list[Paper], list[Paper]]:
        ready: list[Paper] = []
        skipped: list[Paper] = []
        for paper in papers:
            if self._paper_is_analysis_ready(paper):
                ready.append(paper)
            else:
                skipped.append(paper)
        return ready, skipped

    def _paper_is_analysis_ready(self, paper: Paper) -> bool:
        raw_sections = (paper.raw_metadata or {}).get("parsed_sections")
        return bool(
            paper.full_text_markdown
            or paper.parsed_sections
            or raw_sections
            or paper.abstract
        )

    def _resolve_research_question(
        self,
        research_question: str | None,
        papers: list[Paper],
    ) -> str:
        if research_question and research_question.strip():
            return research_question.strip()

        keywords: list[str] = []
        for paper in papers:
            if isinstance(paper.keywords, list):
                keywords.extend(
                    str(item).strip() for item in paper.keywords[:2] if item
                )

        if keywords:
            unique_keywords = self._dedupe_preserve_order(keywords)[:3]
            return (
                "How do the selected papers differ in methods and results for "
                + ", ".join(unique_keywords)
                + "?"
            )

        return "How do the selected papers differ in methods, datasets, metrics, and results?"

    def _apply_filters(
        self,
        records: list[dict[str, Any]],
        filters: dict[str, Any],
    ) -> list[dict[str, Any]]:
        datasets = {
            str(dataset).strip().lower()
            for dataset in filters.get("datasets", []) or []
            if str(dataset).strip()
        }
        metrics = {
            str(metric).strip().lower()
            for metric in filters.get("metrics", []) or []
            if str(metric).strip()
        }
        main_only = bool(filters.get("main_results_only"))
        include_uncomparable = bool(filters.get("include_uncomparable"))

        filtered: list[dict[str, Any]] = []
        for record in records:
            dataset = str(record.get("dataset") or "").strip().lower()
            metric = str(record.get("metric") or "").strip().lower()
            if datasets and dataset not in datasets:
                continue
            if metrics and metric not in metrics:
                continue
            if main_only and not record.get("is_main_result"):
                continue
            if not include_uncomparable and not record.get("comparable", True):
                continue
            filtered.append(record)
        return filtered

    def _build_matrix(self, records: list[dict[str, Any]]) -> dict[str, Any]:
        if not records:
            return {
                "columns": [],
                "metric_names": [],
                "rows": [],
                "best_by_column": {},
            }

        column_meta: dict[str, dict[str, Any]] = {}
        grouped: dict[tuple[str, str], dict[str, Any]] = {}
        best_candidates: dict[str, tuple[str, float, bool]] = {}

        for record in records:
            column_key = record["column_key"]
            column_meta.setdefault(
                column_key,
                {
                    "key": column_key,
                    "dataset": record.get("dataset"),
                    "metric": record.get("metric"),
                    "higher_is_better": record.get("higher_is_better", True),
                },
            )

            row_key = (record["paper_id"], record["method_key"])
            row_id = f"{record['paper_id']}:{record['method_key']}"
            row = grouped.setdefault(
                row_key,
                {
                    "id": row_id,
                    "paper_id": record["paper_id"],
                    "paper_title": record["paper_title"],
                    "method": record["method_name"],
                    "source": record["source"],
                    "metrics": {},
                    "numeric_metrics": {},
                    "datasets": set(),
                    "columns": set(),
                    "confidence_values": [],
                    "record_ids": [],
                    "best_metrics": [],
                },
            )
            row["metrics"][column_key] = record["value_display"]
            row["numeric_metrics"][column_key] = record.get("value_numeric")
            if record.get("dataset"):
                row["datasets"].add(record["dataset"])
            row["columns"].add(column_key)
            row["record_ids"].append(record["id"])
            if isinstance(record.get("confidence"), (int, float)):
                row["confidence_values"].append(float(record["confidence"]))

            numeric_value = record.get("value_numeric")
            if numeric_value is None:
                continue

            higher_is_better = record.get("higher_is_better", True)
            existing = best_candidates.get(column_key)
            if existing is None:
                best_candidates[column_key] = (
                    row_id,
                    float(numeric_value),
                    higher_is_better,
                )
                continue

            _, existing_value, existing_higher_is_better = existing
            if existing_higher_is_better:
                if float(numeric_value) > existing_value:
                    best_candidates[column_key] = (
                        row_id,
                        float(numeric_value),
                        higher_is_better,
                    )
            elif float(numeric_value) < existing_value:
                best_candidates[column_key] = (
                    row_id,
                    float(numeric_value),
                    higher_is_better,
                )

        best_by_column = {key: value[0] for key, value in best_candidates.items()}

        rows: list[dict[str, Any]] = []
        for row in grouped.values():
            row["datasets"] = sorted(row["datasets"])
            row["columns"] = sorted(row["columns"])
            confidence_values = row.pop("confidence_values")
            row["confidence"] = (
                round(sum(confidence_values) / len(confidence_values), 3)
                if confidence_values
                else None
            )
            row["best_metrics"] = sorted(
                [
                    column_key
                    for column_key, best_row_id in best_by_column.items()
                    if best_row_id == row["id"]
                ]
            )
            row["is_best"] = bool(row["best_metrics"])
            rows.append(row)

        rows.sort(
            key=lambda item: (item["paper_title"].lower(), item["method"].lower())
        )

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

    def _build_method_summaries(
        self,
        rows: list[dict[str, Any]],
        records: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        record_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for record in records:
            row_id = f"{record['paper_id']}:{record['method_key']}"
            record_groups[row_id].append(record)

        summaries: list[dict[str, Any]] = []
        for row in rows:
            row_records = record_groups.get(row["id"], [])
            summaries.append(
                {
                    "id": row["id"],
                    "paper_id": row["paper_id"],
                    "paper_title": row["paper_title"],
                    "method_name": row["method"],
                    "source": row["source"],
                    "datasets": row["datasets"],
                    "metrics": sorted(
                        {
                            record["metric"]
                            for record in row_records
                            if record.get("metric")
                        }
                    ),
                    "main_result_count": sum(
                        1 for record in row_records if record.get("is_main_result")
                    ),
                    "record_count": len(row_records),
                    "confidence": row.get("confidence"),
                    "best_metrics": row.get("best_metrics", []),
                }
            )
        return summaries

    def _build_contradiction_candidates(
        self,
        records: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        for record in records:
            dataset = record.get("dataset") or "Unspecified"
            metric = record.get("metric") or "Unspecified"
            grouped[(dataset, metric)].append(record)

        candidates: list[dict[str, Any]] = []
        for (dataset, metric), group in grouped.items():
            comparisons = {
                str(record.get("comparison") or "").strip().lower()
                for record in group
                if record.get("comparison")
            }
            if "better" in comparisons and "worse" in comparisons:
                candidates.append(
                    {
                        "dataset": dataset,
                        "metric": metric,
                        "methods": sorted(
                            {
                                f"{record['paper_title']} — {record['method_name']}"
                                for record in group
                            }
                        ),
                        "reason": "Reported comparison directions disagree across papers.",
                    }
                )
        return candidates[:8]

    def _build_scope_coverage(
        self,
        papers_output: list[dict[str, Any]],
        all_records: list[dict[str, Any]],
        filtered_records: list[dict[str, Any]],
        scope_hits: list[dict[str, Any]],
    ) -> dict[str, Any]:
        paper_confidences = [
            paper["confidence"].get("overall")
            for paper in papers_output
            if isinstance(paper.get("confidence", {}).get("overall"), (int, float))
        ]
        overall = (
            round(sum(paper_confidences) / len(paper_confidences), 3)
            if paper_confidences
            else 0.0
        )
        return {
            "overall": overall,
            "papers_total": len(papers_output),
            "papers_with_records": sum(
                1 for paper in papers_output if paper["record_count"]
            ),
            "papers_with_scope_hits": len({hit["paper_id"] for hit in scope_hits}),
            "records_total": len(all_records),
            "records_after_filters": len(filtered_records),
        }

    def _needs_qa_support(self, extract_result: dict[str, Any]) -> bool:
        records = extract_result.get("records", [])
        confidence = extract_result.get("confidence", {})
        overall = confidence.get("overall")
        return (
            not records
            or len(records) < 2
            or not isinstance(overall, (int, float))
            or overall < 0.65
        )

    def _serialize_paper(self, paper: Paper) -> dict[str, Any]:
        return {
            "id": str(paper.id),
            "title": paper.title,
            "year": paper.published_at.year if paper.published_at else None,
            "ingestion_status": paper.ingestion_status,
            "has_full_text": bool(paper.has_full_text),
            "source": self._paper_source_label(paper),
        }

    def _paper_source_label(self, paper: Paper) -> str:
        if paper.published_at:
            return f"{paper.title} ({paper.published_at.year})"
        return paper.title

    def _format_vector_hit(self, hit: dict[str, Any]) -> dict[str, Any]:
        content = str(hit.get("content") or "").strip()
        snippet = content[:280] + ("..." if len(content) > 280 else "")
        return {
            "paper_id": str(hit.get("paper_id") or ""),
            "paper_title": hit.get("paper_title"),
            "section_title": hit.get("section_title"),
            "similarity": round(float(hit.get("similarity") or 0.0), 3),
            "snippet": snippet,
        }

    def _preserve_requested_order(
        self,
        papers: list[Paper],
        requested_ids: list[str],
    ) -> list[Paper]:
        order_map = {paper_id: index for index, paper_id in enumerate(requested_ids)}
        return sorted(
            papers,
            key=lambda paper: order_map.get(str(paper.id), len(order_map)),
        )

    def _dedupe_preserve_order(self, values: list[str]) -> list[str]:
        seen: set[str] = set()
        output: list[str] = []
        for value in values:
            if value in seen:
                continue
            seen.add(value)
            output.append(value)
        return output

    async def close(self) -> None:
        await self.deep_analysis.close()
