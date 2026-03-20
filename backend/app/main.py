"""FastAPI application factory with middleware, exception handlers, and router registration."""

import structlog
from fastapi import FastAPI, Request
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
        allow_origins=["*"],  # TODO: Restrict in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

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

    # --- Register Routers ---
    from app.api.v1.papers import router as papers_router
    from app.api.v1.search import router as search_router
    from app.api.v1.feeds import router as feeds_router

    app.include_router(papers_router, prefix="/api/v1")
    app.include_router(search_router, prefix="/api/v1")
    app.include_router(feeds_router, prefix="/api/v1")

    # --- Health Check ---

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "ok",
            "app": settings.app_name,
            "version": "0.1.0",
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
