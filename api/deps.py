"""Runtime settings and checkpoint resolution for the FastAPI service.

All configuration is overridable via environment variables so the
service can be reconfigured without code changes (e.g. when deployed
in a container).
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Dict, Optional

from ui_mvp.config import BASE_DIR, MAX_UPLOAD_SIZE_MB, MODEL_OPTIONS


# --- Settings ------------------------------------------------------------

@dataclass(frozen=True)
class Settings:
    base_dir: Path
    max_upload_size_mb: int
    cors_origins: tuple
    api_prefix: str

    @classmethod
    def from_env(cls) -> "Settings":
        origins_raw = os.getenv(
            "API_CORS_ORIGINS",
            # Vite dev server + common alternates.
            "http://localhost:5173,http://127.0.0.1:5173,http://localhost:6006",
        )
        origins = tuple(o.strip() for o in origins_raw.split(",") if o.strip())
        return cls(
            base_dir=BASE_DIR,
            max_upload_size_mb=int(
                os.getenv("API_MAX_UPLOAD_MB", str(MAX_UPLOAD_SIZE_MB))
            ),
            cors_origins=origins,
            api_prefix=os.getenv("API_PREFIX", "/api/v1"),
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings.from_env()


# --- Checkpoint resolution -----------------------------------------------

# Default checkpoint filenames searched at the repo root, per model.
# Override per model with env vars like CHECKPOINT_MESO4=/abs/path/to.pt.
_DEFAULT_CHECKPOINTS: Dict[str, str] = {
    "EFFICIENTB0": "best_corrected_model.pt",
    "MESO4": "",
    "MESOINCEPTION4": "",
    "XCEPTION": "",
}


def resolve_checkpoint(model_key: str) -> Optional[Path]:
    """Return the checkpoint path for a model, or None if unavailable.

    Resolution order:
      1. Env var CHECKPOINT_<MODEL_KEY> (absolute or relative to base_dir)
      2. _DEFAULT_CHECKPOINTS mapping (relative to base_dir)
      3. None — analysis falls back to metadata-only mode with a warning.
    """
    if model_key not in MODEL_OPTIONS:
        return None

    env_value = os.getenv(f"CHECKPOINT_{model_key}")
    candidate: Optional[Path] = None

    if env_value:
        candidate = Path(env_value)
        if not candidate.is_absolute():
            candidate = get_settings().base_dir / candidate
    else:
        default_name = _DEFAULT_CHECKPOINTS.get(model_key, "")
        if default_name:
            candidate = get_settings().base_dir / default_name

    if candidate and candidate.exists():
        return candidate
    return None
