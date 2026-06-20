"""
AXIOM — Adaptive eXecution Intelligence for Operations Management
Nexxon National | Unclassified

Main application entry point.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.api.v1.router import router as v1_router

configure_logging()
logger = get_logger("axiom.startup")

app = FastAPI(
    title="AXIOM",
    description="Adaptive eXecution Intelligence for Operations Management — Nexxon National",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS — locked down in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def audit_middleware(request: Request, call_next):
    """Log every request. Non-negotiable for government contracts."""
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "http_request",
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        duration_ms=round(duration_ms, 2),
    )
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("unhandled_exception", path=request.url.path, error=str(exc))
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "classification": "UNCLASSIFIED"},
    )


app.include_router(v1_router, prefix=settings.API_V1_PREFIX)

logger.info(
    "axiom_startup",
    app=settings.APP_NAME,
    version=settings.APP_VERSION,
    environment=settings.APP_ENV,
)
