"""Meta endpoints: liveness and model catalog.

These are intentionally trivial — they let the frontend (and ops) verify
the service is reachable and discover which models can be requested by
the /analyze endpoint without hardcoding the list on the client side.
"""
from __future__ import annotations

from fastapi import APIRouter

from api.deps import MULTIMODAL_MODEL_DESCRIPTION, MULTIMODAL_MODEL_KEY
from api.models import HealthResponse, ModelInfo, ModelListResponse

router = APIRouter(tags=["meta"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Liveness probe. Returns 200 with {"status": "ok"} when reachable."""
    return HealthResponse(status="ok")


@router.get("/models", response_model=ModelListResponse)
def list_models() -> ModelListResponse:
    """List the single real multimodal detector accepted by /analyze."""
    return ModelListResponse(
        models=[
            ModelInfo(
                key=MULTIMODAL_MODEL_KEY,
                description=MULTIMODAL_MODEL_DESCRIPTION,
            )
        ]
    )
