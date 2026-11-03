"""
Dashboard API Router
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.responses import ok
from app.database.session import get_db
from app.schemas.dashboard import DashboardSummaryResponse
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get(
    "/summary",
    summary="Get real-time operational dashboard summary metrics",
)
async def get_dashboard_summary(
    session: AsyncSession = Depends(get_db),
):
    summary_data = await DashboardService.get_summary(session)
    payload = DashboardSummaryResponse.model_validate(summary_data)
    return ok(data=payload.model_dump())
