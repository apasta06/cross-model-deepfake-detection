"""History endpoints: list past analyses and fetch a single past result.

GET /analyses          → list of HistoryRecord (summary view)
GET /analyses/{id}     → full AnalysisResult (detail view)
"""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, status

from api.models import AnalysisResult as AnalysisResultModel
from api.models import HistoryRecord as HistoryRecordModel
from ui_mvp.storage import load_full_result, load_history

router = APIRouter(tags=["history"])


@router.get(
    "/analyses",
    response_model=List[HistoryRecordModel],
    summary="List past analyses (newest first).",
)
def list_analyses(
    limit: Optional[int] = Query(
        None,
        ge=1,
        le=500,
        description="Maximum number of records to return. Omit for all.",
    ),
) -> List[HistoryRecordModel]:
    records = load_history(limit=limit)
    return [HistoryRecordModel.model_validate(record) for record in records]


@router.get(
    "/analyses/{analysis_id}",
    response_model=AnalysisResultModel,
    responses={404: {"description": "Analysis not found."}},
    summary="Fetch the full AnalysisResult for a past analysis.",
)
def get_analysis(analysis_id: str) -> AnalysisResultModel:
    payload = load_full_result(analysis_id)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No analysis found for id '{analysis_id}'.",
        )
    return AnalysisResultModel.model_validate(payload)
