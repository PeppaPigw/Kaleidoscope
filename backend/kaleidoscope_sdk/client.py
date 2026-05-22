"""Kaleidoscope async SDK client.

Provides a typed, async-first interface for downstream research agents
to interact with the Kaleidoscope paper-intelligence API.

Usage::

    async with KaleidoscopeClient() as ks:
        results = await ks.search("attention mechanisms")
        paper = await ks.get_paper(results.results[0]["id"])
        answer = await ks.ask_paper(paper.id, "What is the main contribution?")
        print(answer.answer)
"""

from __future__ import annotations

import os
from typing import Any

import httpx

from .types import (
    AnswerResult,
    ClaimResult,
    EvidenceResult,
    ImportResult,
    Paper,
    PaperList,
    ResolveResult,
    SearchResult,
)

__all__ = [
    "KaleidoscopeClient",
    "KaleidoscopeError",
    "KaleidoscopeAuthError",
    "KaleidoscopeNotFoundError",
]

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class KaleidoscopeError(Exception):
    """Base error for Kaleidoscope API failures."""

    def __init__(self, message: str, status_code: int | None = None, body: Any = None):
        self.status_code = status_code
        self.body = body
        super().__init__(message)


class KaleidoscopeAuthError(KaleidoscopeError):
    """Raised on 401/403 responses."""


class KaleidoscopeNotFoundError(KaleidoscopeError):
    """Raised on 404 responses."""


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

_DEFAULT_BASE_URL = "http://127.0.0.1:8000"
_DEFAULT_API_KEY = "sk-kaleidoscope"
_API_PREFIX = "/api/v1"


class KaleidoscopeClient:
    """Async HTTP client for the Kaleidoscope agent API."""

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.base_url = (
            base_url or os.environ.get("KALEIDOSCOPE_URL") or _DEFAULT_BASE_URL
        ).rstrip("/")
        self.api_key = api_key or os.environ.get("KALEIDOSCOPE_API_KEY") or _DEFAULT_API_KEY
        self._timeout = timeout
        self._client: httpx.AsyncClient | None = None

    # --- lifecycle ---

    async def _ensure_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self._timeout,
                headers=self._headers(),
            )
        return self._client

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def __aenter__(self) -> KaleidoscopeClient:
        await self._ensure_client()
        return self

    async def __aexit__(self, *_exc: object) -> None:
        await self.close()

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    # --- internal helpers ---

    def _url(self, path: str) -> str:
        if path.startswith("/"):
            return f"{_API_PREFIX}{path}"
        return path

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: Any | None = None,
    ) -> Any:
        client = await self._ensure_client()
        response = await client.request(method, self._url(path), params=params, json=json)
        return self._handle_response(response)

    async def _raw_request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: Any | None = None,
    ) -> Any:
        """Request without the /api/v1 prefix (for /health etc.)."""
        client = await self._ensure_client()
        response = await client.request(method, path, params=params, json=json)
        return self._handle_response(response)

    def _handle_response(self, response: httpx.Response) -> Any:
        if response.status_code in (401, 403):
            raise KaleidoscopeAuthError(
                f"Authentication failed ({response.status_code})",
                status_code=response.status_code,
                body=self._safe_json(response),
            )
        if response.status_code == 404:
            raise KaleidoscopeNotFoundError(
                f"Resource not found: {response.url.path}",
                status_code=404,
                body=self._safe_json(response),
            )
        if response.status_code >= 400:
            raise KaleidoscopeError(
                f"API error {response.status_code}: {response.text[:500]}",
                status_code=response.status_code,
                body=self._safe_json(response),
            )
        return self._safe_json(response)

    @staticmethod
    def _safe_json(response: httpx.Response) -> Any:
        try:
            return response.json()
        except Exception:
            return response.text

    @staticmethod
    def _unwrap(data: Any) -> Any:
        """Unwrap a potential {data: ...} envelope."""
        if isinstance(data, dict) and "data" in data and len(data) <= 3:
            return data["data"]
        return data

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    async def health(self) -> dict[str, Any]:
        """Check API health status."""
        data = await self._raw_request("GET", "/health")
        return data if isinstance(data, dict) else {}

    async def manifest(self) -> dict[str, Any]:
        """Retrieve the agent manifest (tool schemas, scopes, costs)."""
        data = await self._request("GET", "/agent/manifest")
        return data if isinstance(data, dict) else {}

    async def tools(self) -> list[dict[str, Any]]:
        """List available agent tools."""
        data = await self._request("GET", "/agent/tools")
        if isinstance(data, dict) and "tools" in data:
            return data["tools"]  # type: ignore[no-any-return]
        return data if isinstance(data, list) else []

    # ------------------------------------------------------------------
    # Paper operations
    # ------------------------------------------------------------------

    async def search(self, query: str, mode: str = "hybrid", limit: int = 10) -> SearchResult:
        """Search papers using keyword, semantic, or hybrid mode."""
        data = await self._request(
            "GET", "/search", params={"q": query, "mode": mode, "per_page": limit}
        )
        data = self._unwrap(data)
        if isinstance(data, dict):
            return SearchResult(
                results=data.get("items") or data.get("results") or [],
                total=data.get("total", 0),
                query=query,
            )
        return SearchResult(results=[], total=0, query=query)

    async def get_paper(self, paper_id: str) -> Paper:
        """Get a single paper by ID."""
        data = await self._request("GET", f"/papers/{paper_id}")
        data = self._unwrap(data)
        return Paper.model_validate(data)

    async def import_paper(self, identifier: str, identifier_type: str = "doi") -> ImportResult:
        """Import a paper by identifier (DOI, arXiv ID, PMID, URL)."""
        data = await self._request(
            "POST",
            "/papers/import",
            json={"identifier": identifier, "identifier_type": identifier_type},
        )
        data = self._unwrap(data)
        return ImportResult.model_validate(data)

    async def import_status(self, identifier: str) -> dict[str, Any]:
        """Check the import/ingestion status of a paper."""
        data = await self._request("GET", f"/imports/status/{identifier}")
        return data if isinstance(data, dict) else {}

    async def list_papers(self, limit: int = 20, offset: int = 0) -> PaperList:
        """List papers with pagination."""
        page = (offset // limit) + 1 if limit > 0 else 1
        data = await self._request("GET", "/papers", params={"per_page": limit, "page": page})
        data = self._unwrap(data)
        if isinstance(data, dict):
            return PaperList(
                papers=data.get("items") or data.get("papers") or [],
                total=data.get("total", 0),
            )
        return PaperList()

    # ------------------------------------------------------------------
    # Content & Analysis
    # ------------------------------------------------------------------

    async def get_content(self, paper_id: str) -> dict[str, Any]:
        """Get parsed full-text content for a paper."""
        data = await self._request("GET", f"/papers/{paper_id}/content")
        return self._unwrap(data) if isinstance(self._unwrap(data), dict) else {}

    async def get_labels(self, paper_id: str) -> dict[str, Any]:
        """Get AI-generated labels/tags for a paper."""
        data = await self._request("GET", f"/papers/{paper_id}/labels")
        return self._unwrap(data) if isinstance(self._unwrap(data), dict) else {}

    async def get_deep_analysis(self, paper_id: str) -> dict[str, Any]:
        """Get deep analysis results for a paper."""
        data = await self._request("GET", f"/papers/{paper_id}/deep-analysis")
        return self._unwrap(data) if isinstance(self._unwrap(data), dict) else {}

    async def get_overview_image(self, paper_id: str) -> dict[str, Any]:
        """Get overview image metadata for a paper."""
        data = await self._request("GET", f"/papers/{paper_id}/overview-image")
        return self._unwrap(data) if isinstance(self._unwrap(data), dict) else {}

    # ------------------------------------------------------------------
    # QA & Evidence
    # ------------------------------------------------------------------

    async def ask_paper(self, paper_id: str, question: str) -> AnswerResult:
        """Ask a question about a single paper."""
        data = await self._request(
            "POST", f"/paper-qa/{paper_id}/ask", json={"question": question}
        )
        data = self._unwrap(data)
        if isinstance(data, dict):
            return AnswerResult(
                answer=data.get("answer", ""),
                sources=data.get("sources", []),
                confidence=data.get("confidence"),
            )
        return AnswerResult(answer="")

    async def ask_papers(self, paper_ids: list[str], question: str) -> AnswerResult:
        """Ask a question across multiple papers."""
        data = await self._request(
            "POST",
            "/paper-qa/ask-multi",
            json={"paper_ids": paper_ids, "question": question},
        )
        data = self._unwrap(data)
        if isinstance(data, dict):
            return AnswerResult(
                answer=data.get("answer", ""),
                sources=data.get("sources", []),
                confidence=data.get("confidence"),
            )
        return AnswerResult(answer="")

    async def search_evidence(
        self,
        query: str,
        paper_ids: list[str] | None = None,
        top_k: int = 10,
    ) -> EvidenceResult:
        """Search for evidence passages across papers."""
        data = await self._request(
            "POST",
            "/evidence/search",
            json={"query": query, "paper_ids": paper_ids or [], "top_k": top_k},
        )
        data = self._unwrap(data)
        if isinstance(data, dict):
            return EvidenceResult(
                evidence=data.get("evidence") or data.get("results") or [],
                query=query,
            )
        return EvidenceResult(query=query)

    async def verify_claim(
        self,
        claim: str,
        paper_ids: list[str] | None = None,
    ) -> ClaimResult:
        """Verify a scientific claim against paper evidence."""
        data = await self._request(
            "POST",
            "/claims/verify",
            json={"claim": claim, "paper_ids": paper_ids or []},
        )
        data = self._unwrap(data)
        if isinstance(data, dict):
            return ClaimResult(
                verdict=data.get("verdict", ""),
                confidence=data.get("confidence"),
                evidence=data.get("evidence", []),
            )
        return ClaimResult()

    # ------------------------------------------------------------------
    # Context & Synthesis
    # ------------------------------------------------------------------

    async def context_pack(
        self,
        paper_ids: list[str],
        task: str,
        token_budget: int = 8000,
    ) -> dict[str, Any]:
        """Build a compressed context pack for agent consumption."""
        data = await self._request(
            "POST",
            "/agent/context-pack",
            json={
                "paper_ids": paper_ids,
                "question": task,
                "token_budget": token_budget,
            },
        )
        return self._unwrap(data) if isinstance(self._unwrap(data), dict) else {}

    async def resolve(self, identifier: str) -> ResolveResult:
        """Resolve an ambiguous identifier to known papers."""
        data = await self._request("POST", "/resolve", json={"identifier": identifier})
        data = self._unwrap(data)
        if isinstance(data, dict):
            return ResolveResult(
                matches=data.get("matches", []),
                action=data.get("action", ""),
            )
        return ResolveResult()

    # ------------------------------------------------------------------
    # Agent tool dispatch
    # ------------------------------------------------------------------

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Invoke a single agent tool by name."""
        data = await self._request(
            "POST", "/agent/call", json={"tool": tool_name, "arguments": arguments}
        )
        if isinstance(data, dict):
            return data.get("result", data)  # type: ignore[no-any-return]
        return {}

    async def batch_tools(self, calls: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Invoke multiple agent tools in a single request."""
        payload = [
            {"tool": c.get("tool", c.get("name", "")), "arguments": c.get("arguments", {})}
            for c in calls
        ]
        data = await self._request("POST", "/agent/batch", json=payload)
        if isinstance(data, dict) and "results" in data:
            return data["results"]  # type: ignore[no-any-return]
        return data if isinstance(data, list) else []

    # ------------------------------------------------------------------
    # DeepXiv
    # ------------------------------------------------------------------

    async def deepxiv_search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """Search papers via DeepXiv."""
        data = await self._request("GET", "/deepxiv/search", params={"q": query, "size": limit})
        data = self._unwrap(data)
        if isinstance(data, dict):
            return data.get("results") or data.get("items") or []
        return data if isinstance(data, list) else []

    async def deepxiv_paper(self, arxiv_id: str, view: str = "brief") -> dict[str, Any]:
        """Get a DeepXiv paper by arXiv ID (view: brief, head, raw, json)."""
        data = await self._request("GET", f"/deepxiv/papers/{arxiv_id}/{view}")
        return self._unwrap(data) if isinstance(self._unwrap(data), dict) else {}

    # ------------------------------------------------------------------
    # Collections
    # ------------------------------------------------------------------

    async def list_collections(self) -> list[dict[str, Any]]:
        """List all collections."""
        data = await self._request("GET", "/collections")
        data = self._unwrap(data)
        if isinstance(data, dict):
            return data.get("items") or data.get("collections") or []
        return data if isinstance(data, list) else []

    async def create_collection(self, name: str, description: str = "") -> dict[str, Any]:
        """Create a new collection."""
        data = await self._request(
            "POST", "/collections", json={"name": name, "description": description}
        )
        return self._unwrap(data) if isinstance(self._unwrap(data), dict) else {}

    async def add_to_collection(self, collection_id: str, paper_ids: list[str]) -> dict[str, Any]:
        """Add papers to a collection."""
        data = await self._request(
            "POST",
            f"/collections/{collection_id}/papers",
            json={"paper_ids": paper_ids},
        )
        return self._unwrap(data) if isinstance(self._unwrap(data), dict) else {}

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    async def export_citations(self, paper_ids: list[str], format: str = "bibtex") -> str:
        """Export citations in the specified format (bibtex, ris, csl-json).

        Fetches each paper's citation individually and concatenates results.
        """
        parts: list[str] = []
        for pid in paper_ids:
            data = await self._request(
                "GET", f"/papers/{pid}/export", params={"format": format}
            )
            if isinstance(data, str):
                parts.append(data)
            elif isinstance(data, dict) and "content" in data:
                parts.append(str(data["content"]))
            else:
                parts.append(str(data))
        return "\n\n".join(parts)

    # ------------------------------------------------------------------
    # Analytics
    # ------------------------------------------------------------------

    async def analytics_overview(self) -> dict[str, Any]:
        """Get analytics overview (paper counts, trends, activity)."""
        data = await self._request("GET", "/analytics/overview")
        return self._unwrap(data) if isinstance(self._unwrap(data), dict) else {}

    # ------------------------------------------------------------------
    # Research Intelligence
    # ------------------------------------------------------------------

    async def synthesize_papers(
        self, paper_ids: list[str], topic: str
    ) -> dict[str, Any]:
        """Synthesize knowledge across papers: themes, consensus, divergences, gaps."""
        data = await self._request(
            "POST", "/agent/call",
            json={"tool": "synthesize_papers", "arguments": {"paper_ids": paper_ids, "topic": topic}},
        )
        return data.get("result", data) if isinstance(data, dict) else {}

    async def analyze_research_gaps(
        self, paper_ids: list[str], research_question: str
    ) -> dict[str, Any]:
        """Identify unexplored research directions given papers and a question."""
        data = await self._request(
            "POST", "/agent/call",
            json={"tool": "analyze_research_gaps", "arguments": {"paper_ids": paper_ids, "research_question": research_question}},
        )
        return data.get("result", data) if isinstance(data, dict) else {}

    async def extract_methodology(
        self, paper_id: str, focus: str | None = None
    ) -> dict[str, Any]:
        """Extract structured methodology: methods, datasets, metrics, baselines."""
        args: dict[str, Any] = {"paper_id": paper_id}
        if focus:
            args["focus"] = focus
        data = await self._request(
            "POST", "/agent/call",
            json={"tool": "extract_methodology", "arguments": args},
        )
        return data.get("result", data) if isinstance(data, dict) else {}

    async def compare_methods(
        self,
        paper_ids: list[str],
        research_question: str | None = None,
        dimensions: list[str] | None = None,
    ) -> dict[str, Any]:
        """Compare methodologies across papers on specified dimensions."""
        args: dict[str, Any] = {"paper_ids": paper_ids}
        if research_question:
            args["research_question"] = research_question
        if dimensions:
            args["dimensions"] = dimensions
        data = await self._request(
            "POST", "/agent/call",
            json={"tool": "compare_methods", "arguments": args},
        )
        return data.get("result", data) if isinstance(data, dict) else {}

    async def generate_related_work(
        self,
        paper_ids: list[str],
        style: str = "thematic",
        format: str = "markdown",
    ) -> dict[str, Any]:
        """Generate a Related Work section from papers."""
        data = await self._request(
            "POST", "/agent/call",
            json={"tool": "generate_related_work", "arguments": {"paper_ids": paper_ids, "style": style, "format": format}},
        )
        return data.get("result", data) if isinstance(data, dict) else {}

    async def find_reading_path(
        self, paper_id: str, max_papers: int = 10
    ) -> dict[str, Any]:
        """Find optimal reading order to understand a paper."""
        data = await self._request(
            "POST", "/agent/call",
            json={"tool": "find_reading_path", "arguments": {"paper_id": paper_id, "max_papers": max_papers}},
        )
        return data.get("result", data) if isinstance(data, dict) else {}

    async def search_with_reasoning(
        self, research_question: str, scope: str = "moderate", limit: int = 10
    ) -> dict[str, Any]:
        """Intelligent search that understands research intent."""
        data = await self._request(
            "POST", "/agent/call",
            json={"tool": "search_with_reasoning", "arguments": {"research_question": research_question, "scope": scope, "limit": limit}},
        )
        return data.get("result", data) if isinstance(data, dict) else {}

    async def build_evidence_map(
        self,
        claim_or_question: str,
        paper_ids: list[str] | None = None,
        top_k: int = 15,
    ) -> dict[str, Any]:
        """Build structured evidence map for a claim: supporting, qualifying, weak."""
        data = await self._request(
            "POST", "/agent/call",
            json={"tool": "build_evidence_map", "arguments": {"claim_or_question": claim_or_question, "paper_ids": paper_ids or [], "top_k": top_k}},
        )
        return data.get("result", data) if isinstance(data, dict) else {}

    # ─── Deep Research Methods ────────────────────────────────────

    async def investigate(
        self,
        question: str,
        depth: str = "standard",
    ) -> dict[str, Any]:
        """Deep investigation of a research question. Returns papers, findings, gaps, and next steps."""
        data = await self._request(
            "POST", "/agent/call",
            json={"tool": "investigate", "arguments": {"question": question, "depth": depth}},
        )
        return data.get("result", data) if isinstance(data, dict) else {}

    async def extract_experiments(self, paper_id: str) -> dict[str, Any]:
        """Extract all experiments from a paper as structured data."""
        data = await self._request(
            "POST", "/agent/call",
            json={"tool": "extract_experiments", "arguments": {"paper_id": paper_id}},
        )
        return data.get("result", data) if isinstance(data, dict) else {}

    async def multi_paper_qa(
        self,
        question: str,
        max_papers: int = 5,
    ) -> dict[str, Any]:
        """Ask a question across the entire corpus with automatic paper discovery and synthesis."""
        data = await self._request(
            "POST", "/agent/call",
            json={"tool": "multi_paper_qa", "arguments": {"question": question, "max_papers": max_papers}},
        )
        return data.get("result", data) if isinstance(data, dict) else {}

    async def suggest_next_steps(
        self,
        topic: str,
        known_results: str = "",
        paper_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        """Suggest concrete next experiments or research directions."""
        args: dict[str, Any] = {"topic": topic}
        if known_results:
            args["known_results"] = known_results
        if paper_ids:
            args["paper_ids"] = paper_ids
        data = await self._request(
            "POST", "/agent/call",
            json={"tool": "suggest_next_steps", "arguments": args},
        )
        return data.get("result", data) if isinstance(data, dict) else {}

    async def discover_papers(
        self,
        need: str,
        constraints: str = "",
        limit: int = 10,
    ) -> dict[str, Any]:
        """Semantic paper discovery — finds papers relevant to a research need."""
        args: dict[str, Any] = {"need": need, "limit": limit}
        if constraints:
            args["constraints"] = constraints
        data = await self._request(
            "POST", "/agent/call",
            json={"tool": "discover_papers", "arguments": args},
        )
        return data.get("result", data) if isinstance(data, dict) else {}

    async def research_pipeline(
        self,
        question: str,
        depth: str = "standard",
    ) -> dict[str, Any]:
        """Execute a complete research workflow: discover → extract → synthesize → gaps → next steps."""
        data = await self._request(
            "POST", "/agent/call",
            json={"tool": "research_pipeline", "arguments": {"question": question, "depth": depth}},
        )
        return data.get("result", data) if isinstance(data, dict) else {}

    # ─── Corpus Intelligence Methods ─────────────────────────────

    async def compare_papers_table(
        self,
        paper_ids: list[str],
        dimensions: list[str] | None = None,
    ) -> dict[str, Any]:
        """Generate structured comparison table across papers."""
        args: dict[str, Any] = {"paper_ids": paper_ids}
        if dimensions:
            args["dimensions"] = dimensions
        data = await self._request(
            "POST", "/agent/call",
            json={"tool": "compare_papers_table", "arguments": args},
        )
        return data.get("result", data) if isinstance(data, dict) else {}

    async def find_papers_by_taxonomy(
        self,
        domain: str = "",
        task: str = "",
        method: str = "",
        data_object: str = "",
        limit: int = 20,
    ) -> dict[str, Any]:
        """Find papers by structured taxonomy labels."""
        args: dict[str, Any] = {"limit": limit}
        if domain:
            args["domain"] = domain
        if task:
            args["task"] = task
        if method:
            args["method"] = method
        if data_object:
            args["data_object"] = data_object
        data = await self._request(
            "POST", "/agent/call",
            json={"tool": "find_papers_by_taxonomy", "arguments": args},
        )
        return data.get("result", data) if isinstance(data, dict) else {}

    async def trace_citations(
        self,
        paper_id: str,
        direction: str = "both",
        depth: int = 1,
    ) -> dict[str, Any]:
        """Trace citation relationships for a paper."""
        data = await self._request(
            "POST", "/agent/call",
            json={"tool": "trace_citations", "arguments": {"paper_id": paper_id, "direction": direction, "depth": depth}},
        )
        return data.get("result", data) if isinstance(data, dict) else {}

    async def corpus_overview(self, focus: str = "") -> dict[str, Any]:
        """Get bird's-eye view of the corpus."""
        args: dict[str, Any] = {}
        if focus:
            args["focus"] = focus
        data = await self._request(
            "POST", "/agent/call",
            json={"tool": "corpus_overview", "arguments": args},
        )
        return data.get("result", data) if isinstance(data, dict) else {}

    async def extract_all_results(
        self,
        paper_ids: list[str],
        metric_focus: str = "",
    ) -> dict[str, Any]:
        """Extract quantitative results from multiple papers."""
        args: dict[str, Any] = {"paper_ids": paper_ids}
        if metric_focus:
            args["metric_focus"] = metric_focus
        data = await self._request(
            "POST", "/agent/call",
            json={"tool": "extract_all_results", "arguments": args},
        )
        return data.get("result", data) if isinstance(data, dict) else {}

    async def find_contradictions(
        self,
        claim: str,
        paper_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        """Find papers that contradict each other on a claim."""
        args: dict[str, Any] = {"claim": claim}
        if paper_ids:
            args["paper_ids"] = paper_ids
        data = await self._request(
            "POST", "/agent/call",
            json={"tool": "find_contradictions", "arguments": args},
        )
        return data.get("result", data) if isinstance(data, dict) else {}

    async def get_paper_section(self, paper_id: str, section: str) -> dict[str, Any]:
        """Get a specific section of a paper."""
        data = await self._request(
            "POST", "/agent/call",
            json={"tool": "get_paper_section", "arguments": {"paper_id": paper_id, "section": section}},
        )
        return data.get("result", data) if isinstance(data, dict) else {}

    async def rank_papers_for_reading(
        self,
        paper_ids: list[str],
        goal: str,
    ) -> dict[str, Any]:
        """Rank papers by relevance and importance for a research goal."""
        data = await self._request(
            "POST", "/agent/call",
            json={"tool": "rank_papers_for_reading", "arguments": {"paper_ids": paper_ids, "goal": goal}},
        )
        return data.get("result", data) if isinstance(data, dict) else {}

    async def batch_import(
        self,
        identifiers: list[str],
        source: str = "arxiv",
    ) -> dict[str, Any]:
        """Import multiple papers at once."""
        data = await self._request(
            "POST", "/agent/call",
            json={"tool": "batch_import", "arguments": {"identifiers": identifiers, "source": source}},
        )
        return data.get("result", data) if isinstance(data, dict) else {}

    async def find_experts(
        self,
        topic: str,
        limit: int = 10,
    ) -> dict[str, Any]:
        """Find authors who are experts on a given topic."""
        data = await self._request(
            "POST", "/agent/call",
            json={"tool": "find_experts", "arguments": {"topic": topic, "limit": limit}},
        )
        return data.get("result", data) if isinstance(data, dict) else {}

    async def temporal_trends(
        self,
        topic: str,
        granularity: str = "quarterly",
    ) -> dict[str, Any]:
        """Analyze how a topic has evolved over time."""
        data = await self._request(
            "POST", "/agent/call",
            json={"tool": "temporal_trends", "arguments": {"topic": topic, "granularity": granularity}},
        )
        return data.get("result", data) if isinstance(data, dict) else {}

    async def auto_cite(
        self,
        text: str,
        max_citations: int = 5,
    ) -> dict[str, Any]:
        """Find papers that should be cited for a given text."""
        data = await self._request(
            "POST", "/agent/call",
            json={"tool": "auto_cite", "arguments": {"text": text, "max_citations": max_citations}},
        )
        return data.get("result", data) if isinstance(data, dict) else {}

    async def paper_lineage(
        self,
        paper_id: str,
        depth: int = 1,
    ) -> dict[str, Any]:
        """Trace the intellectual lineage of a paper."""
        data = await self._request(
            "POST", "/agent/call",
            json={"tool": "paper_lineage", "arguments": {"paper_id": paper_id, "depth": depth}},
        )
        return data.get("result", data) if isinstance(data, dict) else {}

    async def method_comparison(
        self,
        task: str,
        paper_ids: list[str] | None = None,
        limit: int = 5,
    ) -> dict[str, Any]:
        """Compare methods across papers on the same task."""
        args: dict[str, Any] = {"task": task, "limit": limit}
        if paper_ids:
            args["paper_ids"] = paper_ids
        data = await self._request(
            "POST", "/agent/call",
            json={"tool": "method_comparison", "arguments": args},
        )
        return data.get("result", data) if isinstance(data, dict) else {}

    async def extract_claims(
        self,
        paper_id: str,
        claim_type: str = "all",
        limit: int = 10,
    ) -> dict[str, Any]:
        """Extract factual claims from a paper with evidence."""
        data = await self._request(
            "POST", "/agent/call",
            json={"tool": "extract_claims", "arguments": {"paper_id": paper_id, "claim_type": claim_type, "limit": limit}},
        )
        return data.get("result", data) if isinstance(data, dict) else {}

    async def find_datasets(
        self,
        task: str,
        limit: int = 15,
    ) -> dict[str, Any]:
        """Find datasets mentioned across the corpus for a task."""
        data = await self._request(
            "POST", "/agent/call",
            json={"tool": "find_datasets", "arguments": {"task": task, "limit": limit}},
        )
        return data.get("result", data) if isinstance(data, dict) else {}

    async def literature_map(
        self,
        topic: str,
        max_papers: int = 20,
    ) -> dict[str, Any]:
        """Generate a structured literature map for a topic."""
        data = await self._request(
            "POST", "/agent/call",
            json={"tool": "literature_map", "arguments": {"topic": topic, "max_papers": max_papers}},
        )
        return data.get("result", data) if isinstance(data, dict) else {}
