"""Agent manifest builder for downstream tool discovery."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from app.config import settings
from app.services.agent.tool_dispatcher import TOOLS

MANIFEST_VERSION = "1.0.0"
MANIFEST_UPDATED_AT = "2026-04-25"
TOOL_VERSION = "1.0.0"

_GENERIC_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": True,
}

_TOOL_METADATA: dict[str, dict[str, Any]] = {
    "search_papers": {
        "scopes": ["papers:read", "search:read"],
        "cost": {"tier": "low", "units": 2},
        "output_schema": {
            "type": "object",
            "properties": {"results": {"type": "array"}},
            "additionalProperties": True,
        },
        "examples": [
            {
                "description": "Find recent neural retrieval papers.",
                "arguments": {
                    "query": "neural information retrieval survey",
                    "mode": "hybrid",
                    "limit": 5,
                },
            }
        ],
    },
    "get_paper": {
        "scopes": ["papers:read"],
        "cost": {"tier": "low", "units": 1},
        "output_schema": {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "title": {"type": "string"},
                "abstract": {"type": ["string", "null"]},
            },
            "additionalProperties": True,
        },
        "examples": [
            {
                "description": "Resolve a paper by DOI.",
                "arguments": {"identifier": "10.1145/3570000.3570001"},
            }
        ],
    },
    "get_citations": {
        "scopes": ["papers:read", "citations:read"],
        "cost": {"tier": "low", "units": 2},
        "output_schema": _GENERIC_OUTPUT_SCHEMA,
        "examples": [
            {
                "description": "Fetch incoming and outgoing citation edges.",
                "arguments": {
                    "paper_id": "00000000-0000-0000-0000-000000000001",
                    "direction": "both",
                    "limit": 20,
                },
            }
        ],
    },
    "find_similar": {
        "scopes": ["papers:read", "recommendations:read"],
        "cost": {"tier": "medium", "units": 3},
        "output_schema": {
            "type": "object",
            "properties": {"similar_papers": {"type": "array"}},
            "additionalProperties": True,
        },
        "examples": [
            {
                "description": "Find papers similar to a seed paper.",
                "arguments": {
                    "paper_id": "00000000-0000-0000-0000-000000000001",
                    "limit": 10,
                },
            }
        ],
    },
    "summarize_paper": {
        "scopes": ["papers:read", "llm:use"],
        "cost": {"tier": "high", "units": 10},
        "output_schema": _GENERIC_OUTPUT_SCHEMA,
        "examples": [
            {
                "description": "Create an executive summary for one paper.",
                "arguments": {
                    "paper_id": "00000000-0000-0000-0000-000000000001",
                    "level": "executive",
                },
            }
        ],
    },
    "extract_info": {
        "scopes": ["papers:read", "extraction:read", "llm:use"],
        "cost": {"tier": "high", "units": 8},
        "output_schema": _GENERIC_OUTPUT_SCHEMA,
        "examples": [
            {
                "description": "Extract methods from a paper.",
                "arguments": {
                    "paper_id": "00000000-0000-0000-0000-000000000001",
                    "extract_type": "methods",
                },
            }
        ],
    },
    "ask_paper": {
        "scopes": ["papers:read", "rag:ask", "llm:use"],
        "cost": {"tier": "high", "units": 12},
        "output_schema": _GENERIC_OUTPUT_SCHEMA,
        "examples": [
            {
                "description": "Ask for evidence-backed details in one paper.",
                "arguments": {
                    "paper_id": "00000000-0000-0000-0000-000000000001",
                    "question": "What dataset and metrics does this paper use?",
                },
            }
        ],
    },
    "ask_papers": {
        "scopes": ["papers:read", "rag:ask", "llm:use"],
        "cost": {"tier": "high", "units": 20},
        "output_schema": _GENERIC_OUTPUT_SCHEMA,
        "examples": [
            {
                "description": "Compare evidence across a small paper set.",
                "arguments": {
                    "paper_ids": [
                        "00000000-0000-0000-0000-000000000001",
                        "00000000-0000-0000-0000-000000000002",
                    ],
                    "question": "Where do these papers disagree?",
                },
            }
        ],
    },
    "import_paper": {
        "scopes": ["papers:import"],
        "cost": {"tier": "medium", "units": 5, "async": True},
        "output_schema": {
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "task_id": {"type": "string"},
            },
            "additionalProperties": True,
        },
        "examples": [
            {
                "description": "Queue DOI ingestion.",
                "arguments": {
                    "identifier": "10.1145/3570000.3570001",
                    "identifier_type": "doi",
                },
            }
        ],
    },
    "list_collections": {
        "scopes": ["collections:read"],
        "cost": {"tier": "low", "units": 1},
        "output_schema": {
            "type": "object",
            "properties": {"collections": {"type": "array"}},
            "additionalProperties": True,
        },
        "examples": [
            {
                "description": "List accessible workspaces.",
                "arguments": {},
            }
        ],
    },
    "add_to_collection": {
        "scopes": ["collections:write", "papers:read"],
        "cost": {"tier": "low", "units": 2},
        "output_schema": {
            "type": "object",
            "properties": {"added": {"type": "integer"}},
            "additionalProperties": True,
        },
        "examples": [
            {
                "description": "Add papers to a workspace.",
                "arguments": {
                    "collection_id": "00000000-0000-0000-0000-000000000010",
                    "paper_ids": ["00000000-0000-0000-0000-000000000001"],
                },
            }
        ],
    },
    "export_citations": {
        "scopes": ["papers:read", "exports:read"],
        "cost": {"tier": "low", "units": 2},
        "output_schema": {
            "type": "object",
            "properties": {
                "content": {"type": "string"},
                "format": {"type": "string"},
            },
            "additionalProperties": True,
        },
        "examples": [
            {
                "description": "Export a bibliography as BibTeX.",
                "arguments": {
                    "paper_ids": ["00000000-0000-0000-0000-000000000001"],
                    "format": "bibtex",
                },
            }
        ],
    },
    "get_recent_papers": {
        "scopes": ["papers:read"],
        "cost": {"tier": "low", "units": 1},
        "output_schema": {
            "type": "object",
            "properties": {"papers": {"type": "array"}},
            "additionalProperties": True,
        },
        "examples": [
            {
                "description": "Inspect recently indexed papers.",
                "arguments": {"limit": 10, "status": "indexed"},
            }
        ],
    },
}


def build_agent_manifest(api_base_path: str = "/api/v1") -> dict[str, Any]:
    """Build a stable JSON manifest for downstream agent clients."""
    return {
        "schema_version": MANIFEST_VERSION,
        "updated_at": MANIFEST_UPDATED_AT,
        "service": {
            "name": settings.app_name,
            "api_version": "v1",
            "base_path": api_base_path,
            "description": "Kaleidoscope paper-intelligence API for downstream agents.",
        },
        "auth": {
            "mode": "server-configured",
            "schemes": [
                {
                    "type": "http",
                    "scheme": "bearer",
                    "required_when": "KALEIDOSCOPE_JWT_SECRET is configured",
                }
            ],
            "scope_model": "tool.scopes lists intended authorization scopes.",
        },
        "limits": {
            "batch_max_calls": 20,
            "default_page_limit": 20,
            "max_tool_result_limit": 50,
            "rate_limit_policy": "deployment-configured",
        },
        "transports": {
            "rest": {
                "base_path": f"{api_base_path}/agent",
                "endpoints": {
                    "manifest": f"{api_base_path}/agent/manifest",
                    "list_tools": f"{api_base_path}/agent/tools",
                    "context_pack": f"{api_base_path}/agent/context-pack",
                    "call_tool": f"{api_base_path}/agent/call",
                    "batch_call": f"{api_base_path}/agent/batch",
                    "evidence_search": f"{api_base_path}/evidence/search",
                    "evidence_packs": f"{api_base_path}/evidence/packs",
                    "claim_verify": f"{api_base_path}/claims/verify",
                    "grounded_answer": f"{api_base_path}/answers/grounded",
                    "batch": f"{api_base_path}/batch",
                    "discovery_delta": f"{api_base_path}/discovery/delta",
                    "federated_search": f"{api_base_path}/search/federated",
                    "jsonl_export": f"{api_base_path}/exports/jsonl",
                },
            }
        },
        "external_integrations": {
            "deepxiv": {
                "status": "proxied",
                "base_path": f"{api_base_path}/deepxiv",
                "source_doc": "docs/memo/deepaxiv_api.md",
            }
        },
        "tools": [_manifest_tool(tool) for tool in TOOLS],
    }


def _manifest_tool(tool: dict[str, Any]) -> dict[str, Any]:
    metadata = _TOOL_METADATA.get(tool["name"], {})
    return {
        "id": f"kaleidoscope.{tool['name']}",
        "name": tool["name"],
        "version": TOOL_VERSION,
        "description": tool["description"],
        "input_schema": deepcopy(tool["parameters"]),
        "output_schema": deepcopy(
            metadata.get("output_schema", _GENERIC_OUTPUT_SCHEMA)
        ),
        "scopes": list(metadata.get("scopes", ["agent:call"])),
        "cost": dict(metadata.get("cost", {"tier": "unknown", "units": 1})),
        "examples": deepcopy(metadata.get("examples", [])),
    }
