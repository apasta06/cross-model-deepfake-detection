# Cross-Model Deepfake Detection API

FastAPI service for the project React frontend. The active API path now wraps the real multimodal detector refactored from `detect_video.py`, not the older `ui_mvp.analysis.analyze_media` placeholder path.

## Current Status

- Backend entry point: `api/main.py`
- Main inference module: `api/multimodal_detect.py`
- Upload endpoint: `POST /api/v1/analyze`
- Frontend client: `frontend/src/lib/api.ts`
- Supported model key: `MULTIMODAL_EFFICIENTB0`
- Supported upload type: video only
- Default sampled frames: `20`, matching `detect_video.py`
- Visual checkpoint is required
- Audio checkpoint/audio track are optional; missing audio falls back to visual-only analysis with warnings
- Optional Grad-CAM heatmaps via the `generate_heatmaps` flag (off by default; see "Grad-CAM Heatmaps")

## Architecture

The service is organized into these layers:

- `api/main.py`: creates the FastAPI app, configures CORS, and mounts routers under `/api/v1` by default.
- `api/routes/meta.py`: serves `/health` and `/models`.
- `api/routes/analyze.py`: validates uploads, resolves checkpoints, calls the multimodal detector, maps results to the frontend-compatible `AnalysisResult`, and persists history/result JSON.
- `api/multimodal_detect.py`: reusable multimodal EfficientNet-B0 video/audio inference logic refactored from `detect_video.py`.
- `api/gradcam.py`: opt-in Grad-CAM helper used by `multimodal_detect.py` to produce per-frame heatmap overlays.
- `api/deps.py`: settings and checkpoint resolution.
- `api/models.py`: Pydantic response models matching `frontend/src/types/analysis.ts`.
- `ui_mvp/schemas.py` and `ui_mvp/storage.py`: dataclass response shape and lightweight history/result persistence reused by the API.

The legacy Streamlit/UI MVP pipeline in `ui_mvp.analysis` still exists, but the current FastAPI `/analyze` endpoint uses `api.multimodal_detect.analyze_video_file`.

## Repository Layout

```text
cross-model-deepfake-detection/
├── api/
│   ├── main.py
│   ├── deps.py
│   ├── models.py
│   ├── gradcam.py
│   ├── multimodal_detect.py
│   └── routes/
│       ├── analyze.py
│       ├── history.py
│       ├── meta.py
│       └── reports.py
├── detect_video.py
├── frontend/
│   └── src/
│       ├── lib/api.ts
│       └── types/analysis.ts
├── tests/
│   └── test_multimodal_detect.py
├── ui_mvp/
└── API.md
```

Runtime metadata is stored under `.ui_mvp_data/`:

- `.ui_mvp_data/history.jsonl`: summary row per analysis
- `.ui_mvp_data/results/<analysis_id>.json`: full `AnalysisResult`
- `.ui_mvp_data/reports/`: generated report files

Raw uploaded videos are written to a temp file for one request and deleted in a `finally` block.

## Setup

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

If using a split dependency setup, ensure the active environment has FastAPI plus inference dependencies used by `api/multimodal_detect.py`:

- `torch`
- `torchvision`
- `opencv-python`
- `numpy`
- `Pillow`
- `facenet-pytorch`
- `librosa`
- `moviepy`
- `python-multipart`
- `uvicorn`
- `fastapi`

## Running The Backend

Start the API from repository root:

```bash
source .venv/bin/activate
uvicorn api.main:app --reload --port 8000
```

Useful URLs:

- `http://localhost:8000/docs`
- `http://localhost:8000/redoc`
- `http://localhost:8000/openapi.json`
- `http://localhost:8000/api/v1/health`
- `http://localhost:8000/api/v1/models`

## Checkpoints

The multimodal detector has separate visual and audio checkpoints.

### Video Checkpoint

Required. Resolution order:

1. `CHECKPOINT_MULTIMODAL_VIDEO`
2. `VIDEO_MODEL_PATH`
3. Repository root `best_corrected_model.pt`

If no video checkpoint is found, `POST /api/v1/analyze` returns HTTP `500` with an actionable message.

### Audio Checkpoint

Optional. Resolution order:

1. `CHECKPOINT_MULTIMODAL_AUDIO`
2. `AUDIO_MODEL_PATH`
3. Repository root `best_audio_model.pt`

If no audio checkpoint is found, the API still runs visual inference and returns a visual-only fallback result with a warning.

Example explicit startup:

```bash
CHECKPOINT_MULTIMODAL_VIDEO=best_corrected_model.pt CHECKPOINT_MULTIMODAL_AUDIO=best_audio_model.pt uvicorn api.main:app --reload --port 8000
```

## Model Catalog

`GET /api/v1/models` returns one model:

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

The frontend displays this as a static model label instead of a model dropdown.

## Endpoints

All endpoints are mounted under `/api/v1` unless `API_PREFIX` is changed.

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/v1/health` | Liveness probe |
| `GET` | `/api/v1/models` | List supported model catalog |
| `POST` | `/api/v1/analyze` | Upload video and run multimodal analysis |
| `GET` | `/api/v1/analyses` | List saved analysis summaries |
| `GET` | `/api/v1/analyses/{analysis_id}` | Fetch saved full result |
| `GET` | `/api/v1/analyses/{analysis_id}/report` | Download HTML or JSON report |

## POST /api/v1/analyze

Accepts `multipart/form-data`.

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `file` | binary | yes | Video upload. Supported extensions: `.mp4`, `.avi`, `.mov`, `.mkv`, `.mts`, `.webm` |
| `model` | string | yes | Must be `MULTIMODAL_EFFICIENTB0` |
| `sample_frames` | integer, 1-120 | no | Visual frames to sample. Defaults to `20` |
| `generate_heatmaps` | boolean | no | Opt-in Grad-CAM explainability. Defaults to `false`. When `true`, each sampled frame with a detectable face gains a heatmap overlay and bounding box (see "Grad-CAM Heatmaps"). Slower, especially on CPU |

Images are not accepted by the current multimodal API.

Status codes:

- `200`: analysis complete
- `400`: invalid upload, unsupported format, unreadable video, or no trackable face frames
- `422`: model key is not `MULTIMODAL_EFFICIENTB0`
- `500`: server-side inference configuration/runtime failure, including missing required video checkpoint

Example request:

```bash
curl -X POST http://localhost:8000/api/v1/analyze \
  -F "file=@sample.mp4" \
  -F "model=MULTIMODAL_EFFICIENTB0" \
  -F "sample_frames=20"
```

Example request with Grad-CAM heatmaps enabled:

```bash
curl -X POST http://localhost:8000/api/v1/analyze \
  -F "file=@sample.mp4" \
  -F "model=MULTIMODAL_EFFICIENTB0" \
  -F "sample_frames=20" \
  -F "generate_heatmaps=true"
```

## Multimodal Inference Behavior

The visual path follows `detect_video.py` behavior:

- EfficientNet-B0 with a single output logit
- MTCNN face crop per sampled frame
- JPEG compression simulation at quality 95
- ImageNet normalization
- Temperature scaling with `TEMPERATURE = 8.0`
- Visual threshold `VIDEO_THRESHOLD = 0.60`

The audio path:

- Extracts audio with MoviePy at 16 kHz
- Builds a Librosa mel spectrogram with `n_mels=128` and `fmax=4000`
- Maps the mel image through EfficientNet-B0 with a single output logit
- Uses audio threshold `AUDIO_THRESHOLD = 0.50`

Fusion matrix:

| Video | Audio | Classification | Alert level |
| --- | --- | --- | --- |
| real | real | `Real Video & Real Audio (RVRA)` | `AUTHENTIC` |
| fake | real | `Fake Video & Real Audio (FVRA)` | `PARTIAL FORGERY (Visual Identity Swap)` |
| real | fake | `Real Video & Fake Audio (RVFA)` | `PARTIAL FORGERY (Acoustic Voice Clone)` |
| fake | fake | `Fake Video & Fake Audio (FVFA)` | `TOTAL MULTIMODAL SYNTHESIS` |

If audio is unavailable, the classification becomes `Video Analysis (Audio Missing/Degraded)` and the alert level is based on the visual score only.

## AnalysisResult Response

The response shape matches `frontend/src/types/analysis.ts`.

Important fields:

| Field | Meaning |
| --- | --- |
| `verdict` | Fusion alert level, for example `AUTHENTIC`, `FAKE`, or `PARTIAL FORGERY (Visual Identity Swap)` |
| `confidence_score` | Fused suspiciousness score; visual-only score when audio is unavailable |
| `risk_level` | UI risk bucket derived from `confidence_score` |
| `summary_text` | Human-readable multimodal summary |
| `frame_results` | Per-frame visual suspiciousness scores (see "Per-Frame Fields") |
| `flagged_frame_indices` | Visual frame indices where score is greater than `VIDEO_THRESHOLD` |
| `warnings` | Non-fatal fallback details, especially audio fallback |
| `report_payload` | Raw multimodal details for reporting/UI expansion |

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
  "model_family": "EfficientNet-B0 multimodal",
  "warnings": []
}
```

Visual-only fallback example:

```json
{
  "classification": "Video Analysis (Audio Missing/Degraded)",
  "alert_level": "FAKE",
  "video_score": 0.78,
  "audio_score": null,
  "fused_score": 0.78,
  "audio_available": false,
  "warnings": ["No audio track detected. Analysis used visual-only fallback."]
}
```

Risk buckets used by the UI:

- `confidence_score <= 0.35`: `likely_real`
- `0.35 < confidence_score <= 0.74`: `uncertain`
- `confidence_score > 0.74`: `likely_fake`

### Per-Frame Fields (`frame_results`)

Each entry in `frame_results` describes one sampled visual frame:

| Field | Meaning |
| --- | --- |
| `frame_index` | Source frame index in the video |
| `timestamp_seconds` / `timestamp_label` | Frame time, raw seconds and formatted label |
| `fake_probability` | Per-frame visual suspiciousness (0-1) |
| `risk_label` / `risk_key` | UI risk bucket for the frame |
| `thumbnail_url` | Base64 JPEG data URL of the cropped face |
| `heatmap_url` | Base64 JPEG data URL of the Grad-CAM overlay. `null` unless `generate_heatmaps=true` and a face box was recovered for the frame |
| `face_box` | `[x1, y1, x2, y2]` face rectangle in original-frame pixels, used to position the heatmap over the video. `null` when no usable box was detected |
| `frame_width` / `frame_height` | Source frame resolution the `face_box` is expressed in. `null` when `face_box` is `null` |

The last four heatmap-related fields are always present in the schema but are `null` on a normal (non-heatmap) run, so existing consumers are unaffected.

## Grad-CAM Heatmaps

Grad-CAM is an opt-in explainability feature that highlights which regions of a
face most influenced the visual model's score for a given frame.

Key behaviors:

- **Opt-in, default off.** Heatmaps run only when `generate_heatmaps=true` is
  sent to `POST /api/v1/analyze`. A normal run is byte-for-byte unchanged and
  pays no extra cost.
- **Per sampled frame.** When enabled, every sampled frame with a detectable
  face gets a heatmap overlay (`heatmap_url`) plus the face bounding box
  (`face_box`) and source resolution (`frame_width`/`frame_height`).
- **Scores are unaffected.** Frame scoring runs under `torch.no_grad()` exactly
  as before; the Grad-CAM forward/backward pass is scoped separately, so
  `fake_probability` and the fused verdict are identical whether or not
  heatmaps are requested.
- **Graceful per-frame fallback.** If the face detector returns no usable box
  for a frame (blurry, turned away, multi-face ambiguity, out-of-bounds), that
  frame's `heatmap_url`/`face_box` stay `null`; the frame is still scored
  normally. Heatmap coverage is therefore "most sampled frames with a face,"
  not guaranteed to be all of them.
- **Cost.** With heatmaps on, each frame runs a second MTCNN detection pass (to
  recover the box), a backward pass, and an extra JPEG encode. On CPU (the
  default when CUDA is unavailable) this noticeably increases analysis time;
  this is the reason the feature is opt-in.

Implementation: `api/gradcam.py` (the `GradCAM` helper, hooked on the
EfficientNet-B0 final conv block, single-logit backward, BGR throughout until
JPEG encode), wired into `analyze_visual_track` in `api/multimodal_detect.py`.

The frontend (`frontend/src/components/ForensicMediaViewer.tsx`) overlays the
heatmap on the video while paused at the selected frame, hides it during
playback, and frames it with a verdict-driven border, opacity, and chip derived
from the frame's `fake_probability` versus `video_threshold` (Grad-CAM colors
indicate where the model looked, not whether the frame is fake, so the verdict
is surfaced separately).

### Grad-CAM Diagnostic Logging

`analyze_visual_track` emits `[gradcam-diagnostic]` log records (via the module
logger in `api/multimodal_detect.py`) on every heatmap-enabled run. These are
intentionally retained as a verification aid: they make it possible to confirm
heatmaps are actually being produced and to pinpoint why a frame has no overlay.

When `generate_heatmaps=true`, watch the uvicorn console for one line per
sampled frame:

- `frame N: heatmap OK, box=...` — heatmap generated and positioned successfully.
- `frame N: no usable face box ...` — the detector found no usable box; frame is scored but has no overlay.
- `frame N: heatmap generation raised` — an exception was caught (full traceback logged); frame keeps its score, overlay skipped.
- `GradCAM init failed; heatmaps disabled for this run` — the helper could not initialize; the whole run produces no heatmaps.

If the "Show heatmap" toggle in the UI is disabled, it means the result carried
no `heatmap_url` on any frame. The diagnostic lines tell you which case above
caused it. Absence of any `[gradcam-diagnostic]` line during a heatmap-enabled
run indicates the flag never reached the detector (for example, a stale
`api/routes/analyze.py` that lacks the `generate_heatmaps` form field).

## Frontend Integration

Frontend API client:

- `frontend/src/lib/api.ts`
- Default API base: `http://127.0.0.1:8000/api/v1`

The frontend:

- Fetches `/models` during startup
- Displays a static `Multimodal EfficientNet-B0` model label
- Uploads only video formats
- Sends `model=MULTIMODAL_EFFICIENTB0`
- Defaults `sample_frames` to `20`
- Displays `AnalysisResult` without a translation layer

Run frontend locally from `frontend/`:

```bash
npm run dev
```

Build/test:

```bash
npm run build
npm run test:e2e
```

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `API_PREFIX` | `/api/v1` | Prefix mounted before all API routes |
| `API_CORS_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173,http://localhost:6006` | Allowed browser origins |
| `API_MAX_UPLOAD_MB` | `200` | Maximum upload size |
| `CHECKPOINT_MULTIMODAL_VIDEO` | unset | Required visual checkpoint override |
| `VIDEO_MODEL_PATH` | unset | Alternative visual checkpoint override |
| `CHECKPOINT_MULTIMODAL_AUDIO` | unset | Optional audio checkpoint override |
| `AUDIO_MODEL_PATH` | unset | Alternative audio checkpoint override |

Checkpoint paths may be absolute or relative to the repository root.

## Verification

Backend syntax check used during implementation:

```bash
python3 -m py_compile api/routes/analyze.py api/routes/meta.py api/deps.py api/models.py api/multimodal_detect.py tests/test_multimodal_detect.py
```

Lightweight multimodal tests:

```bash
python3 -m unittest tests/test_multimodal_detect.py
```

Full local validation in a configured environment:

```bash
source .venv/bin/activate
python -m unittest tests/test_multimodal_detect.py tests/test_ui_mvp.py
uvicorn api.main:app --reload --port 8000
```

Frontend validation:

```bash
cd frontend
npm run build
npm run test:e2e
```

## Troubleshooting

### `Video checkpoint missing`

The API could not resolve the required visual checkpoint. Set `CHECKPOINT_MULTIMODAL_VIDEO` or place `best_corrected_model.pt` at the repository root.

### Audio checkpoint missing or no audio track

This is non-fatal. The API returns a visual-only result and includes a warning.

### `ModuleNotFoundError` for `cv2`, `torch`, `facenet_pytorch`, `librosa`, or `moviepy`

The active Python environment is missing inference dependencies. Activate the intended venv and install the project requirements.

### Browser CORS errors

Add the frontend origin to `API_CORS_ORIGINS` and restart uvicorn.

### Long analysis time

The endpoint is synchronous. Reduce `sample_frames`, use CUDA, or test with shorter videos. Enabling `generate_heatmaps` increases time further, especially on CPU.

### Heatmaps not appearing / "Show heatmap" toggle disabled

The toggle is disabled only when no frame in the result carried a `heatmap_url`. Run with `generate_heatmaps=true` and watch the uvicorn console for `[gradcam-diagnostic]` lines (see "Grad-CAM Diagnostic Logging"):

- No `[gradcam-diagnostic]` lines at all — the flag did not reach the detector. Confirm `api/routes/analyze.py` is current (it must contain the `generate_heatmaps` form field) and restart uvicorn. A stale or duplicated module file (for example, an `analyze (2).py` copy that is never imported) is a common cause.
- `no usable face box` on every frame — the detector found no usable box; try a video with a clearer, larger, front-facing face.
- `heatmap generation raised` with a traceback — inspect the logged traceback for the specific failure.
- `GradCAM init failed` — the helper could not attach to the model; confirm the visual checkpoint loads and inference dependencies are present.
