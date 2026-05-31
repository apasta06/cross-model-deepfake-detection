"""Pydantic models for the FastAPI service.

These mirror the dataclasses in ui_mvp/schemas.py and the TypeScript
types in frontend/src/types/analysis.ts. Field names and types are
kept identical so JSON serialization matches both sides without a
translation layer.
"""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


RiskKey = Literal["likely_real", "uncertain", "likely_fake"]
ModelKey = Literal["MULTIMODAL_EFFICIENTB0"]
MediaKind = Literal["video", "image"]
RiskLabel = Literal["Likely Real", "Uncertain", "Likely Fake"]


class MediaMetadata(BaseModel):
    filename: str
    filesize: int
    extension: str
    media_kind: MediaKind
    duration_seconds: Optional[float] = None
    fps: Optional[float] = None
    frame_count: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None


class EvidenceAsset(BaseModel):
    label: str
    kind: str
    path: Optional[str] = None
    description: str = ""


class FrameResult(BaseModel):
    frame_index: int
    timestamp_seconds: float
    timestamp_label: str
    fake_probability: float
    risk_label: RiskLabel
    risk_key: RiskKey
    thumbnail_url: Optional[str] = None


class FrameStats(BaseModel):
    sampled_frames: int
    fake_frames: int
    uncertain_frames: int
    real_frames: int
    avg_fake_probability: float


class AnalysisResult(BaseModel):
    analysis_id: str
    input_type: MediaKind
    filename: str
    filesize: int
    verdict: str
    confidence_score: float
    risk_level: RiskKey
    summary_text: str
    flagged_frame_indices: List[int]
    frame_stats: FrameStats
    evidence_paths: List[EvidenceAsset]
    created_at: str
    model_used: str
    media_metadata: MediaMetadata
    frame_results: List[FrameResult] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    report_payload: Dict[str, Any] = Field(default_factory=dict)


class HistoryRecord(BaseModel):
    analysis_id: str
    created_at: str
    filename: str
    filesize: int
    input_type: MediaKind
    model_used: str
    verdict: str
    confidence_score: float
    risk_level: str
    summary_text: str
    report_path: Optional[str] = None


class HealthResponse(BaseModel):
    status: Literal["ok"]


class ModelInfo(BaseModel):
    key: ModelKey
    description: str


class ModelListResponse(BaseModel):
    models: List[ModelInfo]


class ErrorResponse(BaseModel):
    detail: str
