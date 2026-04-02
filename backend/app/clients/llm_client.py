"""OpenAI-compatible LLM client — BLSC API (Qwen3 / Doubao / GLM-Rerank).

Default endpoints use the BLSC gateway at https://llmapi.blsc.cn.
All credentials come from config.py (which reads from .env).

Models:
  chat      → Qwen3-235B-A22B  (settings.llm_model)
  embed     → Doubao-Embedding-Large-Text  (settings.embed_model)
  rerank    → GLM-Rerank  (settings.rerank_model)
"""

from __future__ import annotations

import structlog
import httpx

from app.config import settings

logger = structlog.get_logger(__name__)

# Resolved model defaults (from config, overridable per-call)
DEFAULT_CHAT_MODEL = settings.llm_model  # "Qwen3-235B-A22B"
DEFAULT_EMBED_MODEL = settings.embed_model  # "Doubao-Embedding-Large-Text"
DEFAULT_RERANK_MODEL = settings.rerank_model  # "GLM-Rerank"


def _resolve_base_url(url: str) -> str:
    """Strip known path suffixes so we always work with the API root."""
    raw = url.rstrip("/")
    for suffix in ("/chat/completions", "/completions", "/embeddings", "/rerank"):
        if raw.endswith(suffix):
            raw = raw[: -len(suffix)]
            break
    return raw


class LLMClient:
    """
    Unified client for BLSC / OpenAI-compatible APIs.

    Supports:
      • chat completions  (Qwen3-235B-A22B, enable_thinking=False by default)
      • embeddings        (Doubao-Embedding-Large-Text)
      • reranking         (GLM-Rerank)

    Override base_url + api_key for non-BLSC providers.
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
    ):
        # Prefer BLSC settings; fall back to legacy openai_api_key / open_base_url
        self.api_key = (
            api_key
            or (settings.llm_api_key if settings.llm_api_key else None)
            or settings.openai_api_key
        )
        raw_url = base_url or settings.llm_base_url or settings.open_base_url
        self.base_url = _resolve_base_url(raw_url)
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=120.0,
            )
        return self._client

    async def complete(
        self,
        prompt: str,
        system: str = "",
        model: str = DEFAULT_CHAT_MODEL,
        max_tokens: int = 4096,
        temperature: float = 0.3,
        response_format: dict | None = None,
        enable_thinking: bool = False,
    ) -> str:
        """
        Chat completion request.

        Args:
            prompt: User message.
            system: System prompt (optional).
            model: Model ID — defaults to Qwen3-235B-A22B.
            max_tokens: Max tokens to generate.
            temperature: 0 = deterministic, 1 = creative.
            response_format: e.g. {"type": "json_object"} for JSON mode.
            enable_thinking: Qwen3 chain-of-thought flag (default False for
                             structured extraction; set True for reasoning tasks).

        Returns:
            Generated text (thinking block stripped if present).
        """
        client = await self._get_client()

        messages: list[dict] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        body: dict = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False,
        }
        if response_format:
            body["response_format"] = response_format
        if enable_thinking:
            body["enable_thinking"] = True

        try:
            resp = await client.post("/chat/completions", json=body)
            resp.raise_for_status()
            data = resp.json()
            choice = data["choices"][0]["message"]
            # Qwen3 wraps CoT in a separate "reasoning_content" field;
            # we return the final answer only.
            content: str = choice.get("content") or ""
            logger.info(
                "llm_completion",
                model=model,
                input_tokens=data.get("usage", {}).get("prompt_tokens"),
                output_tokens=data.get("usage", {}).get("completion_tokens"),
            )
            return content
        except httpx.HTTPStatusError as e:
            logger.error(
                "llm_api_error",
                status=e.response.status_code,
                body=e.response.text[:500],
            )
            raise
        except Exception as e:
            logger.error("llm_error", error=str(e))
            raise

    async def complete_json(
        self,
        prompt: str,
        system: str = "",
        model: str = DEFAULT_CHAT_MODEL,
        max_tokens: int = 4096,
    ) -> dict:
        """Chat completion in JSON mode — returns a parsed dict."""
        import json

        content = await self.complete(
            prompt=prompt,
            system=system,
            model=model,
            max_tokens=max_tokens,
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        return json.loads(content)

    async def embed(
        self,
        texts: list[str],
        model: str = DEFAULT_EMBED_MODEL,
    ) -> list[list[float]]:
        """
        Generate embeddings via Doubao-Embedding-Large-Text.

        Returns one float vector per input text (in the same order).
        """
        client = await self._get_client()

        try:
            resp = await client.post(
                "/embeddings",
                json={
                    "model": model,
                    "input": texts,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            # Standard OpenAI embedding response: data[].embedding
            embeddings = [item["embedding"] for item in data["data"]]
            logger.info(
                "llm_embed",
                model=model,
                count=len(texts),
                dimensions=len(embeddings[0]) if embeddings else 0,
            )
            return embeddings
        except Exception as e:
            logger.error("llm_embed_error", error=str(e))
            raise

    async def rerank(
        self,
        query: str,
        documents: list[str],
        model: str = DEFAULT_RERANK_MODEL,
        top_n: int | None = None,
    ) -> list[dict]:
        """
        Rerank documents against a query using GLM-Rerank.

        Calls POST /rerank (Cohere-compatible endpoint).

        Returns a list of dicts sorted by relevance_score descending:
            [{"index": int, "document": str, "relevance_score": float}, ...]
        """
        client = await self._get_client()

        body: dict = {
            "model": model,
            "query": query,
            "documents": documents,
        }
        if top_n is not None:
            body["top_n"] = top_n

        try:
            resp = await client.post("/rerank", json=body)
            resp.raise_for_status()
            data = resp.json()
            # Handle both Cohere-style {"results": [...]} and OpenAI-style {"data": [...]}
            results = data.get("results") or data.get("data") or []
            ranked = sorted(
                results, key=lambda r: r.get("relevance_score", 0), reverse=True
            )
            logger.info(
                "llm_rerank",
                model=model,
                query_len=len(query),
                doc_count=len(documents),
                top_n=top_n,
            )
            return ranked
        except Exception as e:
            logger.error("llm_rerank_error", error=str(e))
            raise

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
