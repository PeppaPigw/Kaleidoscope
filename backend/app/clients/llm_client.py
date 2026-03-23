"""OpenAI-compatible LLM client — supports GPT, Claude, and local models."""

import structlog
import httpx

from app.config import settings

logger = structlog.get_logger(__name__)

# Default models
DEFAULT_CHAT_MODEL = "gpt-4o-mini"
DEFAULT_EMBED_MODEL = "text-embedding-3-small"


class LLMClient:
    """
    Unified LLM client supporting OpenAI API and compatible providers.

    Configuration:
    - OPENAI_API_KEY in .env
    - Supports: GPT-4o, GPT-4o-mini, Claude (via gateway), local Ollama
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
    ):
        self.api_key = api_key or settings.openai_api_key
        raw_url = (base_url or settings.open_base_url).rstrip("/")
        # .env may contain "…/v1/chat/completions"; strip to base
        for suffix in ("/chat/completions", "/completions", "/embeddings"):
            if raw_url.endswith(suffix):
                raw_url = raw_url[: -len(suffix)]
                break
        self.base_url = raw_url
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
    ) -> str:
        """
        Send a chat completion request.

        Args:
            prompt: User message
            system: System prompt
            model: Model ID
            max_tokens: Max response tokens
            temperature: Sampling temperature (0=deterministic, 1=creative)
            response_format: e.g. {"type": "json_object"} for JSON mode

        Returns:
            Generated text content
        """
        client = await self._get_client()

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        body = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if response_format:
            body["response_format"] = response_format

        try:
            resp = await client.post("/chat/completions", json=body)
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            logger.info(
                "llm_completion",
                model=model,
                input_tokens=data.get("usage", {}).get("prompt_tokens"),
                output_tokens=data.get("usage", {}).get("completion_tokens"),
            )
            return content
        except httpx.HTTPStatusError as e:
            logger.error("llm_api_error", status=e.response.status_code, body=e.response.text[:500])
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
        """
        Send a completion request with JSON mode enabled.

        Returns parsed JSON dict.
        """
        import json

        content = await self.complete(
            prompt=prompt, system=system, model=model,
            max_tokens=max_tokens, temperature=0.1,
            response_format={"type": "json_object"},
        )
        return json.loads(content)

    async def embed(
        self,
        texts: list[str],
        model: str = DEFAULT_EMBED_MODEL,
    ) -> list[list[float]]:
        """
        Generate embeddings for a list of texts.

        Returns list of embedding vectors.
        """
        client = await self._get_client()

        try:
            resp = await client.post("/embeddings", json={
                "model": model,
                "input": texts,
            })
            resp.raise_for_status()
            data = resp.json()
            embeddings = [item["embedding"] for item in data["data"]]
            logger.info("llm_embed", model=model, count=len(texts),
                        dimensions=len(embeddings[0]) if embeddings else 0)
            return embeddings
        except Exception as e:
            logger.error("llm_embed_error", error=str(e))
            raise

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
