"""FastAPI application factory with middleware, exception handlers, and router registration."""

import time as _time
from datetime import datetime, timezone

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException as FastAPIHTTPException, RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.exceptions import (
    ExternalAPIError,
    KaleidoscopeError,
    PaperNotFoundError,
    RateLimitError,
)

logger = structlog.get_logger(__name__)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Kaleidoscope API",
        description=(
            "Academic Paper Intelligence Platform — "
            "Ingest, search, and analyze scholarly papers with AI."
        ),
        version="0.1.0",
        docs_url="/docs",
        openapi_url="/api/openapi.json",
    )

    # --- CORS ---
    app.add_middleware(
        CORSMiddleware,
        allow_origins=getattr(settings, "allowed_origins", ["*"]),
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start = _time.monotonic()
        response = await call_next(request)
        elapsed = _time.monotonic() - start
        elapsed_ms = elapsed * 1000
        if elapsed > 5.0:
            route_path = request.scope.get("path", "")
            if "reparse" in route_path or "graph" in route_path:
                logger.warning(
                    "slow_operation_detected",
                    path=route_path,
                    elapsed_s=round(elapsed, 2),
                    method=request.method,
                )
        if not request.url.path.startswith("/health"):
            logger.info(
                "http_request",
                method=request.method,
                path=request.url.path,
                status=response.status_code,
                duration_ms=f"{elapsed_ms:.1f}",
            )
        return response

    # --- Exception Handlers ---

    @app.exception_handler(PaperNotFoundError)
    async def paper_not_found_handler(request: Request, exc: PaperNotFoundError):
        return JSONResponse(
            status_code=404,
            content={
                "code": "PAPER_NOT_FOUND",
                "message": str(exc),
            },
        )

    @app.exception_handler(RateLimitError)
    async def rate_limit_handler(request: Request, exc: RateLimitError):
        return JSONResponse(
            status_code=429,
            content={
                "code": "RATE_LIMITED",
                "message": str(exc),
                "retry_after": exc.retry_after,
            },
            headers={"Retry-After": str(exc.retry_after)},
        )

    @app.exception_handler(ExternalAPIError)
    async def external_api_handler(request: Request, exc: ExternalAPIError):
        return JSONResponse(
            status_code=502,
            content={
                "code": "EXTERNAL_API_ERROR",
                "message": str(exc),
                "service": exc.service,
            },
        )

    @app.exception_handler(KaleidoscopeError)
    async def kaleidoscope_error_handler(request: Request, exc: KaleidoscopeError):
        return JSONResponse(
            status_code=500,
            content={
                "code": "INTERNAL_ERROR",
                "message": str(exc),
            },
        )

    @app.exception_handler(FastAPIHTTPException)
    async def http_exception_handler(request: Request, exc: FastAPIHTTPException):
        if isinstance(exc.detail, dict):
            detail = exc.detail
            content = {
                "code": detail.get("code", f"HTTP_{exc.status_code}"),
                "message": detail.get("message")
                or detail.get("detail")
                or "An error occurred.",
            }
            for key, value in detail.items():
                if key not in {"code", "message"}:
                    content[key] = value
        else:
            content = {
                "code": f"HTTP_{exc.status_code}",
                "message": str(exc.detail) if exc.detail else "An error occurred.",
            }
        return JSONResponse(status_code=exc.status_code, content=content)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        errors = exc.errors()
        return JSONResponse(
            status_code=422,
            content={
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed.",
                "details": [
                    {"field": ".".join(str(l) for l in e["loc"]), "msg": e["msg"]}
                    for e in errors
                ],
            },
        )

    # --- Register Routers ---
    from app.api.v1.imports import router as imports_router
    from app.api.v1.papers import router as papers_router
    from app.api.v1.search import router as search_router
    from app.api.v1.feeds import router as feeds_router
    from app.api.v1.collections import router as collections_router
    from app.api.v1.tags import router as tags_router
    from app.api.v1.graph import router as graph_router
    from app.api.v1.governance import router as governance_router
    from app.api.v1.intelligence import router as intelligence_router
    from app.api.v1.agent import router as agent_router
    from app.api.v1.filters import router as filters_router
    from app.api.v1.local_pdf import router as local_pdf_router
    from app.api.v1.analysis import router as analysis_router
    from app.api.v1.trends import router as trends_router
    from app.api.v1.trend_ext import router as trend_ext_router
    from app.api.v1.writing import router as writing_router
    from app.api.v1.alerts import router as alerts_router
    # P3 routers
    from app.api.v1.claims import router as claims_router
    from app.api.v1.cross_paper import router as cross_paper_router
    from app.api.v1.figures import router as figures_router
    from app.api.v1.knowledge import router as knowledge_router
    from app.api.v1.knowledge_ext import router as knowledge_ext_router
    from app.api.v1.quality import router as quality_router
    from app.api.v1.researchers import router as researchers_router
    from app.api.v1.auth import router as auth_router

    app.include_router(papers_router, prefix="/api/v1")
    app.include_router(imports_router, prefix="/api/v1")
    app.include_router(search_router, prefix="/api/v1")
    app.include_router(feeds_router, prefix="/api/v1")
    app.include_router(collections_router, prefix="/api/v1")
    app.include_router(tags_router, prefix="/api/v1")
    app.include_router(graph_router, prefix="/api/v1")
    app.include_router(governance_router, prefix="/api/v1")
    app.include_router(intelligence_router, prefix="/api/v1")
    app.include_router(agent_router, prefix="/api/v1")
    app.include_router(filters_router, prefix="/api/v1")
    app.include_router(local_pdf_router, prefix="/api/v1")
    app.include_router(analysis_router, prefix="/api/v1")
    app.include_router(trends_router, prefix="/api/v1")
    app.include_router(trend_ext_router, prefix="/api/v1")
    app.include_router(writing_router, prefix="/api/v1")
    app.include_router(alerts_router, prefix="/api/v1")
    app.include_router(auth_router, prefix="/api/v1")
    # P3 routers
    app.include_router(claims_router, prefix="/api/v1")
    app.include_router(cross_paper_router, prefix="/api/v1")
    app.include_router(figures_router, prefix="/api/v1")
    app.include_router(knowledge_router, prefix="/api/v1")
    app.include_router(knowledge_ext_router, prefix="/api/v1")
    app.include_router(quality_router, prefix="/api/v1")
    # Content/MinerU router
    from app.api.v1.content import router as content_router
    app.include_router(content_router, prefix="/api/v1")
    # Analytics router
    from app.api.v1.analytics import router as analytics_router
    app.include_router(analytics_router, prefix="/api/v1")
    # Researcher analytics router
    app.include_router(researchers_router, prefix="/api/v1")
    # Batch 6: Collaboration & Experiments
    from app.api.v1.collaboration import router as collaboration_router
    from app.api.v1.experiments import router as experiments_router
    app.include_router(collaboration_router, prefix="/api/v1")
    app.include_router(experiments_router, prefix="/api/v1")
    # Admin + SSE (Features 7/8/9/25/26/35/42)
    from app.api.v1.admin import router as admin_router
    from app.api.v1.sse import router as sse_router
    app.include_router(admin_router, prefix="/api/v1")
    app.include_router(sse_router, prefix="/api/v1")

    # --- Health Check ---

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "ok",
            "version": "1.0.0",
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "services": {
                "database": "unknown",
            },
        }

    @app.get("/health/services")
    async def services_health():
        """Check health of all dependent services."""
        from app.services.parsing.grobid_client import GROBIDClient

        results = {}

        # PostgreSQL
        try:
            from app.dependencies import engine
            from sqlalchemy import text

            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            results["postgresql"] = "ok"
        except Exception as e:
            results["postgresql"] = f"error: {e}"

        # Redis
        try:
            import redis as redis_lib

            r = redis_lib.from_url(settings.redis_url)
            r.ping()
            results["redis"] = "ok"
        except Exception as e:
            results["redis"] = f"error: {e}"

        # GROBID
        grobid = GROBIDClient()
        results["grobid"] = "ok" if await grobid.is_alive() else "unavailable"

        return {"services": results}

    logger.info("app_created", app_name=settings.app_name)
    return app


# Create the app instance
app = create_app()
