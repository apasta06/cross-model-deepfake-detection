"""POST /analyze endpoint for the real multimodal detector."""
from __future__ import annotations

import shutil
import tempfile
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from api.deps import (
    MULTIMODAL_MODEL_KEY,
    get_settings,
    resolve_multimodal_audio_checkpoint,
    resolve_multimodal_video_checkpoint,
)
from api.models import AnalysisResult as AnalysisResultModel
from api.multimodal_detect import (
    AUDIO_THRESHOLD,
    VIDEO_THRESHOLD,
    MultimodalConfig,
    MultimodalDetectionError,
    MultimodalDetectionResult,
    VisualFrameScore,
    analyze_video_file,
)
from ui_mvp.config import SUPPORTED_VIDEO_FORMATS
from ui_mvp.schemas import AnalysisResult, EvidenceAsset, HistoryRecord, MediaMetadata, now_iso
from ui_mvp.storage import append_history, save_full_result

try:
    import cv2
except ImportError:  # pragma: no cover
    cv2 = None

router = APIRouter(tags=["analyze"])
DEFAULT_MULTIMODAL_SAMPLE_FRAMES = 20


def _format_timestamp(seconds: float) -> str:
    seconds = max(0, int(round(seconds)))
    minutes, secs = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def _classify_probability(fake_probability: float) -> tuple[str, str]:
    if fake_probability <= 0.35:
        return "likely_real", "Likely Real"
    if fake_probability <= 0.74:
        return "uncertain", "Uncertain"
    return "likely_fake", "Likely Fake"


def _validate_video_upload(path: Path, max_upload_size_mb: int) -> None:
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_VIDEO_FORMATS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only video uploads are supported by the multimodal detector.",
        )

    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb > max_upload_size_mb:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File is {size_mb:.1f} MB, which exceeds the {max_upload_size_mb} MB limit.",
        )


def _extract_video_metadata(media_path: Path, original_filename: str) -> MediaMetadata:
    metadata = MediaMetadata(
        filename=original_filename,
        filesize=media_path.stat().st_size,
        extension=media_path.suffix.lower(),
        media_kind="video",
    )
    if cv2 is None:
        return metadata

    capture = cv2.VideoCapture(str(media_path))
    try:
        if not capture.isOpened():
            return metadata
        frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        fps = float(capture.get(cv2.CAP_PROP_FPS) or 0.0)
        width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        duration_seconds = (frame_count / fps) if fps else None
        metadata.frame_count = frame_count or None
        metadata.fps = round(fps, 2) if fps else None
        metadata.width = width or None
        metadata.height = height or None
        metadata.duration_seconds = round(duration_seconds, 2) if duration_seconds else None
        return metadata
    finally:
        capture.release()


def _build_frame_result(score: VisualFrameScore) -> dict:
    risk_key, risk_label = _classify_probability(score.fake_probability)
    return {
        "frame_index": score.frame_index,
        "timestamp_seconds": score.timestamp_seconds,
        "timestamp_label": _format_timestamp(score.timestamp_seconds),
        "fake_probability": score.fake_probability,
        "risk_label": risk_label,
        "risk_key": risk_key,
    }


def _build_frame_stats(frame_results: list[dict]) -> dict:
    counts = {"likely_fake": 0, "uncertain": 0, "likely_real": 0}
    for item in frame_results:
        counts[str(item["risk_key"])] += 1
    avg_probability = sum(float(item["fake_probability"]) for item in frame_results) / max(len(frame_results), 1)
    return {
        "sampled_frames": len(frame_results),
        "fake_frames": counts["likely_fake"],
        "uncertain_frames": counts["uncertain"],
        "real_frames": counts["likely_real"],
        "avg_fake_probability": round(avg_probability, 4),
    }


def _build_summary_text(detection: MultimodalDetectionResult) -> str:
    video_text = f"Visual suspiciousness {detection.video_score:.1%}"
    fused_text = f"fused suspiciousness {detection.fused_score:.1%}"
    if detection.audio_score is None:
        return (
            f"{detection.classification}. {video_text}. "
            "Audio was unavailable, so the result used visual-only fallback."
        )
    return (
        f"{detection.classification}. {video_text}, "
        f"audio suspiciousness {detection.audio_score:.1%}, {fused_text}."
    )


def _build_evidence_assets(detection: MultimodalDetectionResult) -> list[EvidenceAsset]:
    audio_description = (
        f"Audio track scored {detection.audio_score:.1%} suspiciousness."
        if detection.audio_score is not None
        else "Audio was unavailable or degraded; visual-only fallback was used."
    )
    return [
        EvidenceAsset(
            label="Video review",
            kind="viewer",
            description="The uploaded video is available in the forensic viewer for manual review.",
        ),
        EvidenceAsset(
            label="Visual frame timeline",
            kind="timeline",
            description="Sampled face frames are shown with per-frame visual suspiciousness scores.",
        ),
        EvidenceAsset(
            label="Audio evidence",
            kind="audio",
            description=audio_description,
        ),
        EvidenceAsset(
            label="Fusion matrix",
            kind="fusion",
            description=f"Cross-modal classification: {detection.classification}.",
        ),
    ]


def _build_analysis_result(
    detection: MultimodalDetectionResult,
    media_path: Path,
    original_filename: str,
) -> AnalysisResult:
    frame_results = [_build_frame_result(score) for score in detection.frame_scores]
    risk_key, _ = _classify_probability(detection.fused_score)
    flagged = [
        int(item["frame_index"])
        for item in frame_results
        if float(item["fake_probability"]) > VIDEO_THRESHOLD
    ]

    return AnalysisResult(
        analysis_id=uuid.uuid4().hex[:12],
        input_type="video",
        filename=original_filename,
        filesize=media_path.stat().st_size,
        verdict=detection.alert_level,
        confidence_score=detection.fused_score,
        risk_level=risk_key,
        summary_text=_build_summary_text(detection),
        flagged_frame_indices=flagged,
        frame_stats=_build_frame_stats(frame_results),
        evidence_paths=_build_evidence_assets(detection),
        created_at=now_iso(),
        model_used=MULTIMODAL_MODEL_KEY,
        media_metadata=_extract_video_metadata(media_path, original_filename),
        frame_results=frame_results,
        warnings=detection.warnings,
        report_payload={
            "classification": detection.classification,
            "alert_level": detection.alert_level,
            "video_score": detection.video_score,
            "audio_score": detection.audio_score,
            "fused_score": detection.fused_score,
            "video_threshold": VIDEO_THRESHOLD,
            "audio_threshold": AUDIO_THRESHOLD,
            "audio_available": detection.audio_available,
            "sampled_visual_frames": len(detection.frame_scores),
            "model_family": "EfficientNet-B0 multimodal",
            "warnings": detection.warnings,
        },
    )


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
    file: UploadFile = File(..., description="Video to analyze."),
    model: str = Form(..., description="Model key: MULTIMODAL_EFFICIENTB0."),
    sample_frames: Optional[int] = Form(
        None,
        ge=1,
        le=120,
        description="Frames to sample from video. Defaults to 20 to match detect_video.py.",
    ),
) -> AnalysisResultModel:
    if model != MULTIMODAL_MODEL_KEY:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unknown model '{model}'. Valid key: {MULTIMODAL_MODEL_KEY}.",
        )

    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is missing a filename.",
        )

    settings = get_settings()
    frames = sample_frames or DEFAULT_MULTIMODAL_SAMPLE_FRAMES

    # Persist the upload to a temp file the analysis pipeline can open by path.
    suffix = Path(file.filename).suffix
    tmp_path: Optional[Path] = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = Path(tmp.name)

        _validate_video_upload(tmp_path, settings.max_upload_size_mb)

        video_checkpoint = resolve_multimodal_video_checkpoint()
        if video_checkpoint is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=(
                    "Video checkpoint missing. Set CHECKPOINT_MULTIMODAL_VIDEO "
                    "or place best_corrected_model.pt at repository root."
                ),
            )

        audio_checkpoint = resolve_multimodal_audio_checkpoint()
        try:
            detection = analyze_video_file(
                tmp_path,
                MultimodalConfig(
                    video_checkpoint=video_checkpoint,
                    audio_checkpoint=audio_checkpoint,
                    sample_frames=frames,
                ),
            )
        except MultimodalDetectionError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Inference failed unexpectedly: {exc}",
            ) from exc

        result = _build_analysis_result(detection, tmp_path, file.filename)

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
