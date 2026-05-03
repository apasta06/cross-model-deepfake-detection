from __future__ import annotations

import json
from pathlib import Path

from ui_mvp.schemas import AnalysisResult


def build_report_json(result: AnalysisResult) -> str:
    return json.dumps(result.to_dict(), indent=2)


def build_report_html(result: AnalysisResult) -> str:
    frame_rows = "".join(
        f"<tr><td>{frame.get('frame_index', '-')}</td><td>{frame.get('timestamp_label', '-')}</td>"
        f"<td>{frame.get('fake_probability', 0):.1%}</td><td>{frame.get('risk_label', '-')}</td></tr>"
        for frame in result.frame_results
    )
    warning_items = "".join(f"<li>{warning}</li>" for warning in result.warnings) or "<li>No warnings.</li>"
    evidence_items = "".join(
        f"<li><strong>{asset.label}</strong>: {asset.description}</li>" for asset in result.evidence_paths
    ) or "<li>No run-specific evidence assets were generated.</li>"

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Deepfake Analysis Report - {result.analysis_id}</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 32px; color: #111; }}
    .hero {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 24px; }}
    .card {{ border: 1px solid #ddd; border-radius: 12px; padding: 16px; }}
    h1, h2 {{ margin-bottom: 12px; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 12px; }}
    td, th {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
    th {{ background: #f5f5f5; }}
    .small {{ color: #555; font-size: 14px; }}
  </style>
</head>
<body>
  <h1>Deepfake Analysis Report</h1>
  <p class="small">Analysis ID: {result.analysis_id} | Generated: {result.created_at}</p>
  <div class="hero">
    <div class="card"><h2>Verdict</h2><p>{result.verdict}</p></div>
    <div class="card"><h2>Confidence</h2><p>{result.confidence_score:.1%}</p></div>
    <div class="card"><h2>Risk Level</h2><p>{result.risk_level}</p></div>
  </div>
  <div class="card">
    <h2>Summary</h2>
    <p>{result.summary_text}</p>
    <p class="small">Model: {result.model_used} | File: {result.filename} | Input type: {result.input_type}</p>
  </div>
  <div class="card">
    <h2>Media Metadata</h2>
    <p>Size: {result.filesize} bytes | Duration: {result.media_metadata.duration_seconds} | FPS: {result.media_metadata.fps}</p>
    <p>Resolution: {result.media_metadata.width} x {result.media_metadata.height}</p>
  </div>
  <div class="card">
    <h2>Evidence Notes</h2>
    <ul>{evidence_items}</ul>
  </div>
  <div class="card">
    <h2>Warnings</h2>
    <ul>{warning_items}</ul>
  </div>
  <div class="card">
    <h2>Frame Review</h2>
    <table>
      <thead><tr><th>Frame</th><th>Timestamp</th><th>Fake Probability</th><th>Risk</th></tr></thead>
      <tbody>{frame_rows}</tbody>
    </table>
  </div>
</body>
</html>"""


def suggested_report_name(result: AnalysisResult, suffix: str) -> str:
    safe_name = Path(result.filename).stem.replace(" ", "_")
    return f"{safe_name}_{result.analysis_id}.{suffix}"
