"""NVIDIA Translation API client — Chinese-English translation service.

Uses the NVIDIA integrate.api.nvidia.com API with OpenAI-compatible format.
Configuration is separate from the main LLM API (BLSC).

Usage:
    async with TranslateClient() as client:
        translated = await client.translate("Hello world")
"""

from __future__ import annotations

import asyncio

import httpx
import structlog

from app.config import settings

logger = structlog.get_logger(__name__)

DEFAULT_SYSTEM_PROMPT = (
    "你是一个论文翻译助手，使用最简洁准确的语言翻译下面的内容。不允许任何其他额外输出"
)


class TranslateClient:
    """Async client for NVIDIA translation API."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        system_prompt: str | None = None,
    ) -> None:
        self.api_key = api_key or settings.translate_api_key
        self.base_url = base_url or settings.translate_base_url
        self.model = model or settings.translate_model
        self.system_prompt = system_prompt or DEFAULT_SYSTEM_PROMPT

        if not self.api_key:
            raise ValueError(
                "Translation API key not configured. "
                "Set TRANSLATE_API_KEY in .env or pass api_key."
            )

        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create httpx client with proper headers."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(60.0, connect=10.0),
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                follow_redirects=True,
            )
        return self._client

    async def translate(
        self,
        text: str,
        system_prompt: str | None = None,
    ) -> str:
        """Translate text using NVIDIA API.

        Args:
            text: Text to translate
            system_prompt: Optional override for system prompt

        Returns:
            Translated text or empty string on error
        """
        if not text or len(text.strip()) < 2:
            return text

        prompt = system_prompt or self.system_prompt
        client = await self._get_client()

        log = logger.bind(text_preview=text[:80])
        log.debug("translate_request")

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": text},
            ],
        }

        try:
            resp = await client.post(
                f"{self.base_url.rstrip('/')}/v1/chat/completions",
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

            translated = (
                data.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
                .strip()
            )

            if translated:
                log.debug("translate_success", result_preview=translated[:80])
                return translated
            else:
                log.warning("translate_empty_response")
                return ""

        except httpx.HTTPStatusError as e:
            log.error(
                "translate_http_error",
                status_code=e.response.status_code,
                error=str(e),
            )
            return ""
        except httpx.RequestError as e:
            log.error("translate_request_error", error=str(e))
            return ""
        except Exception as e:
            log.error("translate_unexpected_error", error=str(e))
            return ""

    async def translate_batch(
        self,
        texts: list[str],
        system_prompt: str | None = None,
    ) -> list[str]:
        """Translate multiple texts concurrently.

        Args:
            texts: List of texts to translate
            system_prompt: Optional override for system prompt

        Returns:
            List of translated texts (empty string for failed items)
        """
        if not texts:
            return []

        results = await asyncio.gather(
            *[self.translate(t, system_prompt) for t in texts],
            return_exceptions=True,
        )

        return [r if isinstance(r, str) else "" for r in results]

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> TranslateClient:
        return self

    async def __aexit__(self, *_) -> None:
        await self.close()
