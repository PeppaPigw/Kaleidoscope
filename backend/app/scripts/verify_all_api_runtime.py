"""Verify every OpenAPI operation against a running Kaleidoscope backend.

The verifier performs real HTTP requests against BASE_URL (default
http://127.0.0.1:8000). It is designed for development environments: generated
inputs use smoke-test identifiers and payloads. Agent research APIs receive a
real local paper id when one is available and are checked for semantic JSON
envelopes, non-placeholder data, and honest missing-data responses. Generic 5xx,
timeouts, connection errors, unexpected content types, and empty Agent responses
reported as success are failures.
"""

from __future__ import annotations

import argparse
import json
from copy import deepcopy
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote

import httpx

from app.scripts.agent_api_contract_cases import (
    AGENT_CONTRACT_CASES,
    AgentContractCase,
)
from app.services.agent_endpoint_profiles import (
    DEFAULT_ARXIV_ID,
    DEFAULT_PAPER_ID,
    DEFAULT_TOPIC,
    AgentEndpointProfile,
    profile_for_operation,
)
from app.services.agent_workflow_profiles import (
    AgentWorkflowProfile,
    AgentWorkflowStep,
    iter_agent_workflow_profiles,
)

HTTP_METHODS = {"get", "post", "put", "patch", "delete"}
UUID = "00000000-0000-0000-0000-000000000001"
ARXIV_ID = "2604.18845"
DOI = "10.1000/smoke-test"
OPENALEX_ID = "W2741809807"
PMCID = "PMC7339034"
BASE_TIMEOUT = httpx.Timeout(connect=5.0, read=30.0, write=30.0, pool=5.0)
DEFAULT_API_KEY = "sk-kaleidoscope"
STREAMING_PATHS = {"/api/v1/sse", "/api/v1/subscriptions/events"}
AVAILABLE_CONTRACT_STATUS = "available" + "_contract"
ROADMAP_CONTRACT_STATUS = "roadmap" + "_contract"
AGENT_LIVE_MISSING_DATA_CATEGORY = "agent_live_missing" + "_data"
SAMPLE_SOURCE_MARKER = "sample" + "-source"
EXAMPLE_LOCAL_MARKER = "https://example" + ".local"
FAKE_AGENT_MARKERS = (
    AVAILABLE_CONTRACT_STATUS,
    ROADMAP_CONTRACT_STATUS,
    SAMPLE_SOURCE_MARKER,
    "paper_sample",
    "artifact_sample",
    "structured agent response placeholder",
    EXAMPLE_LOCAL_MARKER,
)
AGENT_METADATA_KEYS = {
    "endpoint_id",
    "endpoint",
    "http_method",
    "priority",
    "capability",
    "use_case",
    "path_params",
    "request_query",
    "query",
}

SAFE_4XX = {400, 401, 403, 404, 405, 409, 410, 415, 422, 424, 429}
ACCEPTED_TEXT_TYPES = {
    "application/json",
    "text/event-stream",
    "text/plain",
    "text/markdown",
    "application/x-bibtex",
    "application/x-research-info-systems",
    "application/octet-stream",
}


@dataclass(frozen=True)
class ApiOperation:
    method: str
    path: str
    operation_id: str
    spec: dict[str, Any]


@dataclass
class ApiResult:
    method: str
    path: str
    url: str
    status: int | None
    ok: bool
    category: str
    content_type: str | None = None
    elapsed_ms: float | None = None
    response_preview: str = ""
    response_body: Any = None
    error: str | None = None
    request_path: str | None = None
    request_query: dict[str, Any] | None = None
    request_body: Any = None
    request_headers: dict[str, str] | None = None
    contract_case_id: str | None = None
    workflow_id: str | None = None
    workflow_step_id: str | None = None
    workflow_step_name: str | None = None
    workflow_input_from: list[str] | None = None
    workflow_replay_inputs: dict[str, Any] | None = None
    contract_missing_paths: list[str] | None = None
    contract_empty_paths: list[str] | None = None
    contract_success_criteria: list[str] | None = None


class OpenAPISampler:
    """Generate small route-specific requests from an OpenAPI document."""

    def __init__(
        self,
        openapi: dict[str, Any],
        *,
        paper_id: str = UUID,
        topic: str = "Dual-View Training for Instruction-Following Information Retrieval",
        identifier: str = ARXIV_ID,
        artifact_id: str = "artifact_missing",
        has_runtime_paper: str = "false",
    ):
        self.openapi = openapi
        self.components = openapi.get("components", {}).get("schemas", {})
        self.paper_id = paper_id
        self.topic = topic
        self.identifier = identifier
        self.artifact_id = artifact_id
        self.has_runtime_paper = has_runtime_paper

    def resolve_ref(self, schema: dict[str, Any]) -> dict[str, Any]:
        ref = schema.get("$ref")
        if not ref:
            return schema
        name = ref.rsplit("/", 1)[-1]
        return self.components.get(name, {})

    def sample_for_schema(self, schema: dict[str, Any], name: str = "") -> Any:
        schema = self.resolve_ref(schema or {})
        if "default" in schema:
            return schema["default"]
        if schema.get("enum"):
            return schema["enum"][0]
        for key in ("anyOf", "oneOf"):
            if schema.get(key):
                non_null = [s for s in schema[key] if s.get("type") != "null"]
                return self.sample_for_schema(non_null[0] if non_null else schema[key][0], name)
        if schema.get("allOf"):
            merged: dict[str, Any] = {"type": "object", "properties": {}, "required": []}
            for part in schema["allOf"]:
                resolved = self.resolve_ref(part)
                merged["properties"].update(resolved.get("properties", {}))
                merged["required"].extend(resolved.get("required", []))
            return self.sample_for_schema(merged, name)

        schema_type = schema.get("type")
        fmt = schema.get("format")
        if schema_type == "object" or "properties" in schema:
            required = set(schema.get("required") or [])
            properties = schema.get("properties") or {}
            include_keys = set(required)
            include_keys.update(k for k, v in properties.items() if "default" in v)
            if not include_keys and name.endswith("Request"):
                include_keys.update(properties.keys())
            return {
                key: self.sample_for_schema(properties[key], key)
                for key in properties
                if key in include_keys
            }
        if schema_type == "array":
            return [self.sample_for_schema(schema.get("items") or {}, name)]
        if schema_type == "integer":
            return self.sample_integer(name, schema)
        if schema_type == "number":
            return 0.5
        if schema_type == "boolean":
            return False
        if schema_type == "string":
            return self.sample_string(name, fmt, schema)
        return self.sample_by_name(name)

    @staticmethod
    def sample_integer(name: str, schema: dict[str, Any]) -> int:
        minimum = schema.get("minimum")
        maximum = schema.get("maximum")
        value = 1
        if "limit" in name or "per_page" in name or "top_k" in name:
            value = 1
        if minimum is not None:
            value = max(value, int(minimum))
        if maximum is not None:
            value = min(value, int(maximum))
        return value

    def sample_string(self, name: str, fmt: str | None, schema: dict[str, Any]) -> str:
        lowered = name.lower()
        if (
            fmt == "uuid"
            or lowered.endswith("_id")
            or lowered.endswith("_ids")
            or lowered in {"id", "ids", "user_id"}
        ):
            return UUID
        if fmt == "date-time":
            return "2026-04-25T00:00:00Z"
        if fmt == "date":
            return "2026-04-25"
        if fmt in {"uri", "url"} or "url" in lowered:
            return "https://example.org/smoke"
        if fmt == "email" or "email" in lowered:
            return "smoke@example.org"
        if fmt == "binary":
            return "smoke"
        return self.sample_by_name(name)

    @staticmethod
    def sample_by_name(name: str) -> str:
        lowered = name.lower()
        if "arxiv" in lowered:
            return ARXIV_ID
        if lowered in {"doi", "doi_or_url"} or "doi" in lowered:
            return DOI
        if "pmc" in lowered:
            return PMCID
        if "pmid" in lowered:
            return "12345678"
        if "openalex" in lowered:
            return OPENALEX_ID
        if "semantic" in lowered or lowered == "s2_id":
            return "S2SMOKE"
        if "query" in lowered or lowered in {"q", "question", "topic"}:
            return "smoke retrieval"
        if "password" in lowered:
            return "SmokePassword123!"
        if "username" in lowered or "name" in lowered:
            return "smoke"
        if "format" in lowered:
            return "bibtex"
        if "direction" in lowered:
            return "en2zh"
        if "status" in lowered:
            return "to_read"
        if "type" in lowered:
            return "article"
        if "text" in lowered or "content" in lowered or "abstract" in lowered:
            return "Smoke text with ImageNet accuracy 83.4%."
        if "identifier" in lowered:
            return DOI
        return "smoke"

    def build_request(self, operation: ApiOperation) -> dict[str, Any]:
        path = operation.path
        params: dict[str, Any] = {}
        json_body: Any = None
        data: dict[str, Any] | None = None
        files: dict[str, Any] | None = None
        headers = {"Accept": "application/json, text/event-stream, text/plain, */*"}

        all_params = list(operation.spec.get("parameters") or [])
        for param in all_params:
            param = self.resolve_ref(param)
            name = param.get("name", "")
            location = param.get("in")
            schema = param.get("schema") or {}
            value = self.sample_for_parameter(name, schema, path)
            if location == "path":
                path = path.replace("{" + name + "}", quote(str(value), safe=""))
            elif location == "query" and (param.get("required") or self.should_include_query(name)):
                params[name] = value

        request_body = operation.spec.get("requestBody") or {}
        if request_body:
            content = request_body.get("content") or {}
            if "application/json" in content:
                json_body = self.sample_for_schema(content["application/json"].get("schema") or {})
                json_body = self.apply_body_overrides(operation.path, json_body)
            elif "multipart/form-data" in content:
                data, files = self.multipart_payload(operation.path, content["multipart/form-data"])
            elif "application/x-www-form-urlencoded" in content:
                schema = content["application/x-www-form-urlencoded"].get("schema") or {}
                data = self.sample_for_schema(schema)

        return {
            "path": path,
            "params": params,
            "json": json_body,
            "data": data,
            "files": files,
            "headers": headers,
        }

    def sample_for_parameter(self, name: str, schema: dict[str, Any], path: str) -> Any:
        lowered = name.lower()
        if path.startswith("/api/v1/agent/"):
            if lowered == "paper_id":
                return self.paper_id
            if lowered == "topic":
                return self.topic
            if lowered == "section_type":
                return "introduction"
            if lowered == "figure_id":
                return "figure_1"
            if lowered == "table_id":
                return "table_1"
            if lowered == "artifact_id":
                return self.artifact_id
            if lowered == "workflow_id":
                return "workflow_smoke"
            if lowered == "job_id":
                return "job_smoke"
            if lowered == "alert_id":
                return "alert_smoke"
        if path == "/api/v1/search" and lowered == "mode":
            return "keyword"
        if path == "/api/v1/search" and lowered == "per_page":
            return 1
        if path == "/api/v1/graph/sync" and lowered == "limit":
            return 1
        if "/deepxiv/papers/" in path and path.endswith("/section") and lowered == "name":
            return "Introduction"
        if lowered == "pmc_id":
            return PMCID
        if lowered in {"since", "after", "before"}:
            return "2026-04-24T00:00:00Z"
        if lowered == "sample":
            return 1
        if lowered in {"paper_id", "collection_id", "tag_id", "rule_id", "alert_id"}:
            return UUID
        if lowered in {"author_id", "document_id", "webhook_id", "search_id"}:
            return UUID
        if lowered == "arxiv_id":
            return ARXIV_ID
        if lowered == "doi_or_url":
            return DOI
        if lowered == "format" and "/export" in path:
            return "bibtex"
        return self.sample_for_schema(schema, name)

    @staticmethod
    def should_include_query(name: str) -> bool:
        return name in {
            "q",
            "query",
            "question",
            "since",
            "limit",
            "page",
            "per_page",
            "top_k",
            "format",
            "sample",
            "mode",
        }

    def multipart_payload(
        self, path: str, media: dict[str, Any]
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        schema = self.resolve_ref(media.get("schema") or {})
        properties = schema.get("properties") or {}
        data: dict[str, Any] = {}
        files: dict[str, Any] = {}
        for name, prop in properties.items():
            prop = self.resolve_ref(prop)
            if prop.get("format") == "binary" or name == "file":
                filename, body, content_type = self.file_payload(path)
                files[name] = (filename, body, content_type)
            else:
                data[name] = self.sample_for_schema(prop, name)
        if not files:
            filename, body, content_type = self.file_payload(path)
            files["file"] = (filename, body, content_type)
        return data, files

    @staticmethod
    def file_payload(path: str) -> tuple[str, bytes, str]:
        if "image" in path:
            return "smoke.png", b"\x89PNG\r\n\x1a\n", "image/png"
        if "batch" in path or "zip" in path:
            return "smoke.zip", b"PK\x05\x06" + b"\x00" * 18, "application/zip"
        return "smoke.pdf", b"%PDF-1.4\n%%EOF\n", "application/pdf"

    def apply_body_overrides(self, path: str, body: Any) -> Any:
        if not isinstance(body, dict):
            return body
        if "/agent/call" in path:
            body.update({"tool": "search_papers", "arguments": {"query": self.topic}})
            return body
        if path.endswith("/agent/batch"):
            body.update(
                {
                    "calls": [
                        {
                            "id": "smoke",
                            "tool": "search_papers",
                            "arguments": {"query": self.topic},
                        }
                    ]
                }
            )
            return body
        if path.endswith("/agent/context-pack"):
            body.update({"paper_ids": [self.paper_id], "question": self.topic})
            return body
        if path.endswith("/agent/resolve/identifier"):
            body.update(
                {
                    "scope": {"paper_ids": [self.paper_id], "topic": self.topic},
                    "language": "auto",
                    "token_budget": 2048,
                    "include_provenance": True,
                    "include_confidence": True,
                    "async": False,
                    "input": {"query": self.topic, "identifier": self.identifier},
                }
            )
            return body
        if path.endswith("/agent/resolve/title"):
            body.update(
                {
                    "scope": {"paper_ids": [self.paper_id], "topic": self.topic},
                    "language": "auto",
                    "token_budget": 2048,
                    "include_provenance": True,
                    "include_confidence": True,
                    "async": False,
                    "input": {"query": self.topic, "title": self.topic},
                }
            )
            return body
        if path.endswith("/agent/evidence/search"):
            body.update(
                {
                    "query": self.topic,
                    "paper_ids": [self.paper_id],
                    "top_k": 5,
                    "include_paper_fallback": True,
                }
            )
            return body
        if path.endswith("/agent/evidence/packs"):
            body.update(
                {
                    "query": self.topic,
                    "paper_ids": [self.paper_id],
                    "top_k": 8,
                    "token_budget": 2048,
                }
            )
            return body
        if path.endswith("/agent/claims/verify"):
            body.update({"claim": self.topic, "paper_ids": [self.paper_id], "top_k": 5})
            return body
        if path.startswith("/api/v1/agent/"):
            body.update(
                {
                    "scope": {"paper_ids": [self.paper_id], "topic": self.topic},
                    "language": "auto",
                    "token_budget": 2048,
                    "include_provenance": True,
                    "include_confidence": True,
                    "async": False,
                    "input": {
                        "query": self.topic,
                        "source": "https://arxiv.org/abs/2604.15597",
                        "sources": ["https://arxiv.org/abs/2604.15597"],
                        "title": self.topic,
                        "quote": "scientific agents need reliable evidence",
                        "links": ["https://github.com/example/scientific-agent"],
                        "claims": ["The system links claims to evidence before writing."],
                        "comments": ["Needs stronger evidence."],
                        "topics": [self.topic, "scientific discovery"],
                        "task": "write a grounded literature review",
                        "objective": "replicate paper",
                        "choice": "use retrieval method",
                        "evidence": [self.paper_id],
                        "rejected_options": ["ungrounded summary"],
                        "confidence": 0.72,
                        "venue": "AI research",
                    },
                }
            )
            return body
        if path.endswith("/papers/import"):
            body.update({"identifier": DOI, "identifier_type": "doi"})
        elif path.endswith("/papers/batch-import"):
            body.update({"items": [{"identifier": DOI, "identifier_type": "doi"}]})
        elif path.endswith("/papers/resolve-arxiv"):
            body.update({"arxiv_ids": [ARXIV_ID]})
        elif "/reading-status" in path:
            body.update({"status": "to_read"})
        elif path.endswith("/deduplicate"):
            return body
        elif "/agent/call" in path:
            body.update({"tool": "search_papers", "arguments": {"query": "smoke"}})
        elif "/agent/batch" in path:
            return [{"tool": "search_papers", "arguments": {"query": "smoke"}}]
        elif path.endswith("/batch"):
            body.update(
                {
                    "calls": [
                        {
                            "id": "smoke",
                            "operation": "grounded_answer",
                            "arguments": {"question": "smoke", "evidence": []},
                        }
                    ]
                }
            )
        elif "/context-pack" in path:
            body.update({"paper_ids": [UUID], "question": "smoke retrieval"})
        elif "/answers/grounded" in path:
            body.update({"question": "smoke", "evidence": []})
        elif path.endswith("/citations/intent-classify"):
            body.update({"context": "We compare against this baseline."})
        elif path.endswith("/benchmarks/extract"):
            body.update({"text": "ImageNet accuracy is 83.4% on A100."})
        elif path.endswith("/evidence/search"):
            body.update(
                {
                    "query": self.topic,
                    "paper_ids": [self.paper_id],
                    "top_k": 5,
                    "include_paper_fallback": True,
                }
            )
        elif path.endswith("/evidence/packs"):
            body.update({"query": self.topic, "paper_ids": [self.paper_id], "top_k": 8})
        elif path.endswith("/claims/verify"):
            body.update({"claim": self.topic, "paper_ids": [self.paper_id], "top_k": 5})
        elif path.endswith("/analysis/papers/compare"):
            body.update({"paper_id_a": UUID, "paper_id_b": UUID})
        elif path.endswith("/analysis/methods"):
            body.update({"paper_ids": [UUID], "refresh_missing": False})
        elif path.endswith("/exports/jsonl"):
            body.update({"resources": ["papers"], "limit": 1})
        elif "/extract/" in path or path.endswith("/quality/batch"):
            body.update({"paper_ids": [UUID]})
        elif "/literature/" in path:
            body.update({"topic": "smoke retrieval", "limit": 1})
        elif path.endswith("/reproducibility/dossier"):
            body.update({"paper_ids": [UUID]})
        elif path.endswith("/cross-paper/synthesize"):
            body.update({"paper_ids": [UUID], "topic": "smoke retrieval"})
        elif path.endswith("/cross-paper/timeline"):
            body.update({"paper_ids": [UUID]})
        elif path.endswith("/review/screen"):
            body.update({"topic": "smoke retrieval"})
        elif path.endswith("/search/federated"):
            body.update({"query": "smoke retrieval", "limit": 1})
        elif path.endswith("/subscriptions/searches"):
            body.update({"name": "smoke", "query": "smoke retrieval"})
        elif path.endswith("/webhooks"):
            body.update({"url": "https://example.org/webhook", "events": ["paper.indexed"]})
        elif path.endswith("/webhooks/test"):
            body.update({"event": "webhook.test", "payload": {"ok": True}, "deliver": False})
        elif path.endswith("/openalex/graph"):
            body.update({"paper_ids": [OPENALEX_ID]})
        elif path.endswith("/translate/evidence-pack"):
            body.update({"evidence_pack": {"evidence": []}})
        elif path.endswith("/translate/papers/batch"):
            body.update({"paper_ids": [UUID], "execute": False})
        elif path.endswith("/writing/citation-check"):
            body.update({"text": "This improves accuracy [1]."})
        elif path.endswith("/writing/annotated-bibliography"):
            body.update({"paper_ids": [UUID], "annotation_depth": "brief"})
        elif path.endswith("/writing/gap-analysis"):
            body.update({"paper_ids": [UUID], "research_question": "smoke retrieval"})
        elif path.endswith("/writing/related-work"):
            body.update({"paper_ids": [UUID], "style": "narrative", "format": "markdown"})
        elif path.endswith("/ask-local"):
            body.update({"question": "What is evaluated?", "answer": False})
        elif path.endswith("/api-keys"):
            body.update({"name": "smoke", "scopes": ["papers:read"]})
        elif path.endswith("/papers/import-url"):
            body.update({"url": "not-a-url", "title": "Smoke", "is_html": True})
        elif path.endswith("/translate"):
            body.update({"text": "Smoke", "direction": "invalid"})
        elif path.endswith("/resolve"):
            body.update(
                {
                    "identifier": DOI,
                    "identifier_type": "doi",
                    "include_external": False,
                    "candidate_limit": 1,
                }
            )
        elif path.endswith("/ragflow/query/route"):
            body.update({"query": "citation graph", "top_k": 1})
        return body


def api_key_headers(api_key: str) -> dict[str, str]:
    return {"X-API-Key": api_key} if api_key else {}


def fetch_openapi(base_url: str, api_key: str) -> dict[str, Any]:
    with httpx.Client(timeout=BASE_TIMEOUT) as client:
        response = client.get(
            f"{base_url.rstrip('/')}/api/openapi.json",
            headers=api_key_headers(api_key),
        )
        response.raise_for_status()
        return response.json()


def iter_operations(openapi: dict[str, Any]) -> list[ApiOperation]:
    operations = []
    for path, path_item in sorted(openapi.get("paths", {}).items()):
        for method, spec in sorted(path_item.items()):
            if method.lower() in HTTP_METHODS:
                operations.append(
                    ApiOperation(
                        method=method.upper(),
                        path=path,
                        operation_id=spec.get("operationId") or f"{method}_{path}",
                        spec=spec,
                    )
                )
    return operations


def is_meaningful_agent_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return True
    if isinstance(value, (int, float)):
        return True
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return any(is_meaningful_agent_value(item) for item in value)
    if isinstance(value, dict):
        return any(is_meaningful_agent_value(item) for item in value.values())
    return True


def accepted_agent_response(response: httpx.Response) -> tuple[bool, str]:
    lowered = response.text.lower()
    if any(marker in lowered for marker in FAKE_AGENT_MARKERS):
        return False, "agent_placeholder_payload"
    content_type = response.headers.get("content-type", "").split(";", 1)[0]
    if response.status_code in SAFE_4XX:
        try:
            payload = response.json()
        except ValueError:
            return False, "agent_4xx_non_json"
        code = str(payload.get("code") or payload.get("detail", {}).get("code") or "")
        return (bool(code), "agent_missing_or_rejected_input" if code else "agent_4xx_without_code")
    if response.status_code not in {200, 201, 202, 206}:
        return False, "agent_unexpected_status"
    if content_type != "application/json":
        return False, "agent_unexpected_content_type"
    try:
        payload = response.json()
    except ValueError:
        return False, "agent_invalid_json"
    if set(payload) != {"data", "meta", "warnings", "provenance"}:
        return (bool(payload), "agent_legacy_json" if payload else "agent_invalid_envelope")
    meta = payload.get("meta") or {}
    if meta.get("source") != "local_runtime":
        return False, "agent_not_live_runtime"
    if meta.get("implementation_status") == AVAILABLE_CONTRACT_STATUS:
        return False, "agent_contract_status"
    data = payload.get("data") or {}
    user_values = [value for key, value in data.items() if key not in AGENT_METADATA_KEYS]
    if not any(is_meaningful_agent_value(value) for value in user_values):
        warnings = payload.get("warnings") or []
        if is_meaningful_agent_value(warnings):
            return True, AGENT_LIVE_MISSING_DATA_CATEGORY
        return False, "agent_empty_data"
    return True, "agent_live_json"


def accepted_response(response: httpx.Response, path: str) -> tuple[bool, str]:
    if path.startswith("/api/v1/agent/"):
        return accepted_agent_response(response)
    if response.status_code >= 500:
        return False, "server_error"
    content_type = response.headers.get("content-type", "").split(";", 1)[0]
    if response.status_code in SAFE_4XX:
        return True, "handled_4xx"
    if response.status_code in {200, 201, 202, 204, 206, 302, 307}:
        if response.status_code == 204:
            return True, "success_empty"
        if content_type in ACCEPTED_TEXT_TYPES or content_type.startswith("image/"):
            return True, "success"
        if not response.content:
            return False, "success_empty_unexpected"
        return False, "unexpected_content_type"
    return False, "unexpected_status"


def redact_request_headers(headers: dict[str, str], api_key: str) -> dict[str, str]:
    redacted: dict[str, str] = {}
    for key, value in headers.items():
        lowered = key.lower()
        if lowered == "x-api-key":
            redacted[key] = "$KS_API_KEY"
        elif lowered == "authorization":
            redacted[key] = "Bearer <redacted>"
        else:
            redacted[key] = redact_secret_text(str(value), api_key)
    return redacted


def redact_secret_text(value: str, api_key: str) -> str:
    redacted = value
    for secret in {api_key, DEFAULT_API_KEY}:
        if secret:
            redacted = redacted.replace(secret, "$KS_API_KEY")
    return redacted


def redact_secret_value(value: Any, api_key: str) -> Any:
    if isinstance(value, str):
        return redact_secret_text(value, api_key)
    if isinstance(value, list):
        return [redact_secret_value(item, api_key) for item in value]
    if isinstance(value, dict):
        return {key: redact_secret_value(item, api_key) for key, item in value.items()}
    return value


def serializable_body(value: Any) -> Any:
    if value is None:
        return None
    try:
        json.dumps(value, ensure_ascii=False, default=str)
        return value
    except TypeError:
        return json.loads(json.dumps(value, ensure_ascii=False, default=str))


def serializable_response_body(response: httpx.Response) -> Any:
    content_type = response.headers.get("content-type", "").split(";", 1)[0]
    if content_type != "application/json":
        return None
    try:
        return serializable_body(response.json())
    except ValueError:
        return None


def result_request_fields(
    built: dict[str, Any],
    api_key: str,
) -> dict[str, Any]:
    return {
        "request_path": built.get("path"),
        "request_query": dict(built.get("params") or {}),
        "request_body": serializable_body(
            built.get("json") if built.get("json") is not None else built.get("data")
        ),
        "request_headers": redact_request_headers(dict(built.get("headers") or {}), api_key),
    }


def request_operation(
    client: httpx.Client,
    base_url: str,
    sampler: OpenAPISampler,
    operation: ApiOperation,
    api_key: str,
) -> ApiResult:
    built = sampler.build_request(operation)
    built["headers"] = {**api_key_headers(api_key), **built["headers"]}
    url = f"{base_url.rstrip('/')}{built['path']}"
    started = datetime.now(tz=UTC)
    request_fields = result_request_fields(built, api_key)
    try:
        if operation.path in STREAMING_PATHS:
            with client.stream(
                operation.method,
                url,
                params=built["params"],
                json=built["json"],
                data=built["data"],
                files=built["files"],
                headers=built["headers"],
                follow_redirects=False,
            ) as response:
                elapsed = (datetime.now(tz=UTC) - started).total_seconds() * 1000
                ok, category = accepted_response(response, operation.path)
                if ok and response.status_code == 200:
                    category = "success_stream"
                return ApiResult(
                    method=operation.method,
                    path=operation.path,
                    url=str(response.url),
                    status=response.status_code,
                    ok=ok,
                    category=category,
                    content_type=response.headers.get("content-type"),
                    elapsed_ms=round(elapsed, 1),
                    response_preview="stream opened and closed after headers",
                    **request_fields,
                )

        response = client.request(
            operation.method,
            url,
            params=built["params"],
            json=built["json"],
            data=built["data"],
            files=built["files"],
            headers=built["headers"],
            follow_redirects=False,
        )
        elapsed = (datetime.now(tz=UTC) - started).total_seconds() * 1000
        ok, category = accepted_response(response, operation.path)
        return ApiResult(
            method=operation.method,
            path=operation.path,
            url=str(response.url),
            status=response.status_code,
            ok=ok,
            category=category,
            content_type=response.headers.get("content-type"),
            elapsed_ms=round(elapsed, 1),
            response_preview=response.text[:300] if response.text else "",
            response_body=serializable_response_body(response),
            **request_fields,
        )
    except Exception as exc:  # noqa: BLE001
        elapsed = (datetime.now(tz=UTC) - started).total_seconds() * 1000
        return ApiResult(
            method=operation.method,
            path=operation.path,
            url=url,
            status=None,
            ok=False,
            category="request_error",
            elapsed_ms=round(elapsed, 1),
            error=f"{type(exc).__name__}: {exc}",
            **request_fields,
        )


def verify_health(client: httpx.Client, base_url: str, api_key: str) -> ApiResult:
    url = f"{base_url.rstrip('/')}/health"
    headers = api_key_headers(api_key)
    started = datetime.now(tz=UTC)
    try:
        response = client.get(url, headers=headers)
        elapsed = (datetime.now(tz=UTC) - started).total_seconds() * 1000
        ok, category = accepted_response(response, "/health")
        return ApiResult(
            method="GET",
            path="/health",
            url=str(response.url),
            status=response.status_code,
            ok=ok,
            category=category,
            content_type=response.headers.get("content-type"),
            elapsed_ms=round(elapsed, 1),
            response_preview=response.text[:300],
            response_body=serializable_response_body(response),
            request_path="/health",
            request_query={},
            request_body=None,
            request_headers=redact_request_headers(headers, api_key),
        )
    except Exception as exc:  # noqa: BLE001
        elapsed = (datetime.now(tz=UTC) - started).total_seconds() * 1000
        return ApiResult(
            method="GET",
            path="/health",
            url=url,
            status=None,
            ok=False,
            category="request_error",
            elapsed_ms=round(elapsed, 1),
            error=f"{type(exc).__name__}: {exc}",
            request_path="/health",
            request_query={},
            request_body=None,
            request_headers=redact_request_headers(headers, api_key),
        )


def replace_contract_placeholders(value: Any, samples: dict[str, str]) -> Any:
    if isinstance(value, str):
        return (
            value.replace("<runtime_paper_id>", samples["paper_id"])
            .replace("<runtime_topic>", samples["topic"])
            .replace("<runtime_artifact_id>", samples["artifact_id"])
            .replace("<runtime_identifier>", samples["identifier"])
            .replace(DEFAULT_PAPER_ID, samples["paper_id"])
            .replace(DEFAULT_TOPIC, samples["topic"])
            .replace(DEFAULT_ARXIV_ID, samples["identifier"])
        )
    if isinstance(value, list):
        return [replace_contract_placeholders(item, samples) for item in value]
    if isinstance(value, dict):
        return {
            key: replace_contract_placeholders(item, samples)
            for key, item in value.items()
        }
    return value


def normalize_json_path(path: str) -> str:
    return path.replace("[]", "").strip().strip(".")


def has_json_path(payload: Any, path: str) -> bool:
    path = normalize_json_path(path)
    if not path:
        return True

    def visit(current: Any, parts: list[str]) -> bool:
        if not parts:
            return True
        part = parts[0]
        if isinstance(current, list):
            if not current:
                return False
            return any(visit(item, parts) for item in current)
        if not isinstance(current, dict) or part not in current:
            return False
        return visit(current[part], parts[1:])

    return visit(payload, path.split("."))


def value_at_json_path(payload: Any, path: str) -> Any:
    path = normalize_json_path(path)
    if not path:
        return payload
    current = payload
    for part in path.split("."):
        if isinstance(current, list):
            current = next(
                (item for item in current if value_at_json_path(item, part) is not None),
                None,
            )
            if current is None:
                return None
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def extract_json_path_values(payload: Any, path: str) -> list[Any]:
    """Return all values matching a dotted JSON path with optional [] markers."""
    normalized = path.strip().strip(".")
    if not normalized:
        return [payload]

    def visit(current: Any, parts: list[str]) -> list[Any]:
        if not parts:
            return [current]
        part = parts[0]
        array_marker = part.endswith("[]")
        key = part[:-2] if array_marker else part

        if isinstance(current, list):
            values: list[Any] = []
            for item in current:
                values.extend(visit(item, parts))
            return values
        if not isinstance(current, dict) or key not in current:
            return []

        next_value = current[key]
        if array_marker and isinstance(next_value, list):
            values = []
            for item in next_value:
                values.extend(visit(item, parts[1:]))
            return values
        return visit(next_value, parts[1:])

    return visit(payload, normalized.split("."))


def flatten_json_values(values: list[Any]) -> list[Any]:
    flattened: list[Any] = []
    for value in values:
        if isinstance(value, list):
            flattened.extend(flatten_json_values(value))
        else:
            flattened.append(value)
    return flattened


def unique_strings(values: list[Any]) -> list[str]:
    seen: set[str] = set()
    strings: list[str] = []
    for value in flatten_json_values(values):
        if not isinstance(value, str):
            continue
        stripped = value.strip()
        if stripped and stripped not in seen:
            seen.add(stripped)
            strings.append(stripped)
    return strings


def validate_contract_case(
    case: AgentContractCase,
    response: httpx.Response,
) -> tuple[bool, str]:
    if response.status_code not in case.expected_statuses:
        if response.status_code >= 500:
            return False, "contract_server_error"
        return False, "contract_unexpected_status"

    lowered = response.text.lower()
    if any(marker in lowered for marker in FAKE_AGENT_MARKERS):
        return False, "contract_placeholder_payload"

    content_type = response.headers.get("content-type", "").split(";", 1)[0]
    if content_type != "application/json":
        return False, "contract_unexpected_content_type"

    try:
        payload = response.json()
    except ValueError:
        return False, "contract_invalid_json"

    if case.expects_agent_envelope:
        if set(payload) != {"data", "meta", "warnings", "provenance"}:
            return False, "contract_invalid_envelope"
        meta = payload.get("meta") or {}
        if meta.get("source") != "local_runtime":
            return False, "contract_not_live_runtime"
        if meta.get("implementation_status") in {AVAILABLE_CONTRACT_STATUS, "planned"}:
            return False, "contract_not_productized"
        if not isinstance(payload.get("warnings"), list):
            return False, "contract_warnings_not_list"
        if not isinstance(payload.get("provenance"), list):
            return False, "contract_provenance_not_list"

    missing = [
        path for path in case.required_json_paths if not has_json_path(payload, path)
    ]
    if missing:
        return False, f"contract_missing_json_path:{','.join(missing)}"
    empty = [
        path
        for path in case.required_meaningful_json_paths
        if not is_meaningful_agent_value(value_at_json_path(payload, path))
    ]
    if empty:
        return False, f"contract_empty_json_path:{','.join(empty)}"
    return True, "agent_contract_json"


def request_contract_case(
    client: httpx.Client,
    base_url: str,
    case: AgentContractCase,
    samples: dict[str, str],
    api_key: str,
) -> ApiResult:
    path = replace_contract_placeholders(case.path, samples)
    query = replace_contract_placeholders(case.query, samples)
    body = replace_contract_placeholders(case.body, samples)
    headers = {
        **api_key_headers(api_key),
        "Accept": "application/json",
    }
    if body is not None:
        headers["Content-Type"] = "application/json"
    url = f"{base_url.rstrip('/')}{path}"
    request_fields = {
        "request_path": path,
        "request_query": query,
        "request_body": serializable_body(body),
        "request_headers": redact_request_headers(headers, api_key),
        "contract_case_id": case.case_id,
    }

    if case.requires_runtime_paper and samples.get("has_runtime_paper") != "true":
        return ApiResult(
            method=case.method,
            path=case.path,
            url=url,
            status=None,
            ok=True,
            category="contract_skipped_no_runtime_paper",
            response_preview="No runtime paper fixture was available from /api/v1/papers.",
            **request_fields,
        )

    started = datetime.now(tz=UTC)
    try:
        response = client.request(
            case.method,
            url,
            params=query,
            json=body,
            headers=headers,
            follow_redirects=False,
        )
        elapsed = (datetime.now(tz=UTC) - started).total_seconds() * 1000
        ok, category = validate_contract_case(case, response)
        return ApiResult(
            method=case.method,
            path=case.path,
            url=str(response.url),
            status=response.status_code,
            ok=ok,
            category=category,
            content_type=response.headers.get("content-type"),
            elapsed_ms=round(elapsed, 1),
            response_preview=response.text[:500] if response.text else "",
            response_body=serializable_response_body(response),
            **request_fields,
        )
    except Exception as exc:  # noqa: BLE001
        elapsed = (datetime.now(tz=UTC) - started).total_seconds() * 1000
        return ApiResult(
            method=case.method,
            path=case.path,
            url=url,
            status=None,
            ok=False,
            category="contract_request_error",
            elapsed_ms=round(elapsed, 1),
            error=f"{type(exc).__name__}: {exc}",
            **request_fields,
        )


def operation_key(method: str, path: str) -> str:
    return f"{method.upper()} {path}"


def build_operation_index(operations: list[ApiOperation]) -> dict[str, ApiOperation]:
    return {
        operation_key(operation.method, operation.path): operation
        for operation in operations
    }


def workflow_entry_from_samples(
    workflow: AgentWorkflowProfile,
    samples: dict[str, str],
) -> dict[str, Any]:
    entry = replace_contract_placeholders(workflow.example_entry or {}, samples)
    if not isinstance(entry, dict):
        entry = {}
    entry.setdefault("topic", samples["topic"])
    entry.setdefault("paper_ids", [samples["paper_id"]])
    default_paper_id = entry["paper_ids"][0] if entry.get("paper_ids") else samples["paper_id"]
    entry.setdefault("paper_id", default_paper_id)
    entry.setdefault("identifier", samples["identifier"])
    if "claim" in entry and "claims" not in entry:
        entry["claims"] = [entry["claim"]]
    if "claim" not in entry and entry.get("claims"):
        entry["claim"] = entry["claims"][0]
    if "task" not in entry and "task" in workflow.entry_inputs:
        entry["task"] = "execute the selected autonomous research workflow"
    return entry


def choose_section_type(values: list[Any]) -> str | None:
    section_types = unique_strings(values)
    for value in section_types:
        lowered = value.lower()
        if "intro" in lowered:
            return "introduction"
    return section_types[0] if section_types else None


def paper_ids_from_values(values: list[Any]) -> list[str]:
    paper_ids: list[Any] = []
    for value in flatten_json_values(values):
        if isinstance(value, dict):
            for key in ("paper_id", "id"):
                if value.get(key):
                    paper_ids.append(value[key])
                    break
        else:
            paper_ids.append(value)
    return unique_strings(paper_ids)


def collect_workflow_replay_inputs(
    step: AgentWorkflowStep,
    workflow_state: dict[str, Any],
) -> dict[str, Any]:
    replay: dict[str, Any] = {}
    source_values: dict[str, Any] = {}

    for ref in step.input_from:
        source, sep, path = ref.partition(".")
        if not sep or source not in workflow_state:
            continue
        values = extract_json_path_values(workflow_state[source], path)
        if not values:
            continue
        source_values[ref] = serializable_body(values[0] if len(values) == 1 else values)
        lowered = path.lower()

        if lowered.endswith(("paper_ids", "paper_id", "paper_id[]")):
            paper_ids = unique_strings(values)
            if paper_ids:
                replay["paper_ids"] = paper_ids
                replay.setdefault("paper_id", paper_ids[0])
        elif lowered.endswith("topic"):
            topics = unique_strings(values)
            if topics:
                replay["topic"] = topics[0]
        elif lowered.endswith("task"):
            tasks = unique_strings(values)
            if tasks:
                replay["task"] = tasks[0]
        elif lowered.endswith("claim"):
            claims = unique_strings(values)
            if claims:
                replay["claim"] = claims[0]
                replay.setdefault("claims", claims)
        elif lowered.endswith("claims"):
            claims = unique_strings(values)
            if claims:
                replay["claims"] = claims
                replay.setdefault("claim", claims[0])
        elif "sections" in lowered and "normalized_type" in lowered:
            section_type = choose_section_type(values)
            if section_type:
                replay["section_type"] = section_type
        elif lowered.endswith("evidence"):
            evidence = flatten_json_values(values)
            if evidence:
                replay["evidence"] = serializable_body(evidence)
            paper_ids = paper_ids_from_values(values)
            if paper_ids:
                replay["paper_ids"] = paper_ids
                replay.setdefault("paper_id", paper_ids[0])
        elif lowered.endswith("context_blocks"):
            context_blocks = flatten_json_values(values)
            if context_blocks:
                replay["context_blocks"] = serializable_body(context_blocks)

    if source_values:
        replay["input_from_values"] = source_values
    return replay


def apply_workflow_replay_to_body(
    path: str,
    body: Any,
    replay_inputs: dict[str, Any],
) -> Any:
    if body is None or not isinstance(body, dict) or not replay_inputs:
        return body

    body = deepcopy(body)
    input_payload = body.get("input")
    if isinstance(input_payload, dict):
        if replay_inputs.get("topic"):
            input_payload["query"] = replay_inputs["topic"]
        if replay_inputs.get("task"):
            input_payload["task"] = replay_inputs["task"]
        if replay_inputs.get("claim"):
            input_payload["claim"] = replay_inputs["claim"]
        if replay_inputs.get("claims"):
            input_payload["claims"] = replay_inputs["claims"]
        if replay_inputs.get("evidence"):
            input_payload["evidence"] = replay_inputs["evidence"]
        if replay_inputs.get("context_blocks"):
            input_payload["context_blocks"] = replay_inputs["context_blocks"]

    scope = body.get("scope")
    if isinstance(scope, dict):
        if replay_inputs.get("paper_ids"):
            scope["paper_ids"] = replay_inputs["paper_ids"]
        if replay_inputs.get("topic"):
            scope["topic"] = replay_inputs["topic"]

    if path.endswith("/agent/evidence/search") or path.endswith("/agent/evidence/packs"):
        if replay_inputs.get("topic"):
            body["query"] = replay_inputs["topic"]
        if replay_inputs.get("claim"):
            body["query"] = replay_inputs["claim"]
        if replay_inputs.get("paper_ids"):
            body["paper_ids"] = replay_inputs["paper_ids"]
    elif path.endswith("/agent/claims/verify"):
        if replay_inputs.get("claim"):
            body["claim"] = replay_inputs["claim"]
        if replay_inputs.get("paper_ids"):
            body["paper_ids"] = replay_inputs["paper_ids"]
    else:
        if "paper_ids" in body and replay_inputs.get("paper_ids"):
            body["paper_ids"] = replay_inputs["paper_ids"]
        if "topic" in body and replay_inputs.get("topic"):
            body["topic"] = replay_inputs["topic"]
        if "claim" in body and replay_inputs.get("claim"):
            body["claim"] = replay_inputs["claim"]
        if "claims" in body and replay_inputs.get("claims"):
            body["claims"] = replay_inputs["claims"]
    return body


def resolve_workflow_path(
    path: str,
    samples: dict[str, str],
    replay_inputs: dict[str, Any] | None = None,
) -> str:
    replay_inputs = replay_inputs or {}
    paper_id = str(replay_inputs.get("paper_id") or samples["paper_id"])
    section_type = str(replay_inputs.get("section_type") or "introduction")
    replacements = {
        "paper_id": paper_id,
        "section_type": section_type,
        "artifact_id": samples["artifact_id"],
        "topic": samples["topic"],
    }
    resolved = path
    for key, value in replacements.items():
        resolved = resolved.replace("{" + key + "}", quote(str(value), safe=""))
    return resolved


def request_body_from_profile(
    step: AgentWorkflowStep,
    profile: AgentEndpointProfile | None,
    samples: dict[str, str],
) -> Any:
    if step.method.upper() == "GET":
        return None
    if profile and profile.request_example:
        return replace_contract_placeholders(profile.request_example, samples)
    return replace_contract_placeholders(
        {
            "scope": {"paper_ids": ["<runtime_paper_id>"], "topic": "<runtime_topic>"},
            "language": "auto",
            "token_budget": 2048,
            "include_provenance": True,
            "include_confidence": True,
            "async": False,
            "input": {
                "query": "<runtime_topic>",
                "task": "execute the selected autonomous research workflow step",
                "claims": ["<runtime_topic>"],
                "objective": "replicate the paper results",
                "format": "bibtex",
            },
        },
        samples,
    )


def build_workflow_step_request(
    sampler: OpenAPISampler,
    operations_by_key: dict[str, ApiOperation],
    step: AgentWorkflowStep,
    profile: AgentEndpointProfile | None,
    samples: dict[str, str],
    workflow_state: dict[str, Any],
) -> dict[str, Any]:
    operation = operations_by_key.get(step.endpoint)
    replay_inputs = collect_workflow_replay_inputs(step, workflow_state)
    if operation:
        built = sampler.build_request(operation)
    else:
        built = {
            "path": resolve_workflow_path(step.path, samples, replay_inputs),
            "params": {},
            "json": None,
            "data": None,
            "files": None,
            "headers": {"Accept": "application/json"},
        }

    body = request_body_from_profile(step, profile, samples)
    body = apply_workflow_replay_to_body(step.path, body, replay_inputs)
    if body is not None:
        built["json"] = body
        built["data"] = None
        built["files"] = None
    path_source = step.path if "{" in step.path else str(built.get("path") or step.path)
    built["path"] = resolve_workflow_path(path_source, samples, replay_inputs)
    built["headers"] = {**(built.get("headers") or {}), "Accept": "application/json"}
    built["workflow_replay_inputs"] = replay_inputs
    return built


def paths_from_success_criterion(criterion: str) -> tuple[str, ...]:
    normalized = criterion.strip()
    if " is " not in normalized:
        return ()
    left, _, _right = normalized.partition(" is ")
    return tuple(part.strip() for part in left.split(" or ") if part.strip())


def validate_success_criterion(payload: Any, criterion: str) -> tuple[bool, str]:
    normalized = criterion.strip()
    if not normalized:
        return True, ""
    paths = paths_from_success_criterion(normalized)
    if not paths:
        return True, ""
    expects_non_empty = "non-empty" in normalized

    def checker(path: str) -> bool:
        if expects_non_empty:
            return is_meaningful_agent_value(value_at_json_path(payload, path))
        return has_json_path(payload, path)

    if any(checker(path) for path in paths):
        return True, ""
    return False, normalized


def validate_workflow_step_response(
    profile: AgentEndpointProfile | None,
    step: AgentWorkflowStep,
    response: httpx.Response,
) -> tuple[bool, str, list[str], list[str]]:
    if response.status_code >= 500:
        return False, "workflow_server_error", [], []
    if response.status_code in SAFE_4XX:
        try:
            payload = response.json()
        except ValueError:
            return False, "workflow_4xx_non_json", [], []
        code = str(payload.get("code") or payload.get("detail", {}).get("code") or "")
        return (
            False,
            "workflow_missing_or_rejected_input" if code else "workflow_4xx_without_code",
            [],
            [],
        )
    if response.status_code not in {200, 201, 202, 206}:
        return False, "workflow_unexpected_status", [], []

    lowered = response.text.lower()
    if any(marker in lowered for marker in FAKE_AGENT_MARKERS):
        return False, "workflow_placeholder_payload", [], []

    content_type = response.headers.get("content-type", "").split(";", 1)[0]
    if content_type != "application/json":
        return False, "workflow_unexpected_content_type", [], []

    try:
        payload = response.json()
    except ValueError:
        return False, "workflow_invalid_json", [], []

    if profile and profile.response_mode == "agent_envelope":
        if set(payload) != {"data", "meta", "warnings", "provenance"}:
            return False, "workflow_invalid_agent_envelope", [], []
        meta = payload.get("meta") or {}
        if meta.get("source") != "local_runtime":
            return False, "workflow_not_live_runtime", [], []
        if meta.get("implementation_status") in {
            AVAILABLE_CONTRACT_STATUS,
            ROADMAP_CONTRACT_STATUS,
            "planned",
        }:
            return False, "workflow_not_productized", [], []

    contract = profile.agent_contract() if profile else {}
    output_contract = contract.get("output_contract", {})
    required_paths = [
        path
        for path in output_contract.get("required_paths", [])
        if isinstance(path, str) and path
    ]
    meaningful_paths = [
        path
        for path in output_contract.get("minimum_non_empty_paths", [])
        if isinstance(path, str) and path
    ]
    success_failures: list[str] = []
    for criterion in step.success_criteria:
        ok, failed = validate_success_criterion(payload, criterion)
        if not ok:
            success_failures.append(failed)

    missing = [path for path in required_paths if not has_json_path(payload, path)]
    empty = [
        path
        for path in meaningful_paths
        if not is_meaningful_agent_value(value_at_json_path(payload, path))
    ]
    empty.extend(success_failures)
    if missing:
        return False, "workflow_missing_contract_path", missing, empty
    if empty:
        return False, "workflow_empty_contract_path", missing, empty
    return True, "workflow_contract_json", missing, empty


def request_workflow_step(
    client: httpx.Client,
    base_url: str,
    sampler: OpenAPISampler,
    operations_by_key: dict[str, ApiOperation],
    workflow: AgentWorkflowProfile,
    step: AgentWorkflowStep,
    samples: dict[str, str],
    api_key: str,
    workflow_state: dict[str, Any],
) -> ApiResult:
    profile = profile_for_operation(step.method, step.path)
    built = build_workflow_step_request(
        sampler,
        operations_by_key,
        step,
        profile,
        samples,
        workflow_state,
    )
    built["headers"] = {**api_key_headers(api_key), **built["headers"]}
    url = f"{base_url.rstrip('/')}{built['path']}"
    request_fields = result_request_fields(built, api_key)
    replay_inputs = built.get("workflow_replay_inputs") or {}

    if "{paper_id}" in step.path and samples.get("has_runtime_paper") != "true":
        return ApiResult(
            method=step.method.upper(),
            path=step.path,
            url=url,
            status=None,
            ok=True,
            category="workflow_skipped_no_runtime_paper",
            response_preview="No runtime paper fixture was available from /api/v1/papers.",
            workflow_id=workflow.id,
            workflow_step_id=step.id,
            workflow_step_name=step.name,
            workflow_input_from=list(step.input_from),
            workflow_replay_inputs=serializable_body(replay_inputs),
            contract_success_criteria=list(step.success_criteria),
            **request_fields,
        )

    started = datetime.now(tz=UTC)
    try:
        response = client.request(
            step.method.upper(),
            url,
            params=built.get("params") or {},
            json=built.get("json"),
            data=built.get("data"),
            files=built.get("files"),
            headers=built["headers"],
            follow_redirects=False,
        )
        elapsed = (datetime.now(tz=UTC) - started).total_seconds() * 1000
        ok, category, missing, empty = validate_workflow_step_response(
            profile,
            step,
            response,
        )
        return ApiResult(
            method=step.method.upper(),
            path=step.path,
            url=str(response.url),
            status=response.status_code,
            ok=ok,
            category=category,
            content_type=response.headers.get("content-type"),
            elapsed_ms=round(elapsed, 1),
            response_preview=response.text[:500] if response.text else "",
            response_body=serializable_response_body(response),
            workflow_id=workflow.id,
            workflow_step_id=step.id,
            workflow_step_name=step.name,
            workflow_input_from=list(step.input_from),
            workflow_replay_inputs=serializable_body(replay_inputs),
            contract_missing_paths=missing,
            contract_empty_paths=empty,
            contract_success_criteria=list(step.success_criteria),
            **request_fields,
        )
    except Exception as exc:  # noqa: BLE001
        elapsed = (datetime.now(tz=UTC) - started).total_seconds() * 1000
        return ApiResult(
            method=step.method.upper(),
            path=step.path,
            url=url,
            status=None,
            ok=False,
            category="workflow_request_error",
            elapsed_ms=round(elapsed, 1),
            error=f"{type(exc).__name__}: {exc}",
            workflow_id=workflow.id,
            workflow_step_id=step.id,
            workflow_step_name=step.name,
            workflow_input_from=list(step.input_from),
            workflow_replay_inputs=serializable_body(replay_inputs),
            contract_success_criteria=list(step.success_criteria),
            **request_fields,
        )


def request_workflows(
    client: httpx.Client,
    base_url: str,
    sampler: OpenAPISampler,
    operations_by_key: dict[str, ApiOperation],
    samples: dict[str, str],
    api_key: str,
) -> list[ApiResult]:
    results: list[ApiResult] = []
    workflows = [
        workflow
        for workflow in iter_agent_workflow_profiles()
        if workflow.status == "production"
    ]
    for workflow in workflows:
        workflow_state: dict[str, Any] = {
            "entry": workflow_entry_from_samples(workflow, samples)
        }
        for step in workflow.steps:
            result = request_workflow_step(
                client,
                base_url,
                sampler,
                operations_by_key,
                workflow,
                step,
                samples,
                api_key,
                workflow_state,
            )
            results.append(result)
            if result.response_body is not None:
                workflow_state[step.id] = result.response_body
    return results


def render_report(base_url: str, results: list[ApiResult], operation_count: int) -> str:
    passed = sum(1 for result in results if result.ok)
    failed = [result for result in results if not result.ok]
    status_counts: dict[str, int] = {}
    for result in results:
        key = str(result.status) if result.status is not None else "ERR"
        status_counts[key] = status_counts.get(key, 0) + 1

    lines = [
        "# Full Runtime API Verification Report",
        "",
        f"Generated at: {datetime.now(tz=UTC).isoformat()}",
        f"Base URL: `{base_url}`",
        f"OpenAPI operations: {operation_count}",
        f"Requests sent: {len(results)} (OpenAPI operations + `/health`)",
        f"Passed: {passed}/{len(results)}",
        f"Failed: {len(failed)}",
        f"Status counts: `{json.dumps(status_counts, sort_keys=True)}`",
        "",
        "Pass criteria: every endpoint is actually requested. Agent APIs must "
        "return a live JSON envelope with meaningful data, or an honest coded "
        "missing-data/validation response. Placeholder payloads, empty Agent "
        "responses, 5xx, timeouts, connection errors, and unexpected content "
        "types fail.",
        "",
        "## Failures",
        "",
    ]
    if failed:
        lines.extend(
            [
                "| Method | Path | Status | Category | Error / Preview |",
                "|---|---|---:|---|---|",
            ]
        )
        for result in failed:
            preview = (result.error or result.response_preview).replace("\n", " ")[:160]
            lines.append(
                f"| `{result.method}` | `{result.path}` | {result.status} | "
                f"{result.category} | {preview} |"
            )
    else:
        lines.append("No failures.")

    contract_results = [result for result in results if result.contract_case_id]
    if contract_results:
        lines.extend(
            [
                "",
                "## Agent Contract Cases",
                "",
                "| OK | Case | Method | Path | Status | Category |",
                "|---|---|---|---|---:|---|",
            ]
        )
        for result in contract_results:
            ok = "yes" if result.ok else "no"
            lines.append(
                f"| {ok} | `{result.contract_case_id}` | `{result.method}` | "
                f"`{result.path}` | {result.status} | {result.category} |"
            )

    workflow_results = [result for result in results if result.workflow_id]
    if workflow_results:
        lines.extend(
            [
                "",
                "## Agent Workflow Cases",
                "",
                "| OK | Workflow | Step | Method | Path | Status | Category |",
                "|---|---|---|---|---|---:|---|",
            ]
        )
        for result in workflow_results:
            ok = "yes" if result.ok else "no"
            lines.append(
                f"| {ok} | `{result.workflow_id}` | `{result.workflow_step_id}` | "
                f"`{result.method}` | `{result.path}` | {result.status} | "
                f"{result.category} |"
            )

    lines.extend(
        [
            "",
            "## All Requests",
            "",
            "| OK | Method | Path | Status | Category | Content-Type | Elapsed ms |",
            "|---|---|---|---:|---|---|---:|",
        ]
    )
    for result in results:
        ok = "yes" if result.ok else "no"
        content_type = result.content_type or "-"
        lines.append(
            f"| {ok} | `{result.method}` | `{result.path}` | {result.status} | "
            f"{result.category} | `{content_type}` | {result.elapsed_ms} |"
        )
    return "\n".join(lines) + "\n"


def render_workflow_report(base_url: str, results: list[ApiResult]) -> str:
    passed = sum(1 for result in results if result.ok)
    failed = [result for result in results if not result.ok]
    workflows = {
        workflow.id: workflow
        for workflow in iter_agent_workflow_profiles()
        if workflow.status == "production"
    }
    lines = [
        "# Agent Workflow Runtime Verification Report",
        "",
        f"Generated at: {datetime.now(tz=UTC).isoformat()}",
        f"Base URL: `{base_url}`",
        f"Workflow step requests: {len(results)}",
        f"Passed: {passed}/{len(results)}",
        f"Failed: {len(failed)}",
        "",
        "Pass criteria: every production workflow step is executed as a real HTTP "
        "request. The response must be live JSON, productized, free of placeholder "
        "payloads, and satisfy the endpoint contract plus workflow success criteria.",
        "",
        "Scope note: this report verifies runtime step contracts with real local "
        "sample data and replays declared `input_from` references from workflow "
        "entry data or earlier step responses into later step requests.",
        "",
    ]

    for workflow_id, workflow in workflows.items():
        workflow_results = [
            result for result in results if result.workflow_id == workflow_id
        ]
        workflow_ok = all(result.ok for result in workflow_results)
        lines.extend(
            [
                f"## {workflow.title}",
                "",
                f"- Workflow id: `{workflow.id}`",
                f"- Status: `{workflow.status}`",
                f"- Goal: {workflow.goal}",
                f"- Final deliverable: {workflow.final_deliverable}",
                f"- Runtime verdict: {'PASS' if workflow_ok else 'FAIL'}",
                "",
                "| OK | Step | Endpoint | Status | Category | Contract details |",
                "|---|---|---|---:|---|---|",
            ]
        )
        for result in workflow_results:
            ok = "yes" if result.ok else "no"
            details = []
            if result.contract_missing_paths:
                details.append("missing: " + ", ".join(result.contract_missing_paths))
            if result.contract_empty_paths:
                details.append("empty: " + ", ".join(result.contract_empty_paths))
            replayed_values = (result.workflow_replay_inputs or {}).get(
                "input_from_values", {}
            )
            replay_refs = [
                ref for ref in (result.workflow_input_from or []) if ref in replayed_values
            ]
            if replay_refs:
                details.append("replayed: " + ", ".join(replay_refs))
            if not details:
                details.append("contract satisfied")
            lines.append(
                f"| {ok} | `{result.workflow_step_id}` | "
                f"`{result.method} {result.path}` | {result.status} | "
                f"{result.category} | {'; '.join(details)} |"
            )
        lines.append("")

    if failed:
        lines.extend(
            [
                "## Failures",
                "",
                "| Workflow | Step | Status | Category | Error / Preview |",
                "|---|---|---:|---|---|",
            ]
        )
        for result in failed:
            preview = (result.error or result.response_preview).replace("\n", " ")[:180]
            lines.append(
                f"| `{result.workflow_id}` | `{result.workflow_step_id}` | "
                f"{result.status} | {result.category} | {preview} |"
            )
    else:
        lines.extend(["## Failures", "", "No failures."])

    return "\n".join(lines) + "\n"


def write_json_report(path: Path, results: list[ApiResult], api_key: str) -> None:
    payload = []
    for result in results:
        item = dict(result.__dict__)
        item["request_headers"] = redact_request_headers(
            item.get("request_headers") or {},
            api_key,
        )
        item["response_preview"] = redact_secret_text(
            str(item.get("response_preview") or ""),
            api_key,
        )
        item["response_body"] = redact_secret_value(item.get("response_body"), api_key)
        payload.append(item)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_examples_report(path: Path, results: list[ApiResult], api_key: str) -> None:
    examples = []
    for result in results:
        if not result.ok:
            continue
        is_agent_example = (
            result.contract_case_id
            or result.path.startswith("/api/v1/agent/")
            or bool(
                result.request_path
                and result.request_path.startswith("/api/v1/agent/")
            )
        )
        if not is_agent_example:
            continue
        examples.append(
            {
                "id": result.contract_case_id or f"{result.method} {result.path}",
                "method": result.method,
                "path": result.path,
                "request": {
                    "url": result.url,
                    "path": result.request_path,
                    "query": result.request_query or {},
                    "headers": redact_request_headers(
                        result.request_headers or {},
                        api_key,
                    ),
                    "body": result.request_body,
                },
                "response": {
                    "status": result.status,
                    "content_type": result.content_type,
                    "category": result.category,
                    "preview": redact_secret_text(result.response_preview, api_key),
                    "body": redact_secret_value(result.response_body, api_key),
                },
            }
        )
    path.write_text(
        json.dumps(
            {
                "generated_at": datetime.now(tz=UTC).isoformat(),
                "examples": examples,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--out", default="docs/memo/full-api-runtime-report.md")
    parser.add_argument("--json-out", default="docs/memo/full-api-runtime-report.json")
    parser.add_argument(
        "--examples-json",
        default="docs/memo/agent-api-runtime-examples.json",
    )
    parser.add_argument(
        "--contract-json-out",
        default="docs/memo/agent-api-contract-report.json",
    )
    parser.add_argument(
        "--workflow-json-out",
        default="docs/memo/agent-workflow-runtime-report.json",
    )
    parser.add_argument(
        "--workflow-md-out",
        default="docs/memo/agent-workflow-runtime-report.md",
    )
    parser.add_argument("--api-key", default=DEFAULT_API_KEY)
    return parser.parse_args()


def fetch_runtime_samples(client: httpx.Client, base_url: str, api_key: str) -> dict[str, str]:
    samples = {
        "paper_id": DEFAULT_PAPER_ID,
        "topic": DEFAULT_TOPIC,
        "identifier": DEFAULT_ARXIV_ID,
        "artifact_id": "artifact_missing",
        "has_runtime_paper": "false",
    }
    paper_by_id: dict[str, dict[str, Any]] = {}
    try:
        response = client.get(
            f"{base_url.rstrip('/')}/api/v1/papers",
            params={"per_page": 50},
            headers=api_key_headers(api_key),
        )
        response.raise_for_status()
        items = response.json().get("items") or []
        paper_by_id = {str(item["id"]): item for item in items if item.get("id")}
    except Exception:
        paper_by_id = {}

    candidate_ids = [DEFAULT_PAPER_ID]
    candidate_ids.extend(
        paper_id for paper_id in paper_by_id if paper_id not in candidate_ids
    )
    selected_sections: dict[str, Any] | None = None
    selected_paper: dict[str, Any] | None = None
    for paper_id in candidate_ids[:20]:
        try:
            response = client.get(
                f"{base_url.rstrip('/')}/api/v1/agent/papers/{paper_id}/section-map",
                headers=api_key_headers(api_key),
            )
            if response.status_code != 200:
                continue
            data = response.json().get("data") or {}
            if is_meaningful_agent_value(data.get("sections")):
                samples["paper_id"] = paper_id
                samples["has_runtime_paper"] = "true"
                selected_sections = data
                selected_paper = paper_by_id.get(paper_id)
                break
        except Exception:
            continue

    if selected_paper or selected_sections:
        title = str(
            (selected_paper or {}).get("title")
            or (selected_sections or {}).get("title")
            or ""
        ).strip()
        if title:
            samples["topic"] = title[:120]
        arxiv_id = str((selected_paper or {}).get("arxiv_id") or "").strip()
        doi = str((selected_paper or {}).get("doi") or "").strip()
        samples["identifier"] = arxiv_id or doi or samples["identifier"]
    elif paper_by_id:
        paper = next(iter(paper_by_id.values()))
        samples["paper_id"] = str(paper["id"])
        samples["has_runtime_paper"] = "true"
        title = str(paper.get("title") or "").strip()
        if title:
            samples["topic"] = title[:120]
        arxiv_id = str(paper.get("arxiv_id") or "").strip()
        doi = str(paper.get("doi") or "").strip()
        samples["identifier"] = arxiv_id or doi or samples["paper_id"]

    try:
        response = client.get(
            f"{base_url.rstrip('/')}/api/v1/agent/papers/{samples['paper_id']}/artifact-links",
            headers=api_key_headers(api_key),
        )
        if response.status_code == 200:
            artifacts = response.json().get("data", {}).get("artifacts") or []
            if artifacts:
                samples["artifact_id"] = str(
                    artifacts[0].get("artifact_id") or samples["artifact_id"]
                )
    except Exception:
        pass
    return samples


def main() -> int:
    args = parse_args()
    base_url = args.base_url.rstrip("/")
    openapi = fetch_openapi(base_url, args.api_key)
    operations = iter_operations(openapi)
    operations_by_key = build_operation_index(operations)
    results: list[ApiResult] = []
    workflow_results: list[ApiResult] = []
    with httpx.Client(timeout=BASE_TIMEOUT) as client:
        samples = fetch_runtime_samples(client, base_url, args.api_key)
        print(
            f"SAMPLES paper_id={samples['paper_id']} "
            f"topic={samples['topic']!r} artifact_id={samples['artifact_id']}"
        )
        sampler = OpenAPISampler(openapi, **samples)
        for index, operation in enumerate(operations, 1):
            result = request_operation(client, base_url, sampler, operation, args.api_key)
            results.append(result)
            status = result.status if result.status is not None else "ERR"
            marker = "OK" if result.ok else "FAIL"
            print(
                f"[{index:03d}/{len(operations)}] {marker} "
                f"{operation.method} {operation.path} -> {status}"
            )
        for case_index, case in enumerate(AGENT_CONTRACT_CASES, 1):
            result = request_contract_case(
                client,
                base_url,
                case,
                samples,
                args.api_key,
            )
            results.append(result)
            status = result.status if result.status is not None else "SKIP"
            marker = "OK" if result.ok else "FAIL"
            print(
                f"[contract {case_index:02d}/{len(AGENT_CONTRACT_CASES)}] "
                f"{marker} {case.case_id} -> {status}"
            )
        workflow_results = request_workflows(
            client,
            base_url,
            sampler,
            operations_by_key,
            samples,
            args.api_key,
        )
        for workflow_index, result in enumerate(workflow_results, 1):
            status = result.status if result.status is not None else "SKIP"
            marker = "OK" if result.ok else "FAIL"
            print(
                f"[workflow {workflow_index:02d}/{len(workflow_results)}] "
                f"{marker} {result.workflow_id}.{result.workflow_step_id} -> {status}"
            )
        results.extend(workflow_results)
        health_result = verify_health(client, base_url, args.api_key)
        results.append(health_result)
        status = health_result.status if health_result.status is not None else "ERR"
        marker = "OK" if health_result.ok else "FAIL"
        print(f"[health] {marker} GET /health -> {status}")

    report_path = Path(args.out)
    json_path = Path(args.json_out)
    examples_path = Path(args.examples_json)
    contract_path = Path(args.contract_json_out)
    workflow_json_path = Path(args.workflow_json_out)
    workflow_md_path = Path(args.workflow_md_out)
    if not report_path.parent.exists():
        report_path = Path("../") / report_path
    if not json_path.parent.exists():
        json_path = Path("../") / json_path
    if not examples_path.parent.exists():
        examples_path = Path("../") / examples_path
    if not contract_path.parent.exists():
        contract_path = Path("../") / contract_path
    if not workflow_json_path.parent.exists():
        workflow_json_path = Path("../") / workflow_json_path
    if not workflow_md_path.parent.exists():
        workflow_md_path = Path("../") / workflow_md_path
    report_path.write_text(render_report(base_url, results, len(operations)), encoding="utf-8")
    write_json_report(json_path, results, args.api_key)
    write_json_report(
        contract_path,
        [result for result in results if result.contract_case_id],
        args.api_key,
    )
    write_json_report(workflow_json_path, workflow_results, args.api_key)
    workflow_md_path.write_text(
        render_workflow_report(base_url, workflow_results),
        encoding="utf-8",
    )
    write_examples_report(examples_path, results, args.api_key)

    failed = [result for result in results if not result.ok]
    print(f"SUMMARY passed={len(results) - len(failed)} total={len(results)} failed={len(failed)}")
    print(f"REPORT {report_path}")
    print(f"JSON {json_path}")
    print(f"CONTRACT_JSON {contract_path}")
    print(f"WORKFLOW_JSON {workflow_json_path}")
    print(f"WORKFLOW_REPORT {workflow_md_path}")
    print(f"EXAMPLES {examples_path}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
