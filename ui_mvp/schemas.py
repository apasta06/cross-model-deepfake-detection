from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class MediaMetadata:
    filename: str
    filesize: int
    extension: str
    media_kind: str
    duration_seconds: Optional[float] = None
    fps: Optional[float] = None
    frame_count: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None


@dataclass
class EvidenceAsset:
    label: str
    kind: str
    path: Optional[str] = None
    description: str = ""


@dataclass
class AnalysisResult:
    analysis_id: str
    input_type: str
    filename: str
    filesize: int
    verdict: str
    confidence_score: float
    risk_level: str
    summary_text: str
    flagged_frame_indices: List[int]
    frame_stats: Dict[str, Any]
    evidence_paths: List[EvidenceAsset]
    created_at: str
    model_used: str
    media_metadata: MediaMetadata
    frame_results: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    report_payload: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["evidence_paths"] = [asdict(item) for item in self.evidence_paths]
        payload["media_metadata"] = asdict(self.media_metadata)
        return payload


@dataclass
class HistoryRecord:
    analysis_id: str
    created_at: str
    filename: str
    filesize: int
    input_type: str
    model_used: str
    verdict: str
    confidence_score: float
    risk_level: str
    summary_text: str
    report_path: Optional[str] = None

    @classmethod
    def from_result(cls, result: AnalysisResult, report_path: Optional[str] = None) -> "HistoryRecord":
        return cls(
            analysis_id=result.analysis_id,
            created_at=result.created_at,
            filename=result.filename,
            filesize=result.filesize,
            input_type=result.input_type,
            model_used=result.model_used,
            verdict=result.verdict,
            confidence_score=result.confidence_score,
            risk_level=result.risk_level,
            summary_text=result.summary_text,
            report_path=report_path,
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
