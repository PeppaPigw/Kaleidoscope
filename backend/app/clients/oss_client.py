"""Aliyun OSS async client — upload images and return public URLs.

oss2 is a sync library; we run blocking calls in a thread pool so they
don't block the asyncio event loop.

Usage:
    async with OssClient() as oss:
        url = await oss.upload_bytes(b"...", "Kaleidoscope/paper-id/fig1.png")
"""

from __future__ import annotations

import asyncio
import mimetypes
from functools import partial
from typing import TYPE_CHECKING

import structlog

from app.config import settings

if TYPE_CHECKING:
    import oss2 as _oss2_type

logger = structlog.get_logger(__name__)


def _bucket_endpoint(host_url: str, bucket_name: str) -> str:
    """Build the public base URL for a bucket."""
    host = host_url.rstrip("/").replace("https://", "")
    return f"https://{bucket_name}.{host}"


class OssClient:
    """Async wrapper around oss2.Bucket for uploading paper images."""

    def __init__(
        self,
        access_key: str | None = None,
        access_key_secret: str | None = None,
        bucket_name: str | None = None,
        endpoint: str | None = None,
        concurrency: int | None = None,
    ) -> None:
        self._ak = access_key or settings.img_host_access_key
        self._sk = access_key_secret or settings.img_host_access_key_secret
        self._bucket_name = bucket_name or settings.img_host_bucket_name
        self._endpoint = endpoint or settings.img_host_url
        self._public_base = _bucket_endpoint(self._endpoint, self._bucket_name)
        self._sem = asyncio.Semaphore(concurrency or settings.img_host_concurrency)
        self._bucket: _oss2_type.Bucket | None = None

    def _get_bucket(self):
        """Lazy-init oss2.Bucket (sync, called from thread pool)."""
        if self._bucket is None:
            import oss2
            auth = oss2.Auth(self._ak, self._sk)
            self._bucket = oss2.Bucket(auth, self._endpoint, self._bucket_name)
        return self._bucket

    async def upload_bytes(self, data: bytes, object_key: str) -> str:
        """
        Upload raw bytes to OSS and return the public URL.

        object_key is the destination path, e.g.
            "Kaleidoscope/2403.01234/images/fig1.png"
        """
        async with self._sem:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(
                None,
                partial(self._sync_put, data, object_key),
            )
        url = f"{self._public_base}/{object_key}"
        logger.debug("oss_upload_done", key=object_key, url=url)
        return url

    def _sync_put(self, data: bytes, object_key: str) -> None:
        """Blocking put (runs in thread pool)."""
        bucket = self._get_bucket()
        content_type, _ = mimetypes.guess_type(object_key)
        headers = {"Content-Type": content_type or "application/octet-stream"}
        bucket.put_object(object_key, data, headers=headers)

    async def upload_many(
        self, items: list[tuple[bytes, str]]
    ) -> dict[str, str]:
        """
        Upload multiple (data, object_key) pairs concurrently.

        Returns {object_key: public_url} mapping.
        """
        tasks = [self.upload_bytes(data, key) for data, key in items]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        mapping: dict[str, str] = {}
        for (_, key), result in zip(items, results):
            if isinstance(result, Exception):
                logger.warning("oss_upload_failed", key=key, error=str(result))
            else:
                mapping[key] = result  # type: ignore[assignment]
        return mapping

    async def __aenter__(self) -> "OssClient":
        return self

    async def __aexit__(self, *_) -> None:
        pass  # oss2 has no async resources to close
