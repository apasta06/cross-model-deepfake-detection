# Cross-Model Deepfake Detection — API Reference

HTTP service that exposes the deepfake detection pipeline to clients (primarily
the React frontend in `frontend/`). Built on FastAPI; wraps the inference,
storage, and reporting modules in `ui_mvp/`.

---

## Table of Contents

1. [Architecture](#architecture)
2. [Repository Layout](#repository-layout)
3. [Setup](#setup)
4. [Running the Server](#running-the-server)
5. [Endpoints](#endpoints)
6. [Request and Response Schemas](#request-and-response-schemas)
7. [Frontend Integration](#frontend-integration)
8. [Configuration](#configuration)
9. [Model Checkpoints](#model-checkpoints)
10. [Troubleshooting](#troubleshooting)

---

## Architecture

The service is organized into two layers:

- **`api/`** — the HTTP layer. FastAPI routers, Pydantic schemas, settings,
  and the application entry point. Routes are thin: they validate input,
  call into `ui_mvp/`, and serialize the result.
- **`ui_mvp/`** — the analysis engine. Frame sampling, model loading,
  inference, verdict classification, history persistence, and report
  rendering. No HTTP or framework dependencies.

This separation means the inference pipeline is reusable from any client
(HTTP, CLI, batch script) without coupling to FastAPI.

---

## Repository Layout

```
cross-model-deepfake-detection/
├── api/                              HTTP service layer
│   ├── __init__.py
│   ├── main.py                       FastAPI app, CORS, router mounting
│   ├── models.py                     Pydantic request/response schemas
│   ├── deps.py                       Settings + checkpoint resolution
│   └── routes/
│       ├── __init__.py
│       ├── meta.py                   GET /health, GET /models
│       ├── analyze.py                POST /analyze
│       ├── history.py                GET /analyses, GET /analyses/{id}
│       └── reports.py                GET /analyses/{id}/report
├── ui_mvp/                           Analysis engine
│   ├── analysis.py                   Frame sampling, inference, classification
│   ├── config.py                     Constants (thresholds, supported formats)
│   ├── schemas.py                    AnalysisResult / HistoryRecord dataclasses
│   ├── reporting.py                  HTML and JSON report builders
│   └── storage.py                    History (JSONL) + full result (JSON)
├── frontend/                         React/Vite client (separate project)
├── models/                           Model architecture definitions
├── requirements.txt                  Legacy training/inference dependencies
├── requirements-api.txt              FastAPI service dependencies
├── requirements-inference.txt        Inference dependencies (numpy, torch, etc.)
└── API.md                            This document
```

Data produced at runtime lives under `.ui_mvp_data/`:

- `.ui_mvp_data/history.jsonl` — append-only summary of every analysis
- `.ui_mvp_data/results/<analysis_id>.json` — full result per analysis
- `.ui_mvp_data/reports/` — generated report files

### File-by-file purpose

**`api/main.py`** — FastAPI application factory. Creates the `app` object,
attaches CORS middleware, and mounts each router under the configured prefix
(default `/api/v1`).

**`api/models.py`** — Pydantic models for every request body and response
shape. Field names and types mirror `ui_mvp/schemas.py` and
`frontend/src/types/analysis.ts` so no translation layer is needed between
Python, JSON, and TypeScript.

**`api/deps.py`** — Runtime configuration. `Settings` is read once from
environment variables; `resolve_checkpoint()` maps a model key to a
`.pt` file on disk, with env-var overrides.

**`api/routes/meta.py`** — Liveness probe and model catalog. Stateless,
read-only.

**`api/routes/analyze.py`** — The main upload endpoint. Saves the upload
to a temp file, validates it, resolves the checkpoint, calls
`analyze_media()`, persists the result, and returns it. Cleans up the
temp file in all paths.

**`api/routes/history.py`** — Lists past analyses and fetches a single
past result. Backed by `ui_mvp/storage.py`.

**`api/routes/reports.py`** — Downloads a built report in HTML or JSON
form. Rehydrates the stored result dict into the `AnalysisResult`
dataclass and feeds it to `ui_mvp/reporting.py`.

**`ui_mvp/analysis.py`** — Core pipeline. `analyze_media(media_path,
model_name, checkpoint_path, sample_frames)` performs frame sampling,
runs the model, classifies risk, and returns an `AnalysisResult`. When
`checkpoint_path` is `None` or missing, falls back to metadata-only
review mode with a warning attached to the result.

**`ui_mvp/schemas.py`** — Dataclasses: `MediaMetadata`, `EvidenceAsset`,
`AnalysisResult`, `HistoryRecord`. `to_dict()` is the canonical
JSON-serializable shape.

**`ui_mvp/config.py`** — Thresholds (`RISK_THRESHOLDS`), allowed file
extensions, max upload size, default frame count, and the
`MODEL_OPTIONS` catalog.

**`ui_mvp/reporting.py`** — `build_report_json()` and
`build_report_html()`. The HTML report is a standalone document with
inline CSS, suitable for direct download.

**`ui_mvp/storage.py`** — File-backed persistence. `append_history()` /
`load_history()` for summary records; `save_full_result()` /
`load_full_result()` for full results.

---

## Setup

### Prerequisites

- Python 3.10 or newer (tested on 3.14)
- macOS / Linux. Windows is not tested.

### Installation

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-api.txt
pip install -r requirements-inference.txt
```

`requirements-api.txt` installs FastAPI, uvicorn, and python-multipart.
`requirements-inference.txt` installs numpy, torch, torchvision, opencv,
Pillow, and optional audio/video extras for the legacy `detect_video.py`
CLI. The optional extras (`librosa`, `moviepy`, `facenet-pytorch`) are
not required by the API itself; if any of them fails to install on your
Python version, comment that line out and re-run.

The pins in `requirements.txt` are legacy (Python 3.8 / torch 1.8) and
should not be installed on modern Python.

---

## Running the Server

```bash
source .venv/bin/activate
uvicorn api.main:app --reload --port 8000
```

Confirm it is up by visiting:

- `http://localhost:8000/docs` — interactive Swagger UI
- `http://localhost:8000/redoc` — alternative documentation viewer
- `http://localhost:8000/openapi.json` — machine-readable OpenAPI spec

The `/docs` page is the source of truth for endpoint contracts. Every
schema, parameter, status code, and example is generated from the route
definitions and stays in sync automatically.

---

## Endpoints

All endpoints are mounted under the `/api/v1` prefix.

| Method | Path                                | Purpose                                  |
| ------ | ----------------------------------- | ---------------------------------------- |
| GET    | `/api/v1/health`                    | Liveness probe                           |
| GET    | `/api/v1/models`                    | List supported detection models          |
| POST   | `/api/v1/analyze`                   | Upload media and run analysis            |
| GET    | `/api/v1/analyses`                  | List past analyses (newest first)        |
| GET    | `/api/v1/analyses/{id}`             | Fetch full result for one past analysis  |
| GET    | `/api/v1/analyses/{id}/report`      | Download report (HTML or JSON)           |

### POST /api/v1/analyze

Accepts `multipart/form-data` with these fields:

| Field           | Type          | Required | Description                                                            |
| --------------- | ------------- | -------- | ---------------------------------------------------------------------- |
| `file`          | binary        | yes      | Image or video to analyze                                              |
| `model`         | string        | yes      | One of `XCEPTION`, `MESO4`, `MESOINCEPTION4`, `EFFICIENTB0`            |
| `sample_frames` | integer (1–120) | no     | Frames to sample from a video; ignored for images. Defaults to 12.     |

Supported file extensions (from `ui_mvp/config.py`):

- Video: `.mp4`, `.avi`, `.mov`, `.mkv`, `.mts`, `.webm`
- Image: `.jpg`, `.jpeg`, `.png`, `.bmp`

Max upload size: 200 MB by default (override via `API_MAX_UPLOAD_MB`).

**Status codes:**

- `200` — analysis complete, body is an `AnalysisResult`
- `400` — invalid upload (unsupported format, too large, missing filename, decode failure)
- `422` — unknown model key
- `500` — unexpected inference failure

### GET /api/v1/analyses

Query parameters:

- `limit` (integer, 1–500, optional) — cap the number of records returned.

Returns an array of `HistoryRecord` objects sorted by `created_at` descending.

### GET /api/v1/analyses/{analysis_id}

Returns the full `AnalysisResult` for an analysis. Returns `404` if the
ID is unknown.

### GET /api/v1/analyses/{analysis_id}/report

Query parameters:

- `format` (string, `html` or `json`, default `html`) — report format.

Returns the report as a download (`Content-Disposition: attachment`) with
a sensible filename derived from the original upload name and analysis
ID. Returns `404` if the ID is unknown.

---

## Request and Response Schemas

The full schemas are documented at `/docs` (Swagger UI) and
`/openapi.json`. The headline shapes are summarized here for quick
reference; the wire format matches
`frontend/src/types/analysis.ts` field-for-field.

### AnalysisResult

The primary response from `POST /analyze` and `GET /analyses/{id}`.

| Field                    | Type                              | Notes                                     |
| ------------------------ | --------------------------------- | ----------------------------------------- |
| `analysis_id`            | string                            | 12-character hex identifier               |
| `input_type`             | `"video" \| "image"`              |                                           |
| `filename`               | string                            | Original upload filename                  |
| `filesize`               | integer                           | Bytes                                     |
| `verdict`                | string                            | Human-readable label                      |
| `confidence_score`       | float                             | Average fake probability across frames    |
| `risk_level`             | `"likely_real" \| "uncertain" \| "likely_fake"` | Derived from `confidence_score` |
| `summary_text`           | string                            | One-line natural-language summary         |
| `flagged_frame_indices`  | integer[]                         | Frames with `fake_probability >= 0.65`    |
| `frame_stats`            | object                            | Counts and average; see below             |
| `evidence_paths`         | `EvidenceAsset[]`                 | UI hints for evidence panels              |

| Field                    | Type                              | Notes                                     |
| ------------------------ | --------------------------------- | ----------------------------------------- |
| `created_at`             | string (ISO 8601 UTC)             |                                           |
| `model_used`             | string                            | The model key that was requested          |
| `media_metadata`         | `MediaMetadata`                   | Filename, size, dimensions, fps, etc.     |
| `frame_results`          | `FrameResult[]`                   | Per-frame probabilities and risk labels   |
| `warnings`               | string[]                          | Non-fatal issues (e.g. checkpoint missing)|
| `report_payload`         | object                            | Supplementary data used by the report     |

### Risk classification

Thresholds defined in `ui_mvp/config.py`:

- `confidence_score <= 0.35` → `likely_real`
- `0.35 < confidence_score <= 0.74` → `uncertain`
- `confidence_score > 0.74` → `likely_fake`

These bands apply both to overall verdict and to per-frame risk labels.

### HistoryRecord

The lightweight summary returned by `GET /analyses`.

| Field              | Type     |
| ------------------ | -------- |
| `analysis_id`      | string   |
| `created_at`       | string   |
| `filename`         | string   |
| `filesize`         | integer  |
| `input_type`       | string   |
| `model_used`       | string   |

| Field              | Type     |
| ------------------ | -------- |
| `verdict`          | string   |
| `confidence_score` | float    |
| `risk_level`       | string   |
| `summary_text`     | string   |
| `report_path`      | string \| null |

---

## Frontend Integration

The response shape of `POST /analyze` matches the `AnalysisResult` type
already declared in `frontend/src/types/analysis.ts`. No transformation
layer is required.

### Example: uploading and rendering a result

```ts
import type { AnalysisResult } from "./types/analysis";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000/api/v1";

async function analyze(file: File, model: string): Promise<AnalysisResult> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("model", model);

  const res = await fetch(`${API_BASE}/analyze`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const { detail } = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(`Analysis failed: ${detail}`);
  }
  return res.json() as Promise<AnalysisResult>;
}
```

### Example: listing past analyses

```ts
import type { HistoryRecord } from "./types/analysis";

async function listAnalyses(limit?: number): Promise<HistoryRecord[]> {
  const url = new URL(`${API_BASE}/analyses`);
  if (limit) url.searchParams.set("limit", String(limit));
  const res = await fetch(url);
  return res.json();
}
```

### Example: downloading a report

```ts
function reportUrl(analysisId: string, format: "html" | "json" = "html") {
  return `${API_BASE}/analyses/${analysisId}/report?format=${format}`;
}

// Trigger a browser download
window.location.href = reportUrl(analysisId);
```

### CORS

The dev server allows origins from environment variable `API_CORS_ORIGINS`
(comma-separated). Defaults:

- `http://localhost:5173` — Vite dev server
- `http://127.0.0.1:5173` — same, alternate host
- `http://localhost:6006` — Storybook

To add another origin, set the env var before starting uvicorn:

```bash
export API_CORS_ORIGINS="http://localhost:5173,http://localhost:3000"
uvicorn api.main:app --reload --port 8000
```

---

## Configuration

All settings are environment variables read at startup. Defaults are
defined in `api/deps.py`.

| Variable                  | Default                                                                | Purpose                                            |
| ------------------------- | ---------------------------------------------------------------------- | -------------------------------------------------- |
| `API_PREFIX`              | `/api/v1`                                                              | Path prefix mounted in front of every route        |
| `API_CORS_ORIGINS`        | `http://localhost:5173,http://127.0.0.1:5173,http://localhost:6006`    | Comma-separated allowed origins                    |
| `API_MAX_UPLOAD_MB`       | `200`                                                                  | Max upload size before rejection                   |
| `CHECKPOINT_EFFICIENTB0`  | `best_corrected_model.pt`                                              | Checkpoint for EFFICIENTB0 (resolved from repo root)|
| `CHECKPOINT_MESO4`        | (unset)                                                                | Checkpoint for MESO4                               |
| `CHECKPOINT_MESOINCEPTION4` | (unset)                                                              | Checkpoint for MESOINCEPTION4                      |
| `CHECKPOINT_XCEPTION`     | (unset)                                                                | Checkpoint for XCEPTION                            |

Checkpoint paths may be absolute or relative to the repo root.

---

## Model Checkpoints

The four supported models are listed by `GET /api/v1/models` and the
`MODEL_OPTIONS` dictionary in `ui_mvp/config.py`. Each model needs a
matching `.pt` weights file to produce real scores.

### Resolution order

For each `model` value, the checkpoint is resolved in this order:

1. Env var `CHECKPOINT_<MODEL_KEY>` if set (absolute or relative to repo root)
2. Default mapping in `api/deps.py` (only `EFFICIENTB0` has a default today)
3. None — the analysis still runs in metadata-only mode and returns a
   warning in the response, with placeholder probabilities of `0.5`

### Wiring up additional models

Drop the `.pt` file somewhere readable and set the env var before
starting the server:

```bash
export CHECKPOINT_MESO4=/abs/path/to/meso4.pt
export CHECKPOINT_XCEPTION=./checkpoints/xception.pt
uvicorn api.main:app --reload --port 8000
```

No code change required.

### Behavior when a checkpoint is missing

`POST /analyze` still returns `200`. The result contains:

- A `warnings` array including a message like `"No compatible checkpoint
  was supplied..."`
- A `verdict` of `"Needs configured model checkpoint"`
- `confidence_score` of `0.5` and `risk_level` of `"uncertain"`
- Placeholder `frame_results` with neutral probabilities

This is intentional: the API stays usable for frontend development
before all weights are in place.

---

## Troubleshooting

### `Address already in use` on port 8000

Another process is holding the port — usually a previous uvicorn worker
that survived `Ctrl-C` because of `--reload`. Either kill it or pick a
different port:

```bash
lsof -ti:8000 | xargs kill -9
# or
uvicorn api.main:app --reload --port 8001
```

If you change the port, update the frontend's API base URL accordingly.

### `ModuleNotFoundError: No module named 'numpy'` (or `torch`, `cv2`, etc.)

The inference dependencies are not installed in the active environment.
Verify your venv is activated, then:

```bash
pip install -r requirements-inference.txt
```

### `facenet-pytorch` (or `librosa`, `moviepy`) fails to install

These are optional, used only by the legacy `detect_video.py` CLI. The
API itself does not need them. Comment out the failing line in
`requirements-inference.txt` and re-run `pip install`.

### Analysis returns placeholder scores with a "checkpoint" warning

The chosen model has no checkpoint wired up. See
[Model Checkpoints](#model-checkpoints) above.

### Analysis takes too long / times out

The current pipeline is synchronous and CPU-bound for non-GPU machines.
Long videos (60+ seconds, many sampled frames) can take 30 seconds or
more. Options:

- Reduce `sample_frames` in the request (down to 1 if needed)
- Run on a machine with CUDA available
- Add an async/job-based variant of the endpoint (not implemented in v1)

### CORS errors in the browser console

The frontend's origin is not in the allowed list. Add it via
`API_CORS_ORIGINS` (see [Configuration](#configuration)) and restart the
server.

### Reloader prints "Uvicorn running" but never "Application startup complete"

The worker process crashed during import. Stop the server and re-run
without `--reload` to surface the underlying error:

```bash
uvicorn api.main:app --port 8000
```

The traceback will identify the missing module or misconfiguration.

### Where do uploaded files live?

Each upload is written to a system temp file
(`tempfile.NamedTemporaryFile`) for the duration of one request, then
deleted in a `finally` block. The repository does not retain raw upload
bytes. Only the derived `AnalysisResult` is persisted to
`.ui_mvp_data/`.
