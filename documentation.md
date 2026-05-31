# Cross-Model Deepfake Detection Backend System

This document summarizes the current backend and frontend integration for the project application. The active application path is FastAPI plus React, with inference handled by the real multimodal detector refactored from `detect_video.py`.

## Project Status

- Active API branch: `wire-multimodal-detector-api`
- Implementation commit: `6c31df6 Wire API to multimodal detector`
- Backend entry point: `api/main.py`
- Inference module: `api/multimodal_detect.py`
- Upload endpoint: `POST /api/v1/analyze`
- Frontend: `frontend/` React/Vite app
- Supported model: `MULTIMODAL_EFFICIENTB0`
- Upload type: video only
- Default sample frames: `20`

## Directory And File Structure

```text
cross-model-deepfake-detection/
├── api/
│   ├── main.py                 # FastAPI app, CORS, router mounting
│   ├── deps.py                 # Settings and multimodal checkpoint resolution
│   ├── models.py               # Pydantic response schemas
│   ├── multimodal_detect.py    # Real video/audio detector refactored from detect_video.py
│   └── routes/
│       ├── analyze.py          # POST /api/v1/analyze
│       ├── meta.py             # GET /health and /models
│       ├── history.py          # Saved result lookup
│       └── reports.py          # HTML/JSON report download
├── detect_video.py             # Original CLI-style inference script
├── frontend/                   # React/Vite frontend
├── tests/
│   └── test_multimodal_detect.py
├── ui_mvp/                     # Legacy Streamlit schemas/storage/report helpers
├── best_corrected_model.pt     # Default visual checkpoint location when present
└── best_audio_model.pt         # Default optional audio checkpoint location when present
```

## Inference Architecture

The detector is multimodal and uses separate EfficientNet-B0 models for visual and audio signals.

### Visual Track

- Samples up to `20` frames by default.
- Uses MTCNN to extract a face crop from each sampled frame.
- Simulates JPEG compression at quality 95 before inference.
- Applies the same normalization from `detect_video.py`.
- Scores each face frame with EfficientNet-B0 using a single output logit.
- Applies temperature scaling with `TEMPERATURE = 8.0`.
- Uses `VIDEO_THRESHOLD = 0.60` for visual suspiciousness.

### Audio Track

- Extracts audio with MoviePy at 16 kHz.
- Builds a Librosa mel spectrogram with `n_mels=128` and `fmax=4000`.
- Converts the spectrogram into an EfficientNet-compatible image.
- Scores with a separate EfficientNet-B0 audio model.
- Uses `AUDIO_THRESHOLD = 0.50` for audio suspiciousness.

Audio inference is optional. If the audio checkpoint is missing, the video has no audio track, or audio extraction fails, the API returns visual-only fallback with warnings.

## Fusion Logic

The API maps visual/audio scores into the same quadrant logic as `detect_video.py`.

| Visual score | Audio score | Classification | Alert level |
| --- | --- | --- | --- |
| clean | clean | `Real Video & Real Audio (RVRA)` | `AUTHENTIC` |
| fake | clean | `Fake Video & Real Audio (FVRA)` | `PARTIAL FORGERY (Visual Identity Swap)` |
| clean | fake | `Real Video & Fake Audio (RVFA)` | `PARTIAL FORGERY (Acoustic Voice Clone)` |
| fake | fake | `Fake Video & Fake Audio (FVFA)` | `TOTAL MULTIMODAL SYNTHESIS` |

When audio is unavailable:

- Classification: `Video Analysis (Audio Missing/Degraded)`
- Alert level: `FAKE` if visual score is above `VIDEO_THRESHOLD`, otherwise `REAL`
- Fused score: visual score

When both modalities are available, fused suspiciousness is the average of visual and audio scores.

## API Contract

### Model Catalog

`GET /api/v1/models` returns only:

```json
{
  "models": [
    {
      "key": "MULTIMODAL_EFFICIENTB0",
      "description": "Multimodal EfficientNet-B0 video/audio deepfake detector."
    }
  ]
}
```

### Analyze Endpoint

Route:

```text
POST /api/v1/analyze
```

Request type: `multipart/form-data`

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `file` | File | yes | Video file, one of `.mp4`, `.avi`, `.mov`, `.mkv`, `.mts`, `.webm` |
| `model` | string | yes | Must be `MULTIMODAL_EFFICIENTB0` |
| `sample_frames` | integer | no | Number of visual frames to sample, 1-120, default `20` |

Images are rejected because the active detector is video/audio multimodal.

### Response

The response is the existing frontend-compatible `AnalysisResult` shape.

Key fields:

- `verdict`: fusion alert level
- `confidence_score`: fused suspiciousness score, or visual score for fallback
- `risk_level`: UI risk bucket derived from `confidence_score`
- `summary_text`: human-readable multimodal summary
- `frame_results`: visual frame-level scores
- `flagged_frame_indices`: frames above `VIDEO_THRESHOLD`
- `warnings`: non-fatal fallback messages
- `report_payload`: raw multimodal details, including visual score, audio score, fused score, thresholds, and classification

Example `report_payload`:

```json
{
  "classification": "Fake Video & Real Audio (FVRA)",
  "alert_level": "PARTIAL FORGERY (Visual Identity Swap)",
  "video_score": 0.82,
  "audio_score": 0.32,
  "fused_score": 0.57,
  "video_threshold": 0.6,
  "audio_threshold": 0.5,
  "audio_available": true,
  "sampled_visual_frames": 20,
  "model_family": "EfficientNet-B0 multimodal"
}
```

## Checkpoint Configuration

The video checkpoint is required.

Resolution order:

1. `CHECKPOINT_MULTIMODAL_VIDEO`
2. `VIDEO_MODEL_PATH`
3. `best_corrected_model.pt` at repository root

The audio checkpoint is optional.

Resolution order:

1. `CHECKPOINT_MULTIMODAL_AUDIO`
2. `AUDIO_MODEL_PATH`
3. `best_audio_model.pt` at repository root

Example:

```bash
CHECKPOINT_MULTIMODAL_VIDEO=best_corrected_model.pt CHECKPOINT_MULTIMODAL_AUDIO=best_audio_model.pt uvicorn api.main:app --reload --port 8000
```

## Local Setup

Backend:

```bash
source .venv/bin/activate
uvicorn api.main:app --reload --port 8000
```

Frontend:

```bash
cd frontend
npm run dev
```

Open the frontend at `http://127.0.0.1:5173` when working from WSL/browser environments.

## Verification

Backend syntax and lightweight fusion tests:

```bash
python3 -m py_compile api/routes/analyze.py api/routes/meta.py api/deps.py api/models.py api/multimodal_detect.py tests/test_multimodal_detect.py
python3 -m unittest tests/test_multimodal_detect.py
```

Full Python tests in the configured venv:

```bash
source .venv/bin/activate
python -m unittest tests/test_multimodal_detect.py tests/test_ui_mvp.py
```

Frontend:

```bash
cd frontend
npm run build
npm run test:e2e
```

## Notes For Future Work

- `detect_video.py` should remain runnable as a CLI wrapper, but the reusable logic now lives in `api/multimodal_detect.py`.
- The frontend currently shows a static model label rather than a dropdown because only one real model is supported.
- The current endpoint is synchronous; long videos may take noticeable time, especially on CPU.
- More detailed multimodal visualization can be added later by reading `report_payload` in the React UI.
