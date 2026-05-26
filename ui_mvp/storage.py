from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from ui_mvp.config import DATA_DIR, HISTORY_FILE, REPORTS_DIR
from ui_mvp.schemas import HistoryRecord


def ensure_data_dirs() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    REPORTS_DIR.mkdir(exist_ok=True)


def append_history(record: HistoryRecord) -> None:
    ensure_data_dirs()
    with HISTORY_FILE.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record.to_dict()) + "\n")


def load_history(limit: Optional[int] = None) -> List[dict]:
    if not HISTORY_FILE.exists():
        return []
    items = []
    with HISTORY_FILE.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            items.append(json.loads(line))
    items.sort(key=lambda item: item.get("created_at", ""), reverse=True)
    if limit is not None:
        return items[:limit]
    return items


def update_report_path(analysis_id: str, report_path: str) -> None:
    items = load_history()
    changed = False
    for item in items:
        if item.get("analysis_id") == analysis_id:
            item["report_path"] = report_path
            changed = True
            break
    if not changed:
        return
    ensure_data_dirs()
    with HISTORY_FILE.open("w", encoding="utf-8") as handle:
        for item in items:
            handle.write(json.dumps(item) + "\n")


def write_report_file(filename: str, content: str) -> Path:
    ensure_data_dirs()
    target = REPORTS_DIR / filename
    target.write_text(content, encoding="utf-8")
    return target

