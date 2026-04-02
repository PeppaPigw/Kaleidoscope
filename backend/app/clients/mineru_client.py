"""MinerU API client — PDF/HTML → Markdown + image upload to OSS.

Flow:
  1. submit_task(url, model)  →  task_id
  2. poll_task(task_id)       →  wait for state == "done"
  3. download zip             →  extract full.md + images/
  4. upload images to OSS     →  rewrite img src in markdown
  5. return MinerUResult with rewritten markdown

Concurrency:
  - MinerU tasks:  controlled by caller (seed_arxiv uses asyncio.gather)
  - OSS uploads:   OssClient semaphore (default 100)

API reference: https://mineru.net/api/v4
"""

from __future__ import annotations

import asyncio
import io
import re
import zipfile
from enum import Enum
from pathlib import PurePosixPath

import httpx
import structlog

from app.config import settings

logger = structlog.get_logger(__name__)

MINERU_BASE_URL = "https://mineru.net/api/v4"

# Image extensions to upload; everything else is ignored
_IMG_EXTS = frozenset({".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp"})


class MinerUModel(str, Enum):
    PDF_VLM = "vlm"            # Vision-language model (best quality PDF)
    PDF_PIPELINE = "pipeline"  # Standard pipeline for PDF
    HTML = "MinerU-HTML"       # HTML extraction


class MinerUTaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "done"
    FAILED = "failed"


class MinerUResult:
    """Result of a completed MinerU extraction pipeline."""

    def __init__(
        self,
        task_id: str,
        status: MinerUTaskStatus,
        markdown: str | None = None,
        layout: dict | None = None,
        image_urls: dict[str, str] | None = None,
        result_url: str | None = None,
        error: str | None = None,
    ) -> None:
        self.task_id = task_id
        self.status = status
        self.markdown = markdown
        self.layout = layout                  # parsed layout.json content
        self.image_urls = image_urls or {}    # {original_path: oss_url}
        self.result_url = result_url
        self.error = error

    @property
    def success(self) -> bool:
        return self.status == MinerUTaskStatus.SUCCESS and self.markdown is not None


class MinerUClient:
    """Async client for MinerU document extraction with OSS image hosting."""

    def __init__(self, api_token: str | None = None) -> None:
        self.api_token = api_token or settings.mineru_api_token
        if not self.api_token:
            raise ValueError(
                "MinerU API token not configured. "
                "Set MINERU_API_TOKEN in .env or pass api_token."
            )
        self._client: httpx.AsyncClient | None = None

    # ------------------------------------------------------------------ #
    #  Low-level HTTP                                                      #
    # ------------------------------------------------------------------ #

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(120.0, connect=10.0),
                headers={
                    "Authorization": f"Bearer {self.api_token}",
                    "Content-Type": "application/json",
                },
                follow_redirects=True,
            )
        return self._client

    def _check_response(self, data: dict, context: str) -> None:
        code = data.get("code", -1)
        if code != 0:
            msg = data.get("msg") or data.get("message") or f"code={code}"
            raise RuntimeError(f"MinerU API error ({context}): {msg}")

    # ------------------------------------------------------------------ #
    #  Task management                                                     #
    # ------------------------------------------------------------------ #

    async def submit_task(
        self,
        url: str,
        model_version: str | MinerUModel | None = None,
        is_html: bool = False,
    ) -> str:
        """Submit extraction task and return task_id."""
        if model_version is None:
            model_version = MinerUModel.HTML if is_html else MinerUModel.PDF_VLM
        if isinstance(model_version, MinerUModel):
            model_version = model_version.value

        client = await self._get_client()
        payload = {"url": url, "model_version": model_version}

        log = logger.bind(url=url[:80], model=model_version)
        log.info("mineru_submit")

        resp = await client.post(f"{MINERU_BASE_URL}/extract/task", json=payload)
        resp.raise_for_status()
        data = resp.json()
        self._check_response(data, "submit")

        task_id = (
            data.get("data", {}).get("task_id")
            or data.get("data", {}).get("batch_id")
        )
        if not task_id:
            raise ValueError(f"No task_id in MinerU response: {data}")

        log.info("mineru_submitted", task_id=task_id)
        return task_id

    async def poll_task(self, task_id: str) -> dict:
        """GET /extract/task/{task_id} → raw response dict."""
        client = await self._get_client()
        resp = await client.get(f"{MINERU_BASE_URL}/extract/task/{task_id}")
        resp.raise_for_status()
        data = resp.json()
        self._check_response(data, "poll")
        return data

    # ------------------------------------------------------------------ #
    #  Zip extraction                                                      #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _extract_zip(
        zip_bytes: bytes,
    ) -> tuple[str | None, dict | None, dict[str, bytes]]:
        """
        Extract from MinerU zip:
          - full.md  → markdown text
          - layout.json → layout dict
          - images/*  → {relative_path: bytes}

        Returns (markdown, layout, images).
        """
        markdown: str | None = None
        layout: dict | None = None
        images: dict[str, bytes] = {}

        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            names = zf.namelist()

            # 1. full.md (prefer) or any *.md
            md_candidates = [
                n for n in names if n.endswith(".md") and "full" in n.lower()
            ] or [n for n in names if n.endswith(".md")]
            if md_candidates:
                target_md = max(
                    md_candidates,
                    key=lambda n: zf.getinfo(n).file_size,
                )
                markdown = zf.read(target_md).decode("utf-8", errors="replace")

            # 2. layout.json
            layout_names = [n for n in names if n.endswith("layout.json")]
            if layout_names:
                import json
                try:
                    layout = json.loads(zf.read(layout_names[0]))
                except Exception:
                    pass

            # 3. images/ directory
            for name in names:
                p = PurePosixPath(name)
                if p.suffix.lower() in _IMG_EXTS:
                    # Normalize path: strip leading dirs, keep images/xxx
                    parts = p.parts
                    try:
                        img_idx = next(
                            i for i, part in enumerate(parts)
                            if part.lower() == "images"
                        )
                        rel = "/".join(parts[img_idx:])
                    except StopIteration:
                        rel = p.name  # fallback: just filename
                    images[rel] = zf.read(name)

        return markdown, layout, images

    # ------------------------------------------------------------------ #
    #  OSS image upload + markdown rewrite                                 #
    # ------------------------------------------------------------------ #

    @staticmethod
    async def _upload_images(
        images: dict[str, bytes],
        paper_slug: str,
        oss_client,
    ) -> dict[str, str]:
        """
        Upload all images to OSS concurrently.

        paper_slug: sanitised paper identifier for the OSS path,
                    e.g. "2403.01234v1" or "attention-is-all-you-need"

        Returns {original_rel_path: oss_url}.
        """
        if not images:
            return {}

        items = [
            (data, f"Kaleidoscope/{paper_slug}/{rel_path}")
            for rel_path, data in images.items()
        ]
        url_map = await oss_client.upload_many(items)
        # Re-key by original relative path
        return {
            rel_path: url_map[f"Kaleidoscope/{paper_slug}/{rel_path}"]
            for rel_path, _ in zip(images.keys(), items)
            if f"Kaleidoscope/{paper_slug}/{rel_path}" in url_map
        }

    @staticmethod
    def _rewrite_markdown(markdown: str, image_urls: dict[str, str]) -> str:
        """
        Replace local image paths in markdown with OSS URLs.

        Handles patterns like:
          ![caption](images/fig1.png)
          ![caption](./images/fig1.png)
          <img src="images/fig1.png">
        """
        if not image_urls:
            return markdown

        # Build reverse map: filename → url  (for fuzzy matching)
        fname_to_url: dict[str, str] = {}
        for rel_path, url in image_urls.items():
            fname_to_url[PurePosixPath(rel_path).name] = url
            fname_to_url[rel_path] = url

        def _replace_src(m: re.Match) -> str:
            src = m.group(1)
            # Try exact, then strip ./ prefix, then filename-only
            key = src.lstrip("./")
            url = (
                fname_to_url.get(src)
                or fname_to_url.get(key)
                or fname_to_url.get(PurePosixPath(src).name)
            )
            return m.group(0).replace(src, url) if url else m.group(0)

        # Markdown images:  ![alt](path)
        markdown = re.sub(r"!\[[^\]]*\]\(([^)]+)\)", _replace_src, markdown)
        # HTML img tags:    <img src="path" ...>
        markdown = re.sub(
            r'<img\s[^>]*src=["\']([^"\']+)["\'][^>]*>',
            _replace_src,
            markdown,
            flags=re.IGNORECASE,
        )
        return markdown

    # ------------------------------------------------------------------ #
    #  Public high-level API                                               #
    # ------------------------------------------------------------------ #

    async def extract(
        self,
        url: str,
        model_version: str | MinerUModel | None = None,
        is_html: bool = False,
        max_wait_seconds: int = 300,
        poll_interval: float = 8.0,
        initial_wait_seconds: float = 0.0,
        paper_slug: str | None = None,
        oss_client=None,
    ) -> MinerUResult:
        """
        Full pipeline: submit → poll → download zip → OSS upload → rewrite.

        Args:
            url:                  URL of the PDF or HTML to process.
            model_version:        Override model (default: vlm for PDF, MinerU-HTML for HTML).
            is_html:              Set True to auto-select MinerU-HTML model.
            max_wait_seconds:     Polling timeout.
            poll_interval:        Seconds between status checks.
            initial_wait_seconds: Fixed wait before first poll (e.g. 180 for PDF tasks).
            paper_slug:           Base path inside OSS bucket (e.g. arxiv_id).
                                  Defaults to last path segment of url.
            oss_client:           OssClient instance. If None and images exist,
                                  a new OssClient is created (if OSS is configured).
        """
        from app.clients.oss_client import OssClient

        log = logger.bind(url=url[:80])

        if paper_slug is None:
            paper_slug = PurePosixPath(url.split("?")[0]).stem or "paper"

        # 1. Submit
        task_id = await self.submit_task(url, model_version, is_html)

        # 2. Poll — optional initial wait before first check
        elapsed = 0.0
        full_zip_url: str | None = None

        if initial_wait_seconds > 0:
            log.info("mineru_initial_wait", seconds=initial_wait_seconds, task_id=task_id)
            await asyncio.sleep(initial_wait_seconds)
            elapsed += initial_wait_seconds

        while elapsed < max_wait_seconds:
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

            try:
                result = await self.poll_task(task_id)
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    backoff = min(poll_interval * 2, 30)
                    await asyncio.sleep(backoff)
                    elapsed += backoff
                    continue
                raise
            except RuntimeError:
                log.debug("mineru_poll_api_error", elapsed=elapsed)
                continue

            data = result.get("data", {})
            state = data.get("state", "")

            if state == "done":
                full_zip_url = data.get("full_zip_url", "")
                break

            if state in ("failed", "error"):
                err = data.get("err_msg") or data.get("error", "Unknown error")
                log.error("mineru_task_failed", task_id=task_id, error=err)
                return MinerUResult(
                    task_id=task_id,
                    status=MinerUTaskStatus.FAILED,
                    error=err,
                )

            log.debug("mineru_polling", elapsed=elapsed, state=state)

        else:
            log.warning("mineru_timeout", task_id=task_id, elapsed=elapsed)
            return MinerUResult(
                task_id=task_id,
                status=MinerUTaskStatus.FAILED,
                error=f"Timeout after {max_wait_seconds}s",
            )

        if not full_zip_url:
            return MinerUResult(
                task_id=task_id,
                status=MinerUTaskStatus.FAILED,
                error="No full_zip_url in response",
            )

        # 3. Download zip
        log.info("mineru_downloading_zip", zip_url=full_zip_url[:80])
        client = await self._get_client()
        try:
            zip_resp = await client.get(full_zip_url)
            zip_resp.raise_for_status()
            zip_bytes = zip_resp.content
        except Exception as e:
            log.error("mineru_zip_download_failed", error=str(e))
            return MinerUResult(
                task_id=task_id,
                status=MinerUTaskStatus.FAILED,
                error=f"Zip download failed: {e}",
            )

        # 4. Extract zip contents
        try:
            markdown, layout, images = self._extract_zip(zip_bytes)
        except Exception as e:
            log.error("mineru_zip_extract_failed", error=str(e))
            return MinerUResult(
                task_id=task_id,
                status=MinerUTaskStatus.FAILED,
                error=f"Zip extract failed: {e}",
            )

        if not markdown:
            return MinerUResult(
                task_id=task_id,
                status=MinerUTaskStatus.FAILED,
                error="No markdown found in zip",
            )

        log.info(
            "mineru_zip_extracted",
            md_chars=len(markdown),
            images=len(images),
            has_layout=layout is not None,
        )

        # 5. Upload images to OSS and rewrite markdown
        image_urls: dict[str, str] = {}
        if images:
            try:
                _oss = oss_client or OssClient()
                image_urls = await self._upload_images(images, paper_slug, _oss)
                markdown = self._rewrite_markdown(markdown, image_urls)
                log.info("mineru_images_uploaded", count=len(image_urls))
            except Exception as e:
                # OSS failure is non-fatal — keep raw markdown
                log.warning("mineru_oss_upload_failed", error=str(e)[:200])

        return MinerUResult(
            task_id=task_id,
            status=MinerUTaskStatus.SUCCESS,
            markdown=markdown,
            layout=layout,
            image_urls=image_urls,
            result_url=full_zip_url,
        )

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
