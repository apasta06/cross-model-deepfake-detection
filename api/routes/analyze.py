"""POST /analyze endpoint.

Accepts a multipart upload of an image or video plus a model key,
runs the existing ui_mvp inference pipeline, persists a history
record, and returns the AnalysisResult as JSON.

The heavy lifting (frame sampling, model loading, scoring, verdict
classification) remains in ui_mvp/analysis.py. This route is only
glue between HTTP and that pipeline.
"""
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from api.deps import get_settings, resolve_checkpoint
from api.models import AnalysisResult as AnalysisResultModel
from ui_mvp.analysis import AnalysisError, analyze_media, validate_upload
from ui_mvp.config import DEFAULT_SAMPLE_FRAMES, MODEL_OPTIONS
from ui_mvp.schemas import HistoryRecord
from ui_mvp.storage import append_history, save_full_result

router = APIRouter(tags=["analyze"])


@router.post(
    "/analyze",
    response_model=AnalysisResultModel,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"description": "Invalid upload (unsupported format, too large, missing fields)."},
        422: {"description": "Unknown model key."},
        500: {"description": "Inference failed unexpectedly."},
    },
)
async def analyze(
    file: UploadFile = File(..., description="Image or video to analyze."),
    model: str = Form(..., description="Model key: XCEPTION | MESO4 | MESOINCEPTION4 | EFFICIENTB0."),
    sample_frames: Optional[int] = Form(
        None,
        ge=1,
        le=120,
        description="Frames to sample from video. Ignored for images. Defaults to ui_mvp config.",
    ),
) -> AnalysisResultModel:
    if model not in MODEL_OPTIONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unknown model '{model}'. Valid keys: {sorted(MODEL_OPTIONS)}.",
        )

    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is missing a filename.",
        )

    settings = get_settings()
    frames = sample_frames or DEFAULT_SAMPLE_FRAMES

    # Persist the upload to a temp file the analysis pipeline can open by path.
    suffix = Path(file.filename).suffix
    tmp_path: Optional[Path] = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = Path(tmp.name)

        try:
            validate_upload(tmp_path, settings.max_upload_size_mb)
        except AnalysisError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc

        checkpoint_path = resolve_checkpoint(model)

        try:
            result = analyze_media(
                media_path=tmp_path,
                model_name=model,
                checkpoint_path=checkpoint_path,
                sample_frames=frames,
            )
        except AnalysisError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc

        # Preserve the original filename (NamedTemporaryFile gives an opaque name).
        result.filename = file.filename
        result.media_metadata.filename = file.filename

        # Persist for history endpoints; report_path stays None until /report is requested.
        append_history(HistoryRecord.from_result(result))
        save_full_result(result)

        return AnalysisResultModel.model_validate(result.to_dict())

    finally:
        if tmp_path and tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                # Don't mask the real error if cleanup fails.
                pass
