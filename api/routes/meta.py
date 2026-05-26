"""Meta endpoints: liveness and model catalog.

These are intentionally trivial — they let the frontend (and ops) verify
the service is reachable and discover which models can be requested by
the /analyze endpoint without hardcoding the list on the client side.
"""
from __future__ import annotations

from fastapi import APIRouter

from api.models import HealthResponse, ModelInfo, ModelListResponse
from ui_mvp.config import MODEL_OPTIONS

router = APIRouter(tags=["meta"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Liveness probe. Returns 200 with {"status": "ok"} when reachable."""
    return HealthResponse(status="ok")


@router.get("/models", response_model=ModelListResponse)
def list_models() -> ModelListResponse:
    """List the deepfake detection models the /analyze endpoint accepts.

    Pulled from ui_mvp.config.MODEL_OPTIONS so frontend and API agree on
    the canonical model catalog.
    """
    models = [
        ModelInfo(key=key, description=description)
        for key, description in MODEL_OPTIONS.items()
    ]
    return ModelListResponse(models=models)
