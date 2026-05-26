from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / ".ui_mvp_data"
REPORTS_DIR = DATA_DIR / "reports"
HISTORY_FILE = DATA_DIR / "history.jsonl"

SUPPORTED_VIDEO_FORMATS = (".mp4", ".avi", ".mov", ".mkv", ".mts", ".webm")
SUPPORTED_IMAGE_FORMATS = (".jpg", ".jpeg", ".png", ".bmp")
SUPPORTED_INPUT_FORMATS = SUPPORTED_VIDEO_FORMATS + SUPPORTED_IMAGE_FORMATS
MAX_UPLOAD_SIZE_MB = 200
DEFAULT_SAMPLE_FRAMES = 12

MODEL_OPTIONS = {
    "XCEPTION": "Frame-wise Xception classifier using a compatible checkpoint.",
    "MESO4": "Frame-wise Meso4 classifier using a compatible checkpoint.",
    "MESOINCEPTION4": "Frame-wise MesoInception4 classifier using a compatible checkpoint.",
    "EFFICIENTB0": "Frame-wise EfficientNet-B0 classifier using a compatible checkpoint.",
}

RETENTION_MESSAGE = (
    "Uploads are processed locally. Raw uploaded media is deleted after analysis. "
    "Only audit metadata is retained unless you export a report."
)

RISK_THRESHOLDS = {
    "real_max": 0.35,
    "uncertain_max": 0.74,
}

RISK_COLORS = {
    "likely_real": "#2E8B57",
    "uncertain": "#D98E04",
    "likely_fake": "#C0392B",
}

