"""MinerU API client — PDF/HTML → Markdown conversion.

Uses MinerU cloud API (https://mineru.net/api/v4) to convert
PDF and HTML documents to structured Markdown.

Flow: submit_task → poll_until_done → download_markdown

API reference:
  POST /api/v4/extract/task → data.task_id
  GET  /api/v4/extract/task/{task_id} → data.state, data.full_zip_url, etc.
"""

import asyncio
from enum import Enum

import httpx
import structlog

from app.config import settings

logger = structlog.get_logger(__name__)

MINERU_BASE_URL = "https://mineru.net/api/v4"


class MinerUModel(str, Enum):
    """MinerU model versions for different content types."""
    PDF_VLM = "vlm"            # Vision-language model for PDF
    PDF_PIPELINE = "pipeline"  # Standard pipeline for PDF
    HTML = "MinerU-HTML"       # HTML extraction


class MinerUTaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "done"
    FAILED = "failed"


class MinerUResult:
    """Result of a MinerU extraction task."""

    def __init__(
        self,
        task_id: str,
        status: MinerUTaskStatus,
        markdown: str | None = None,
        result_url: str | None = None,
        error: str | None = None,
    ):
        self.task_id = task_id
        self.status = status
        self.markdown = markdown
        self.result_url = result_url
        self.error = error

    @property
    def success(self) -> bool:
        return self.status == MinerUTaskStatus.SUCCESS and self.markdown is not None


class MinerUClient:
    """Async client for MinerU document extraction API."""

    def __init__(self, api_token: str | None = None):
        self.api_token = api_token or settings.mineru_api_token
        if not self.api_token:
            raise ValueError(
                "MinerU API token is not configured. "
                "Set MINERU_API_TOKEN in .env or pass api_token."
            )
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(60.0, connect=10.0),
                headers={
                    "Authorization": f"Bearer {self.api_token}",
                    "Content-Type": "application/json",
                    "Accept": "*/*",
                },
            )
        return self._client

    def _check_response(self, data: dict, context: str) -> None:
        """Raise on API-level errors (HTTP 200 but code != 0)."""
        code = data.get("code", -1)
        if code != 0:
            msg = data.get("msg") or data.get("message") or f"code={code}"
            raise RuntimeError(f"MinerU API error ({context}): {msg}")

    async def submit_task(
        self,
        url: str,
        model_version: str | MinerUModel | None = None,
        is_html: bool = False,
    ) -> str:
        """
        Submit a document extraction task.

        Returns task_id for polling.
        """
        if model_version is None:
            model_version = MinerUModel.HTML if is_html else MinerUModel.PDF_VLM

        if isinstance(model_version, MinerUModel):
            model_version = model_version.value

        client = await self._get_client()
        payload = {
            "url": url,
            "model_version": model_version,
        }

        log = logger.bind(url=url[:80], model=model_version)
        log.info("mineru_submit_task")

        resp = await client.post(f"{MINERU_BASE_URL}/extract/task", json=payload)
        resp.raise_for_status()
        data = resp.json()
        self._check_response(data, "submit")

        # Single-file API returns data.task_id
        task_id = data.get("data", {}).get("task_id", "")
        if not task_id:
            # Fallback for batch shape
            task_id = data.get("data", {}).get("batch_id", "")
        if not task_id:
            raise ValueError(f"MinerU API returned no task_id: {data}")

        log.info("mineru_task_submitted", task_id=task_id)
        return task_id

    async def poll_task(self, task_id: str) -> dict:
        """
        Poll the status of a MinerU extraction task.

        Uses GET /api/v4/extract/task/{task_id}
        """
        client = await self._get_client()
        resp = await client.get(f"{MINERU_BASE_URL}/extract/task/{task_id}")
        resp.raise_for_status()
        data = resp.json()
        self._check_response(data, "poll")
        return data

    async def extract(
        self,
        url: str,
        model_version: str | MinerUModel | None = None,
        is_html: bool = False,
        max_wait_seconds: int = 300,
        poll_interval: float = 5.0,
    ) -> MinerUResult:
        """
        Full extraction pipeline: submit → poll → download.

        Returns MinerUResult with markdown content.
        """
        log = logger.bind(url=url[:80])

        # 1. Submit
        task_id = await self.submit_task(url, model_version, is_html)

        # 2. Poll until done
        elapsed = 0.0
        while elapsed < max_wait_seconds:
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

            try:
                result = await self.poll_task(task_id)
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    # Rate limited, back off
                    backoff = min(poll_interval * 2, 30)
                    await asyncio.sleep(backoff)
                    elapsed += backoff
                    continue
                raise
            except RuntimeError:
                # API error during poll, retry
                log.debug("mineru_poll_api_error", elapsed=elapsed)
                continue

            data = result.get("data", {})
            state = data.get("state", "")

            if state == "done":
                # Extract result URLs
                full_zip_url = data.get("full_zip_url", "")
                content_list = data.get("content_list", {})
                md_url = content_list.get("md", "")

                # Download markdown
                markdown = await self._download_markdown(md_url or full_zip_url)
                if markdown:
                    log.info(
                        "mineru_extraction_done",
                        task_id=task_id,
                        md_length=len(markdown),
                    )
                    return MinerUResult(
                        task_id=task_id,
                        status=MinerUTaskStatus.SUCCESS,
                        markdown=markdown,
                        result_url=md_url or full_zip_url,
                    )
                else:
                    return MinerUResult(
                        task_id=task_id,
                        status=MinerUTaskStatus.FAILED,
                        error="Failed to download markdown result",
                    )

            elif state in ("failed", "error"):
                error_msg = data.get("err_msg") or data.get("error", "Unknown error")
                log.error("mineru_task_failed", task_id=task_id, error=error_msg)
                return MinerUResult(
                    task_id=task_id,
                    status=MinerUTaskStatus.FAILED,
                    error=error_msg,
                )

            else:
                log.debug(
                    "mineru_polling",
                    elapsed=elapsed,
                    task_id=task_id,
                    state=state,
                )

        # Timeout
        log.warning("mineru_timeout", task_id=task_id, elapsed=elapsed)
        return MinerUResult(
            task_id=task_id,
            status=MinerUTaskStatus.FAILED,
            error=f"Timeout after {max_wait_seconds}s",
        )

    async def _download_markdown(self, url: str) -> str | None:
        """Download markdown content from MinerU result URL."""
        if not url:
            return None

        try:
            client = await self._get_client()
            resp = await client.get(url)
            resp.raise_for_status()

            content_type = resp.headers.get("content-type", "")

            if "zip" in content_type or url.endswith(".zip"):
                # Handle ZIP containing markdown
                import io
                import zipfile

                with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
                    # Find the .md file
                    md_files = [f for f in zf.namelist() if f.endswith(".md")]
                    if md_files:
                        # Prefer full.md or the largest .md file
                        target = next(
                            (f for f in md_files if "full" in f.lower()),
                            max(md_files, key=lambda f: zf.getinfo(f).file_size),
                        )
                        return zf.read(target).decode("utf-8", errors="replace")
                return None
            else:
                return resp.text

        except Exception as e:
            logger.error("mineru_download_failed", url=url[:80], error=str(e))
            return None

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
