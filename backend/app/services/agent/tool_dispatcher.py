"""Agent Tool Dispatcher — expose Kaleidoscope capabilities as callable tools.

The TOOLS registry and ToolDispatcher are transport-agnostic.
They are currently served via a REST API (/api/v1/agent/*).
When real MCP transport (stdio/SSE) is added in P2, it will
reuse the same TOOLS and ToolDispatcher without changes.
"""

import json
from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.paper import Paper

logger = structlog.get_logger(__name__)


# ─── Tool Registry ───────────────────────────────────────────────

TOOLS = [
    {
        "name": "search_papers",
        "description": "Search academic papers by keyword, semantic query, or hybrid. Returns title, DOI, abstract, and relevance score.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query text"},
                "mode": {"type": "string", "enum": ["keyword", "semantic", "hybrid"], "default": "hybrid"},
                "limit": {"type": "integer", "default": 10, "maximum": 50},
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_paper",
        "description": "Get full details of a paper by its internal ID, DOI, or arXiv ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "identifier": {"type": "string", "description": "Paper ID, DOI, or arXiv ID"},
            },
            "required": ["identifier"],
        },
    },
    {
        "name": "get_citations",
        "description": "Get forward/backward citation relationships for a paper from the citation graph.",
        "parameters": {
            "type": "object",
            "properties": {
                "paper_id": {"type": "string", "description": "Paper ID"},
                "direction": {"type": "string", "enum": ["forward", "backward", "both"], "default": "both"},
                "limit": {"type": "integer", "default": 20},
            },
            "required": ["paper_id"],
        },
    },
    {
        "name": "find_similar",
        "description": "Find papers similar to a given paper using citation analysis and semantic similarity.",
        "parameters": {
            "type": "object",
            "properties": {
                "paper_id": {"type": "string", "description": "Paper ID"},
                "limit": {"type": "integer", "default": 10},
            },
            "required": ["paper_id"],
        },
    },
    {
        "name": "summarize_paper",
        "description": "Generate a summary of a paper at the specified detail level.",
        "parameters": {
            "type": "object",
            "properties": {
                "paper_id": {"type": "string", "description": "Paper ID"},
                "level": {"type": "string", "enum": ["tweet", "abstract", "executive", "detailed"], "default": "abstract"},
            },
            "required": ["paper_id"],
        },
    },
    {
        "name": "extract_info",
        "description": "Extract structured information (highlights, methods, datasets, metrics) from a paper.",
        "parameters": {
            "type": "object",
            "properties": {
                "paper_id": {"type": "string", "description": "Paper ID"},
                "extract_type": {"type": "string", "enum": ["highlights", "methods"], "default": "highlights"},
            },
            "required": ["paper_id"],
        },
    },
    {
        "name": "ask_paper",
        "description": "Ask a natural language question about a paper's content. Uses RAG to find relevant passages and generate an answer.",
        "parameters": {
            "type": "object",
            "properties": {
                "paper_id": {"type": "string", "description": "Paper ID"},
                "question": {"type": "string", "description": "Question to ask about the paper"},
            },
            "required": ["paper_id", "question"],
        },
    },
    {
        "name": "ask_papers",
        "description": "Ask a question across multiple papers. Synthesizes and compares information from multiple sources.",
        "parameters": {
            "type": "object",
            "properties": {
                "paper_ids": {"type": "array", "items": {"type": "string"}, "description": "List of paper IDs"},
                "question": {"type": "string", "description": "Question to ask across papers"},
            },
            "required": ["paper_ids", "question"],
        },
    },
    {
        "name": "import_paper",
        "description": "Import a paper by DOI, arXiv ID, PMID, or URL. Queues it for full ingestion.",
        "parameters": {
            "type": "object",
            "properties": {
                "identifier": {"type": "string", "description": "DOI, arXiv ID, PMID, or URL"},
                "identifier_type": {"type": "string", "enum": ["doi", "arxiv", "pmid", "url", "title"], "default": "doi"},
            },
            "required": ["identifier"],
        },
    },
    {
        "name": "list_collections",
        "description": "List all paper collections with paper counts.",
        "parameters": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "add_to_collection",
        "description": "Add paper(s) to a collection.",
        "parameters": {
            "type": "object",
            "properties": {
                "collection_id": {"type": "string", "description": "Collection ID"},
                "paper_ids": {"type": "array", "items": {"type": "string"}, "description": "Paper IDs to add"},
            },
            "required": ["collection_id", "paper_ids"],
        },
    },
    {
        "name": "export_citations",
        "description": "Export citations in BibTeX, RIS, or CSL-JSON format.",
        "parameters": {
            "type": "object",
            "properties": {
                "paper_ids": {"type": "array", "items": {"type": "string"}, "description": "Paper IDs to export"},
                "format": {"type": "string", "enum": ["bibtex", "ris", "csl_json"], "default": "bibtex"},
            },
            "required": ["paper_ids"],
        },
    },
    {
        "name": "get_recent_papers",
        "description": "Get recently ingested papers, optionally filtered by status.",
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "default": 20},
                "status": {"type": "string", "enum": ["indexed", "enriched", "discovered"], "description": "Filter by ingestion status"},
            },
        },
    },
]


class ToolDispatcher:
    """Dispatch tool calls to the appropriate Kaleidoscope service."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def call_tool(self, tool_name: str, arguments: dict) -> Any:
        """Execute a tool and return structured results."""
        log = logger.bind(tool=tool_name, args_keys=list(arguments.keys()))

        try:
            handler = getattr(self, f"_handle_{tool_name}", None)
            if not handler:
                return {"error": f"Unknown tool: {tool_name}"}
            result = await handler(arguments)
            log.info("tool_executed_ok")
            return result
        except Exception as e:
            log.error("tool_execution_failed", error=str(e))
            return {"error": str(e)}

    # ─── Tool Handlers ────────────────────────────────────────────

    async def _handle_search_papers(self, args: dict) -> dict:
        from app.services.search.instances import hybrid_service

        # Use process-level singleton (avoids repeated SPECTER2 model loading)
        results = hybrid_service.search(
            query=args["query"],
            mode=args.get("mode", "hybrid"),
            per_page=args.get("limit", 10),
        )
        return results

    async def _handle_get_paper(self, args: dict) -> dict:
        from app.services.collection_service import ReadingStatusService

        identifier = args["identifier"]
        # Try UUID, DOI, arXiv ID
        query = select(Paper).where(Paper.deleted_at.is_(None))
        if len(identifier) == 36 and "-" in identifier:  # UUID
            query = query.where(Paper.id == identifier)
        elif identifier.startswith("10."):  # DOI
            query = query.where(Paper.doi == identifier)
        else:  # arXiv ID
            query = query.where(Paper.arxiv_id == identifier)

        result = await self.db.execute(query)
        paper = result.scalar_one_or_none()
        if not paper:
            return {"error": "Paper not found"}

        # Get per-user reading status from UserReadingStatus table
        rs_svc = ReadingStatusService(self.db)
        reading_status = await rs_svc.get_status(str(paper.id))

        return {
            "id": str(paper.id),
            "doi": paper.doi,
            "arxiv_id": paper.arxiv_id,
            "title": paper.title,
            "abstract": paper.abstract,
            "published_at": str(paper.published_at) if paper.published_at else None,
            "citation_count": paper.citation_count,
            "has_full_text": paper.has_full_text,
            "reading_status": reading_status,
        }

    async def _handle_get_citations(self, args: dict) -> dict:
        from app.services.graph.citation_graph import CitationGraphService
        svc = CitationGraphService(self.db)
        return await svc.get_citations(
            args["paper_id"],
            direction=args.get("direction", "both"),
            limit=args.get("limit", 20),
        )

    async def _handle_find_similar(self, args: dict) -> dict:
        from app.services.graph.citation_graph import RecommendationService
        svc = RecommendationService(self.db)
        results = await svc.recommend_similar(
            args["paper_id"], limit=args.get("limit", 10),
        )
        return {"similar_papers": results}

    async def _handle_summarize_paper(self, args: dict) -> dict:
        from app.services.extraction.summarizer import SummarizationService
        result = await self.db.execute(
            select(Paper).where(Paper.id == args["paper_id"])
        )
        paper = result.scalar_one_or_none()
        if not paper:
            return {"error": "Paper not found"}
        svc = SummarizationService(self.db)
        try:
            return await svc.summarize(paper, level=args.get("level", "abstract"))
        finally:
            await svc.close()

    async def _handle_extract_info(self, args: dict) -> dict:
        from app.services.extraction.extractor import ExtractionService
        result = await self.db.execute(
            select(Paper).where(Paper.id == args["paper_id"])
        )
        paper = result.scalar_one_or_none()
        if not paper:
            return {"error": "Paper not found"}
        svc = ExtractionService(self.db)
        try:
            if args.get("extract_type") == "methods":
                return await svc.extract_methods(paper)
            return await svc.extract_highlights(paper)
        finally:
            await svc.close()

    async def _handle_ask_paper(self, args: dict) -> dict:
        from app.services.extraction.qa_engine import PaperQAEngine
        svc = PaperQAEngine(self.db)
        try:
            result = await svc.ask(args["paper_id"], args["question"])
            return result.to_dict()
        finally:
            await svc.close()

    async def _handle_ask_papers(self, args: dict) -> dict:
        from app.services.extraction.qa_engine import PaperQAEngine
        svc = PaperQAEngine(self.db)
        try:
            result = await svc.ask_collection(args["paper_ids"], args["question"])
            return result.to_dict()
        finally:
            await svc.close()

    async def _handle_import_paper(self, args: dict) -> dict:
        from app.tasks.ingest_tasks import ingest_paper
        task = ingest_paper.delay(
            identifier=args["identifier"],
            id_type=args.get("identifier_type", "doi"),
        )
        return {"status": "queued", "task_id": task.id}

    async def _handle_list_collections(self, args: dict) -> dict:
        from app.services.collection_service import CollectionService
        svc = CollectionService(self.db)
        collections = await svc.list_collections()
        return {
            "collections": [
                {"id": str(c.id), "name": c.name, "paper_count": c.paper_count}
                for c in collections
            ]
        }

    async def _handle_add_to_collection(self, args: dict) -> dict:
        from app.services.collection_service import CollectionService
        svc = CollectionService(self.db)
        added = await svc.add_papers(
            args["collection_id"], args["paper_ids"],
        )
        await self.db.commit()
        return {"added": added}

    async def _handle_export_citations(self, args: dict) -> dict:
        from app.services.export_service import ExportService
        svc = ExportService(self.db)
        content = await svc.export_papers(
            args["paper_ids"],
            format=args.get("format", "bibtex"),
        )
        return {"content": content, "format": args.get("format", "bibtex")}

    async def _handle_get_recent_papers(self, args: dict) -> dict:
        query = (
            select(Paper)
            .where(Paper.deleted_at.is_(None))
            .order_by(Paper.created_at.desc())
            .limit(args.get("limit", 20))
        )
        if "status" in args:
            query = query.where(Paper.ingestion_status == args["status"])

        result = await self.db.execute(query)
        papers = result.scalars().all()
        return {
            "papers": [
                {
                    "id": str(p.id),
                    "title": p.title,
                    "doi": p.doi,
                    "created_at": str(p.created_at),
                    "ingestion_status": p.ingestion_status,
                }
                for p in papers
            ]
        }


# Backward compat alias
MCPToolDispatcher = ToolDispatcher

