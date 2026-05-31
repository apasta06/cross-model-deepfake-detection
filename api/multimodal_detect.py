"""Reusable multimodal video/audio deepfake inference.

This module keeps the model architecture and scoring behavior from
detect_video.py, but returns structured data that can be consumed by FastAPI
or a CLI wrapper. Audio failures are non-fatal: the caller receives a
visual-only result with warnings.
"""
from __future__ import annotations

import io
import os
import tempfile
import base64
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

try:  # Heavy inference dependencies are optional for lightweight unit tests.
    import cv2
except ImportError:  # pragma: no cover
    cv2 = None

try:
    import librosa
except ImportError:  # pragma: no cover
    librosa = None

try:
    import numpy as np
except ImportError:  # pragma: no cover
    np = None

try:
    import torch
except ImportError:  # pragma: no cover
    torch = None

try:
    from facenet_pytorch import MTCNN
except ImportError:  # pragma: no cover
    MTCNN = None

try:
    from moviepy import VideoFileClip
except ImportError:  # pragma: no cover
    VideoFileClip = None

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    Image = None

try:
    from torchvision import models, transforms
except ImportError:  # pragma: no cover
    models = None
    transforms = None


VIDEO_THRESHOLD = 0.60
AUDIO_THRESHOLD = 0.50
TEMPERATURE = 8.0
DEVICE = torch.device("cuda" if torch and torch.cuda.is_available() else "cpu") if torch else "cpu"

DEFAULT_VIDEO_CHECKPOINT = "best_corrected_model.pt"
DEFAULT_AUDIO_CHECKPOINT = "best_audio_model.pt"


class MultimodalDetectionError(RuntimeError):
    """Raised when required visual inference cannot be completed."""


@dataclass(frozen=True)
class MultimodalConfig:
    video_checkpoint: Path
    audio_checkpoint: Optional[Path] = None
    video_threshold: float = VIDEO_THRESHOLD
    audio_threshold: float = AUDIO_THRESHOLD
    temperature: float = TEMPERATURE
    sample_frames: int = 20
    device: torch.device = DEVICE


@dataclass(frozen=True)
class VisualFrameScore:
    frame_index: int
    timestamp_seconds: float
    fake_probability: float
    thumbnail_url: Optional[str] = None


@dataclass(frozen=True)
class FusionResult:
    classification: str
    alert_level: str
    fused_score: float
    audio_available: bool


@dataclass(frozen=True)
class MultimodalDetectionResult:
    video_score: float
    audio_score: Optional[float]
    fused_score: float
    classification: str
    alert_level: str
    frame_scores: list[VisualFrameScore]
    audio_available: bool
    warnings: list[str] = field(default_factory=list)


def _require_inference_dependencies(*dependencies: tuple[str, object]) -> None:
    missing = [name for name, dependency in dependencies if dependency is None]
    if missing:
        raise MultimodalDetectionError(
            "Missing inference dependencies: " + ", ".join(missing) + ". Install the project requirements before running detection."
        )


def build_video_transform():
    _require_inference_dependencies(("torchvision", transforms))
    return transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )


def build_audio_transform():
    _require_inference_dependencies(("torchvision", transforms))
    return transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.Grayscale(num_output_channels=3),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )


def build_thumbnail_data_url(image, max_size: tuple[int, int] = (320, 320), quality: int = 80) -> str:
    _require_inference_dependencies(("Pillow", Image))
    thumbnail = image.copy().convert("RGB")
    thumbnail.thumbnail(max_size)
    buffer = io.BytesIO()
    thumbnail.save(buffer, format="JPEG", quality=quality, optimize=True)
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/jpeg;base64,{encoded}"


def default_video_checkpoint(base_dir: Optional[Path] = None) -> Path:
    root = base_dir or Path(__file__).resolve().parent.parent
    return root / DEFAULT_VIDEO_CHECKPOINT


def default_audio_checkpoint(base_dir: Optional[Path] = None) -> Path:
    root = base_dir or Path(__file__).resolve().parent.parent
    return root / DEFAULT_AUDIO_CHECKPOINT


def load_video_model(checkpoint_path: Path, device: torch.device = DEVICE):
    _require_inference_dependencies(("torch", torch), ("torchvision", models))
    if not checkpoint_path.exists():
        raise MultimodalDetectionError(f"Video model weights not found at {checkpoint_path}.")

    model = models.efficientnet_b0(weights=None)
    in_features = model.classifier[1].in_features
    model.classifier = torch.nn.Sequential(
        torch.nn.Dropout(p=0.3),
        torch.nn.Linear(in_features, 1),
    )
    model.load_state_dict(torch.load(checkpoint_path, map_location=device, weights_only=True))
    return model.to(device).eval()


def load_audio_model(checkpoint_path: Path, device: torch.device = DEVICE):
    _require_inference_dependencies(("torch", torch), ("torchvision", models))
    if not checkpoint_path.exists():
        raise MultimodalDetectionError(f"Audio model weights not found at {checkpoint_path}.")

    model = models.efficientnet_b0(weights=None)
    in_features = model.classifier[1].in_features
    model.classifier = torch.nn.Sequential(
        torch.nn.Dropout(p=0.4),
        torch.nn.Linear(in_features, 1),
    )
    model.load_state_dict(torch.load(checkpoint_path, map_location=device, weights_only=True))
    return model.to(device).eval()


def analyze_visual_track(
    video_path: Path,
    video_model,
    sample_frames: int,
    temperature: float,
    device: torch.device = DEVICE,
) -> list[VisualFrameScore]:
    _require_inference_dependencies(
        ("cv2", cv2),
        ("numpy", np),
        ("torch", torch),
        ("Pillow", Image),
        ("facenet_pytorch", MTCNN),
    )
    capture = cv2.VideoCapture(str(video_path))
    try:
        if not capture.isOpened():
            raise MultimodalDetectionError("Unable to open the uploaded video.")

        total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        fps = float(capture.get(cv2.CAP_PROP_FPS) or 0.0)
        if total_frames <= 0:
            raise MultimodalDetectionError("The uploaded video does not expose a readable frame count.")

        sample_count = max(1, min(int(sample_frames), total_frames))
        sample_indices = np.linspace(0, max(total_frames - 1, 0), num=sample_count, dtype=int)
        mtcnn = MTCNN(keep_all=False, device=device, image_size=224, post_process=False)
        scores: list[VisualFrameScore] = []

        transform_video = build_video_transform()
        with torch.no_grad():
            for frame_index in sample_indices:
                capture.set(cv2.CAP_PROP_POS_FRAMES, int(frame_index))
                ok, frame = capture.read()
                if not ok:
                    continue

                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                face_img = mtcnn(frame_rgb)
                if face_img is None:
                    continue

                face_np = face_img.permute(1, 2, 0).byte().numpy()
                face_pil = Image.fromarray(face_np)

                buffer = io.BytesIO()
                face_pil.save(buffer, format="JPEG", quality=95)
                buffer.seek(0)
                face_pil_compressed = Image.open(buffer)
                try:
                    thumbnail_url = build_thumbnail_data_url(face_pil_compressed)
                except Exception:
                    thumbnail_url = None

                face_tensor = transform_video(face_pil_compressed).unsqueeze(0).to(device)
                output = video_model(face_tensor)
                probability = torch.sigmoid(output / temperature).item()
                timestamp = (float(frame_index) / fps) if fps else 0.0
                scores.append(
                    VisualFrameScore(
                        frame_index=int(frame_index),
                        timestamp_seconds=round(timestamp, 2),
                        fake_probability=float(probability),
                        thumbnail_url=thumbnail_url,
                    )
                )

        if not scores:
            raise MultimodalDetectionError("Frame extraction failed. Face cannot be tracked.")
        return scores
    finally:
        capture.release()


def analyze_audio_track(
    video_path: Path,
    audio_model,
    temperature: float,
    device: torch.device = DEVICE,
) -> tuple[Optional[float], list[str]]:
    _require_inference_dependencies(
        ("cv2", cv2),
        ("librosa", librosa),
        ("numpy", np),
        ("torch", torch),
        ("Pillow", Image),
        ("moviepy", VideoFileClip),
    )
    warnings: list[str] = []
    temp_audio_path: Optional[Path] = None
    video_clip = None

    try:
        video_clip = VideoFileClip(str(video_path))
        if video_clip.audio is None:
            return None, ["No audio track detected. Analysis used visual-only fallback."]

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_audio:
            temp_audio_path = Path(tmp_audio.name)

        video_clip.audio.write_audiofile(str(temp_audio_path), logger=None, fps=16000)

        y, sr = librosa.load(temp_audio_path, sr=16000)
        mel_spec = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128, fmax=4000)
        mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
        mel_normalized = cv2.normalize(
            mel_spec_db,
            None,
            alpha=0,
            beta=255,
            norm_type=cv2.NORM_MINMAX,
            dtype=cv2.CV_8U,
        )
        mel_pil = Image.fromarray(mel_normalized)
        transform_audio = build_audio_transform()
        audio_tensor = transform_audio(mel_pil).unsqueeze(0).to(device)

        with torch.no_grad():
            output = audio_model(audio_tensor)
            probability = torch.sigmoid(output / temperature).item()
        return float(probability), warnings
    except Exception as exc:  # Audio is optional; keep visual-only result usable.
        return None, [f"Audio analysis failed. Analysis used visual-only fallback: {exc}"]
    finally:
        if video_clip is not None:
            video_clip.close()
        if temp_audio_path and temp_audio_path.exists():
            try:
                os.remove(temp_audio_path)
            except OSError:
                pass


def fuse_scores(
    video_score: float,
    audio_score: Optional[float],
    video_threshold: float = VIDEO_THRESHOLD,
    audio_threshold: float = AUDIO_THRESHOLD,
) -> FusionResult:
    if audio_score is None:
        return FusionResult(
            classification="Video Analysis (Audio Missing/Degraded)",
            alert_level="FAKE" if video_score > video_threshold else "REAL",
            fused_score=float(video_score),
            audio_available=False,
        )

    is_video_fake = video_score > video_threshold
    is_audio_fake = audio_score > audio_threshold
    fused_score = float((video_score + audio_score) / 2)

    if not is_video_fake and not is_audio_fake:
        classification = "Real Video & Real Audio (RVRA)"
        alert_level = "AUTHENTIC"
    elif is_video_fake and not is_audio_fake:
        classification = "Fake Video & Real Audio (FVRA)"
        alert_level = "PARTIAL FORGERY (Visual Identity Swap)"
    elif not is_video_fake and is_audio_fake:
        classification = "Real Video & Fake Audio (RVFA)"
        alert_level = "PARTIAL FORGERY (Acoustic Voice Clone)"
    else:
        classification = "Fake Video & Fake Audio (FVFA)"
        alert_level = "TOTAL MULTIMODAL SYNTHESIS"

    return FusionResult(
        classification=classification,
        alert_level=alert_level,
        fused_score=fused_score,
        audio_available=True,
    )


def analyze_video_file(video_path: Path, config: MultimodalConfig) -> MultimodalDetectionResult:
    _require_inference_dependencies(("numpy", np))
    if not video_path.exists():
        raise MultimodalDetectionError(f"Video target file not found at {video_path}.")
    if not config.video_checkpoint.exists():
        raise MultimodalDetectionError(f"Video model weights not found at {config.video_checkpoint}.")

    warnings: list[str] = []
    video_model = load_video_model(config.video_checkpoint, config.device)
    frame_scores = analyze_visual_track(
        video_path=video_path,
        video_model=video_model,
        sample_frames=config.sample_frames,
        temperature=config.temperature,
        device=config.device,
    )
    video_score = float(np.mean([score.fake_probability for score in frame_scores]))

    audio_score: Optional[float] = None
    if config.audio_checkpoint and config.audio_checkpoint.exists():
        audio_model = load_audio_model(config.audio_checkpoint, config.device)
        audio_score, audio_warnings = analyze_audio_track(
            video_path=video_path,
            audio_model=audio_model,
            temperature=config.temperature,
            device=config.device,
        )
        warnings.extend(audio_warnings)
    else:
        warnings.append("Audio checkpoint missing. Analysis used visual-only fallback.")

    fusion = fuse_scores(
        video_score=video_score,
        audio_score=audio_score,
        video_threshold=config.video_threshold,
        audio_threshold=config.audio_threshold,
    )

    return MultimodalDetectionResult(
        video_score=video_score,
        audio_score=audio_score,
        fused_score=fusion.fused_score,
        classification=fusion.classification,
        alert_level=fusion.alert_level,
        frame_scores=frame_scores,
        audio_available=fusion.audio_available,
        warnings=warnings,
    )
