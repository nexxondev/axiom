"""
AXIOM — Adaptive eXecution Intelligence for Operations Management
Nexxon National | Unclassified

Main application entry point.
"""

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.api.v1.router import router as v1_router
from app.api.v1.routes.auth import router as auth_router

configure_logging()
logger = get_logger("axiom.startup")
from app.db.database import init_db

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
app.include_router(auth_router, prefix="/api/v1")

# Serve tactical UI
if os.path.exists("frontend"):
    app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/", include_in_schema=False)
async def serve_ui():
    return FileResponse("frontend/index.html")

@app.get("/login", include_in_schema=False)
async def serve_login():
    return FileResponse("frontend/login.html")


@app.on_event("startup")
async def startup_event():
    await init_db()
    logger.info("database_initialized", db="axiom.db")

logger.info(
    "axiom_startup",
    app=settings.APP_NAME,
    version=settings.APP_VERSION,
    environment=settings.APP_ENV,
)