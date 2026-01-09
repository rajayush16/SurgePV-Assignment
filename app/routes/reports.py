from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import LatencyResponse, TopAssigneesResponse
from app.services.reports import average_latency, top_assignees


router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/top-assignees", response_model=TopAssigneesResponse)
def report_top_assignees(limit: int = 10, db: Session = Depends(get_db)) -> TopAssigneesResponse:
    items = top_assignees(db, limit)
    return TopAssigneesResponse(items=items)


@router.get("/latency", response_model=LatencyResponse)
def report_latency(db: Session = Depends(get_db)) -> LatencyResponse:
    return LatencyResponse(**average_latency(db))
