"""Report download endpoint.

GET /analyses/{id}/report?format=html|json

The HTML and JSON builders already exist in ui_mvp/reporting.py; this
route only resolves the analysis from storage and returns the built
artifact with appropriate Content-Type and Content-Disposition headers.
"""
from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import Response

from ui_mvp.reporting import build_report_html, build_report_json, suggested_report_name
from ui_mvp.schemas import AnalysisResult, EvidenceAsset, MediaMetadata
from ui_mvp.storage import load_full_result

router = APIRouter(tags=["reports"])


def _rehydrate(payload: dict) -> AnalysisResult:
    """Rebuild the AnalysisResult dataclass from the stored JSON dict."""
    media = MediaMetadata(**payload["media_metadata"])
    evidence = [EvidenceAsset(**asset) for asset in payload.get("evidence_paths", [])]
    kwargs = {**payload, "media_metadata": media, "evidence_paths": evidence}
    return AnalysisResult(**kwargs)


@router.get(
    "/analyses/{analysis_id}/report",
    responses={
        200: {"description": "Report content; content-type depends on format."},
        404: {"description": "Analysis not found."},
    },
    summary="Download a report for a past analysis (HTML or JSON).",
)
def get_report(
    analysis_id: str,
    format: Literal["html", "json"] = Query(
        "html",
        description="Report format. 'html' for a styled standalone document, 'json' for the raw result.",
    ),
) -> Response:
    payload = load_full_result(analysis_id)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No analysis found for id '{analysis_id}'.",
        )

    result = _rehydrate(payload)

    if format == "json":
        content = build_report_json(result)
        media_type = "application/json"
        filename = suggested_report_name(result, "json")
    else:
        content = build_report_html(result)
        media_type = "text/html"
        filename = suggested_report_name(result, "html")

    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
