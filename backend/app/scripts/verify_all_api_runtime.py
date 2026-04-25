"""Verify every OpenAPI operation against a running Kaleidoscope backend.

The verifier performs real HTTP requests against BASE_URL (default
http://127.0.0.1:8000). It is designed for development environments: generated
inputs use smoke-test identifiers and payloads, and success means the endpoint
responded without a server-side failure. 4xx responses are recorded as handled
API responses; 5xx, timeouts, connection errors, and invalid response bodies are
reported as failures.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote

import httpx

HTTP_METHODS = {"get", "post", "put", "patch", "delete"}
UUID = "00000000-0000-0000-0000-000000000001"
ARXIV_ID = "2401.00001"
DOI = "10.1000/smoke-test"
OPENALEX_ID = "W2741809807"
PMCID = "PMC7339034"
BASE_TIMEOUT = httpx.Timeout(connect=3.0, read=8.0, write=8.0, pool=3.0)
STREAMING_PATHS = {"/api/v1/sse", "/api/v1/subscriptions/events"}

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
    error: str | None = None


class OpenAPISampler:
    """Generate small route-specific requests from an OpenAPI document."""

    def __init__(self, openapi: dict[str, Any]):
        self.openapi = openapi
        self.components = openapi.get("components", {}).get("schemas", {})

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

    @staticmethod
    def apply_body_overrides(path: str, body: Any) -> Any:
        if not isinstance(body, dict):
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
        elif path.endswith("/evidence/search") or path.endswith("/evidence/packs"):
            body.update({"query": "ImageNet accuracy"})
        elif path.endswith("/claims/verify"):
            body.update({"claim": "The method improves accuracy."})
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


def fetch_openapi(base_url: str) -> dict[str, Any]:
    with httpx.Client(timeout=BASE_TIMEOUT) as client:
        response = client.get(f"{base_url.rstrip('/')}/api/openapi.json")
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


def accepted_response(response: httpx.Response) -> tuple[bool, str]:
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
            return True, "success_empty"
        return False, "unexpected_content_type"
    return False, "unexpected_status"


def request_operation(
    client: httpx.Client,
    base_url: str,
    sampler: OpenAPISampler,
    operation: ApiOperation,
) -> ApiResult:
    built = sampler.build_request(operation)
    url = f"{base_url.rstrip('/')}{built['path']}"
    started = datetime.now(tz=UTC)
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
                ok, category = accepted_response(response)
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
        ok, category = accepted_response(response)
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
        )


def verify_health(client: httpx.Client, base_url: str) -> ApiResult:
    url = f"{base_url.rstrip('/')}/health"
    started = datetime.now(tz=UTC)
    try:
        response = client.get(url)
        elapsed = (datetime.now(tz=UTC) - started).total_seconds() * 1000
        ok, category = accepted_response(response)
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
        )


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
        "Pass criteria: every endpoint is actually requested; 2xx/3xx and "
        "handled 4xx responses count as responsive API behavior; 5xx, "
        "timeouts, connection errors, and unexpected content types fail.",
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


def write_json_report(path: Path, results: list[ApiResult]) -> None:
    payload = [result.__dict__ for result in results]
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--out", default="docs/memo/full-api-runtime-report.md")
    parser.add_argument("--json-out", default="docs/memo/full-api-runtime-report.json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    base_url = args.base_url.rstrip("/")
    openapi = fetch_openapi(base_url)
    operations = iter_operations(openapi)
    sampler = OpenAPISampler(openapi)
    results: list[ApiResult] = []
    with httpx.Client(timeout=BASE_TIMEOUT) as client:
        for index, operation in enumerate(operations, 1):
            result = request_operation(client, base_url, sampler, operation)
            results.append(result)
            status = result.status if result.status is not None else "ERR"
            marker = "OK" if result.ok else "FAIL"
            print(
                f"[{index:03d}/{len(operations)}] {marker} "
                f"{operation.method} {operation.path} -> {status}"
            )
        health_result = verify_health(client, base_url)
        results.append(health_result)
        status = health_result.status if health_result.status is not None else "ERR"
        marker = "OK" if health_result.ok else "FAIL"
        print(f"[health] {marker} GET /health -> {status}")

    report_path = Path(args.out)
    json_path = Path(args.json_out)
    if not report_path.parent.exists():
        report_path = Path("../") / report_path
    if not json_path.parent.exists():
        json_path = Path("../") / json_path
    report_path.write_text(render_report(base_url, results, len(operations)), encoding="utf-8")
    write_json_report(json_path, results)

    failed = [result for result in results if not result.ok]
    print(f"SUMMARY passed={len(results) - len(failed)} total={len(results)} failed={len(failed)}")
    print(f"REPORT {report_path}")
    print(f"JSON {json_path}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
