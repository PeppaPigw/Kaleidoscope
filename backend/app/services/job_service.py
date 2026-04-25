"""Async job status service backed by Celery result metadata."""

from __future__ import annotations

from typing import Any

from app.worker import celery_app

_TERMINAL_STATES = {"SUCCESS", "FAILURE", "REVOKED"}
_FAILURE_STATES = {"FAILURE", "REVOKED"}


class JobService:
    """Expose stable job lifecycle JSON for Celery-backed tasks."""

    def get_job(self, job_id: str, include_traceback: bool = False) -> dict[str, Any]:
        """Return the current Celery result state for a job ID."""
        result = celery_app.AsyncResult(job_id)
        return self._format_result(result, include_traceback=include_traceback)

    def list_jobs(self, entity_id: str | None = None) -> dict[str, Any]:
        """Return known jobs for an entity.

        Celery result backends do not maintain a reverse index from paper/entity IDs
        to task IDs. This endpoint provides the stable JSON contract now and makes
        the missing persistence explicit for downstream agents.
        """
        return {
            "entity_id": entity_id,
            "jobs": [],
            "total": 0,
            "tracking": "celery_result_backend_only",
            "warning": "No durable entity-to-job index is available yet.",
        }

    def cancel_job(
        self,
        job_id: str,
        terminate: bool = False,
        signal: str = "SIGTERM",
    ) -> dict[str, Any]:
        """Revoke a queued/running Celery task and return the observed state."""
        celery_app.control.revoke(job_id, terminate=terminate, signal=signal)
        payload = self.get_job(job_id)
        payload["cancel_requested"] = True
        payload["terminate_requested"] = terminate
        return payload

    def _format_result(
        self,
        result: Any,
        include_traceback: bool = False,
    ) -> dict[str, Any]:
        state = str(getattr(result, "state", "PENDING"))
        info = getattr(result, "info", None)
        payload = {
            "job_id": str(getattr(result, "id", "")),
            "state": state,
            "status": self._public_status(state),
            "ready": bool(result.ready()),
            "successful": bool(result.successful()) if result.ready() else False,
            "failed": state in _FAILURE_STATES,
            "terminal": state in _TERMINAL_STATES,
            "result": None,
            "error": None,
            "metadata": None,
        }

        if state == "SUCCESS":
            payload["result"] = self._jsonable(getattr(result, "result", None))
        elif state in _FAILURE_STATES:
            payload["error"] = str(info or getattr(result, "result", "")) or state
        elif isinstance(info, dict):
            payload["metadata"] = self._jsonable(info)
        elif info is not None:
            payload["metadata"] = {"info": str(info)}

        if include_traceback and getattr(result, "traceback", None):
            payload["traceback"] = str(result.traceback)

        return payload

    @staticmethod
    def _public_status(state: str) -> str:
        return {
            "PENDING": "pending",
            "RECEIVED": "queued",
            "STARTED": "running",
            "RETRY": "retrying",
            "SUCCESS": "succeeded",
            "FAILURE": "failed",
            "REVOKED": "cancelled",
        }.get(state, state.lower())

    def _jsonable(self, value: Any) -> Any:
        if value is None or isinstance(value, str | int | float | bool):
            return value
        if isinstance(value, list):
            return [self._jsonable(item) for item in value]
        if isinstance(value, tuple):
            return [self._jsonable(item) for item in value]
        if isinstance(value, dict):
            return {str(key): self._jsonable(item) for key, item in value.items()}
        return str(value)
