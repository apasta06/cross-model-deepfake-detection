from __future__ import annotations

import tempfile
import uuid
from dataclasses import asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

from ui_mvp.config import DEFAULT_SAMPLE_FRAMES, MODEL_OPTIONS, RISK_THRESHOLDS, SUPPORTED_IMAGE_FORMATS, SUPPORTED_VIDEO_FORMATS
from ui_mvp.schemas import AnalysisResult, EvidenceAsset, MediaMetadata, now_iso

try:
    import cv2
except ImportError:  # pragma: no cover
    cv2 = None

try:
    import torch
    import torchvision.transforms as transforms
    from PIL import Image
    from models.EfficientNet.EfficientNet import EfficientNet
    from models.MesoNet import Meso4, MesoInception4
    from models import xception_origin
except ImportError:  # pragma: no cover
    torch = None
    transforms = None
    Image = None
    EfficientNet = None
    Meso4 = None
    MesoInception4 = None
    xception_origin = None


class AnalysisError(RuntimeError):
    pass


def validate_upload(path: Path, max_upload_size_mb: int) -> None:
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_VIDEO_FORMATS + SUPPORTED_IMAGE_FORMATS:
        raise AnalysisError(f"Unsupported file format: {suffix or 'unknown'}")
    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb > max_upload_size_mb:
        raise AnalysisError(f"File is {size_mb:.1f} MB, which exceeds the {max_upload_size_mb} MB limit.")


def analyze_media(
    media_path: Path,
    model_name: str,
    checkpoint_path: Optional[Path],
    sample_frames: int = DEFAULT_SAMPLE_FRAMES,
) -> AnalysisResult:
    if model_name not in MODEL_OPTIONS:
        raise AnalysisError(f"Unsupported model selection: {model_name}")

    media_metadata = extract_media_metadata(media_path)
    warnings: List[str] = []
    frame_results: List[Dict[str, object]] = []
    evidence_assets = [
        EvidenceAsset(
            label="Video review",
            kind="viewer",
            description="The original uploaded media is available in the forensic viewer for manual review.",
        )
    ]

    if checkpoint_path and checkpoint_path.exists():
        frame_results = run_visual_inference(media_path, model_name, checkpoint_path, sample_frames)
    else:
        if checkpoint_path and not checkpoint_path.exists():
            warnings.append(f"Checkpoint path not found: {checkpoint_path}")
        warnings.append(
            "No compatible checkpoint was supplied. The UI is running in metadata-only review mode, "
            "so verdict and confidence are conservative placeholders."
        )
        frame_results = build_placeholder_frame_results(media_metadata, sample_frames)

    verdict, confidence_score, risk_level, summary_text, flagged = summarize_frame_results(frame_results, warnings)
    frame_stats = build_frame_stats(frame_results)

    if media_metadata.media_kind == "video":
        evidence_assets.append(
            EvidenceAsset(
                label="Frame timeline",
                kind="timeline",
                description="Sampled frames are shown with per-frame fake probabilities for quick triage.",
            )
        )
    else:
        evidence_assets.append(
            EvidenceAsset(
                label="Still image review",
                kind="image",
                description="Single-image analysis is supported for compatible checkpoints.",
            )
        )

    evidence_assets.append(
        EvidenceAsset(
            label="Audio evidence",
            kind="note",
            description="No run-specific spectrogram or audio anomaly output is produced by the current Phase 1 pipeline.",
        )
    )

    analysis_id = uuid.uuid4().hex[:12]
    return AnalysisResult(
        analysis_id=analysis_id,
        input_type=media_metadata.media_kind,
        filename=media_metadata.filename,
        filesize=media_metadata.filesize,
        verdict=verdict,
        confidence_score=confidence_score,
        risk_level=risk_level,
        summary_text=summary_text,
        flagged_frame_indices=flagged,
        frame_stats=frame_stats,
        evidence_paths=evidence_assets,
        created_at=now_iso(),
        model_used=model_name,
        media_metadata=media_metadata,
        frame_results=frame_results,
        warnings=warnings,
        report_payload={
            "frame_stats": frame_stats,
            "warnings": warnings,
            "evidence": [asdict(asset) for asset in evidence_assets],
        },
    )


def extract_media_metadata(media_path: Path) -> MediaMetadata:
    suffix = media_path.suffix.lower()
    base = MediaMetadata(
        filename=media_path.name,
        filesize=media_path.stat().st_size,
        extension=suffix,
        media_kind="image" if suffix in SUPPORTED_IMAGE_FORMATS else "video",
    )
    if base.media_kind == "image":
        if Image is not None:
            with Image.open(media_path) as image:
                base.width, base.height = image.size
        return base

    if cv2 is None:
        return base

    capture = cv2.VideoCapture(str(media_path))
    try:
        if not capture.isOpened():
            return base
        frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        fps = float(capture.get(cv2.CAP_PROP_FPS) or 0.0)
        width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        duration_seconds = (frame_count / fps) if fps else None
        base.frame_count = frame_count or None
        base.fps = round(fps, 2) if fps else None
        base.width = width or None
        base.height = height or None
        base.duration_seconds = round(duration_seconds, 2) if duration_seconds else None
        return base
    finally:
        capture.release()


def build_model(model_name: str):
    if torch is None:
        raise AnalysisError("Torch and torchvision are required for checkpoint-backed analysis.")
    if model_name == "XCEPTION":
        return xception_origin.xception(num_classes=2, pretrained="")
    if model_name == "MESO4":
        return Meso4()
    if model_name == "MESOINCEPTION4":
        return MesoInception4()
    if model_name == "EFFICIENTB0":
        return EfficientNet.from_pretrained("efficientnet-b0", in_channels=3, num_classes=2)
    raise AnalysisError(f"Unsupported model builder for {model_name}")


def build_transform():
    if transforms is None:
        raise AnalysisError("torchvision transforms are required for checkpoint-backed analysis.")
    return transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.4489, 0.3352, 0.3106], std=[0.2380, 0.1965, 0.1962]),
        ]
    )


def run_visual_inference(
    media_path: Path,
    model_name: str,
    checkpoint_path: Path,
    sample_frames: int,
) -> List[Dict[str, object]]:
    model = build_model(model_name)
    state = torch.load(checkpoint_path, map_location="cpu")
    if isinstance(state, dict) and "state_dict" in state:
        state = state["state_dict"]
    model.load_state_dict(state, strict=False)
    model.eval()
    transform = build_transform()

    frames = load_sampled_frames(media_path, sample_frames)
    if not frames:
        raise AnalysisError("No frames could be extracted from the uploaded media.")

    results = []
    with torch.no_grad():
        for frame_index, timestamp_seconds, image in frames:
            tensor = transform(image).unsqueeze(0)
            logits = model(tensor)
            probabilities = torch.softmax(logits, dim=1)[0].cpu().numpy()
            fake_probability = float(probabilities[1]) if len(probabilities) > 1 else float(probabilities[0])
            risk_key, risk_label = classify_probability(fake_probability)
            results.append(
                {
                    "frame_index": int(frame_index),
                    "timestamp_seconds": round(timestamp_seconds, 2),
                    "timestamp_label": format_timestamp(timestamp_seconds),
                    "fake_probability": fake_probability,
                    "risk_label": risk_label,
                    "risk_key": risk_key,
                }
            )
    return results


def load_sampled_frames(media_path: Path, sample_frames: int) -> List[Tuple[int, float, "Image.Image"]]:
    suffix = media_path.suffix.lower()
    if suffix in SUPPORTED_IMAGE_FORMATS:
        if Image is None:
            raise AnalysisError("Pillow is required to process image uploads.")
        with Image.open(media_path) as image:
            return [(0, 0.0, image.convert("RGB").copy())]

    if cv2 is None:
        raise AnalysisError("OpenCV is required to sample frames from videos.")

    capture = cv2.VideoCapture(str(media_path))
    try:
        if not capture.isOpened():
            raise AnalysisError("Unable to open the uploaded video.")
        total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        fps = float(capture.get(cv2.CAP_PROP_FPS) or 0.0)
        if total_frames <= 0:
            raise AnalysisError("The uploaded video does not expose a readable frame count.")
        sample_indices = np.linspace(0, max(total_frames - 1, 0), num=min(sample_frames, total_frames), dtype=int)
        sampled = []
        for frame_index in sample_indices:
            capture.set(cv2.CAP_PROP_POS_FRAMES, int(frame_index))
            ok, frame = capture.read()
            if not ok:
                continue
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            timestamp = (float(frame_index) / fps) if fps else 0.0
            sampled.append((int(frame_index), timestamp, Image.fromarray(rgb)))
        return sampled
    finally:
        capture.release()


def build_placeholder_frame_results(metadata: MediaMetadata, sample_frames: int) -> List[Dict[str, object]]:
    total = max(1, min(sample_frames, metadata.frame_count or sample_frames))
    results = []
    for idx in range(total):
        timestamp = 0.0
        if metadata.duration_seconds and total > 1:
            timestamp = (metadata.duration_seconds / (total - 1)) * idx
        results.append(
            {
                "frame_index": idx,
                "timestamp_seconds": round(timestamp, 2),
                "timestamp_label": format_timestamp(timestamp),
                "fake_probability": 0.5,
                "risk_label": "Uncertain",
                "risk_key": "uncertain",
            }
        )
    return results


def summarize_frame_results(frame_results: List[Dict[str, object]], warnings: List[str]):
    probabilities = [float(item["fake_probability"]) for item in frame_results]
    confidence_score = float(sum(probabilities) / len(probabilities)) if probabilities else 0.5
    risk_key, risk_label = classify_probability(confidence_score)
    flagged = [int(item["frame_index"]) for item in frame_results if float(item["fake_probability"]) >= 0.65]

    if warnings and all(abs(prob - 0.5) < 1e-8 for prob in probabilities):
        verdict = "Needs configured model checkpoint"
        summary = "Manual review is available, but automated model-backed scoring is pending checkpoint configuration."
        return verdict, confidence_score, "uncertain", summary, flagged

    if risk_key == "likely_fake":
        summary = f"Likely manipulated. {len(flagged)} sampled frame(s) crossed the warning threshold."
    elif risk_key == "likely_real":
        summary = "Likely authentic under the configured model, with low fake probability across sampled frames."
    else:
        summary = "Uncertain result. Sampled frames show mixed or borderline manipulation risk."
    return risk_label, confidence_score, risk_key, summary, flagged


def build_frame_stats(frame_results: List[Dict[str, object]]) -> Dict[str, object]:
    counts = {"likely_fake": 0, "uncertain": 0, "likely_real": 0}
    for item in frame_results:
        label, _ = classify_probability(float(item["fake_probability"]))
        counts[label] += 1
    return {
        "sampled_frames": len(frame_results),
        "fake_frames": counts["likely_fake"],
        "uncertain_frames": counts["uncertain"],
        "real_frames": counts["likely_real"],
        "avg_fake_probability": round(
            float(sum(float(item["fake_probability"]) for item in frame_results) / max(len(frame_results), 1)), 4
        ),
    }


def classify_probability(fake_probability: float) -> Tuple[str, str]:
    if fake_probability <= RISK_THRESHOLDS["real_max"]:
        return "likely_real", "Likely Real"
    if fake_probability <= RISK_THRESHOLDS["uncertain_max"]:
        return "uncertain", "Uncertain"
    return "likely_fake", "Likely Fake"


def format_timestamp(seconds: float) -> str:
    seconds = max(0, int(round(seconds)))
    mins, secs = divmod(seconds, 60)
    hours, mins = divmod(mins, 60)
    if hours:
        return f"{hours:02d}:{mins:02d}:{secs:02d}"
    return f"{mins:02d}:{secs:02d}"


def save_uploaded_file(uploaded_file) -> Path:
    suffix = Path(uploaded_file.name).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
        tmp_file.write(uploaded_file.getbuffer())
        return Path(tmp_file.name)
