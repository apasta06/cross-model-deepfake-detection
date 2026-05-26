"""FastAPI application entry point.

Run locally with:
    uvicorn api.main:app --reload --port 8000

Interactive docs:
    http://localhost:8000/docs       (Swagger UI)
    http://localhost:8000/redoc      (ReDoc)
    http://localhost:8000/openapi.json
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.deps import get_settings
from api.routes import analyze, history, meta, reports

settings = get_settings()

app = FastAPI(
    title="Cross-Model Deepfake Detection API",
    description=(
        "HTTP service for the cross-model deepfake detection pipeline. "
        "Wraps the existing ui_mvp inference, history, and reporting logic."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Routers are mounted under the configured prefix (default: /api/v1).
# meta:    /health, /models
# analyze: /analyze
# history: /analyses, /analyses/{id}
# reports: /analyses/{id}/report
app.include_router(meta.router, prefix=settings.api_prefix)
app.include_router(analyze.router, prefix=settings.api_prefix)
app.include_router(history.router, prefix=settings.api_prefix)
app.include_router(reports.router, prefix=settings.api_prefix)


@app.get("/", include_in_schema=False)
def root() -> dict:
    """Trivial root redirect target. Real endpoints live under /api/v1."""
    return {
        "name": "Cross-Model Deepfake Detection API",
        "version": "0.1.0",
        "docs": "/docs",
        "api_prefix": settings.api_prefix,
    }
