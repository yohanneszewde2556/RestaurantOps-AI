"""
Analytics API Router
Provides endpoints for ingredient consumption velocity, popular menu items,
and recipe food-cost profitability analytics.
"""

from datetime import date, datetime, time, timezone
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ValidationException
from app.core.responses import ok
from app.database.session import get_db
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


def _parse_query_datetime(val: Optional[str], is_end: bool = False) -> Optional[datetime]:
    """Parse query date string supporting ISO 8601, timezone offsets, and YYYY-MM-DD."""
    if not val:
        return None
    val = val.strip().replace(" ", "+")
    try:
        dt = datetime.fromisoformat(val)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        try:
            d = date.fromisoformat(val)
            t = time.max if is_end else time.min
            return datetime.combine(d, t, tzinfo=timezone.utc)
        except ValueError:
            raise ValidationException(f"Invalid date format: '{val}'. Expected ISO-8601 or YYYY-MM-DD.")


@router.get(
    "/consumption",
    summary="Get ingredient consumption analytics and timeline trends",
)
async def get_consumption_analytics(
    start_date: Optional[str] = Query(None, description="Start date filter (ISO or YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date filter (ISO or YYYY-MM-DD)"),
    limit: int = Query(10, ge=1, le=100, description="Max top consumed ingredients to return"),
    session: AsyncSession = Depends(get_db),
):
    """
    Returns ingredient consumption analytics:
      - Period summary (today, last 7 days, last 30 days)
      - Top consumed ingredients by volume and cost
      - Chronological daily consumption trend buckets
    """
    start_dt = _parse_query_datetime(start_date, is_end=False)
    end_dt = _parse_query_datetime(end_date, is_end=True)

    data = await AnalyticsService.get_consumption_analytics(
        session=session,
        start_date=start_dt,
        end_date=end_dt,
        limit=limit,
    )
    return ok(data=data.model_dump())


@router.get(
    "/popular-items",
    summary="Get best-selling menu items and revenue contributions",
)
async def get_popular_items(
    start_date: Optional[str] = Query(None, description="Start date filter (ISO or YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date filter (ISO or YYYY-MM-DD)"),
    limit: int = Query(10, ge=1, le=50, description="Max items to return"),
    session: AsyncSession = Depends(get_db),
):
    """
    Returns menu item sales rankings:
      - Quantity sold per item
      - Revenue generated and revenue contribution percentage
      - Unique order transaction frequency
    """
    start_dt = _parse_query_datetime(start_date, is_end=False)
    end_dt = _parse_query_datetime(end_date, is_end=True)

    data = await AnalyticsService.get_popular_items(
        session=session,
        start_date=start_dt,
        end_date=end_dt,
        limit=limit,
    )
    return ok(data=data.model_dump())


@router.get(
    "/food-cost",
    summary="Get recipe food cost, margins, and profitability breakdown",
)
async def get_food_cost_analytics(
    session: AsyncSession = Depends(get_db),
):
    """
    Returns recipe cost and margin profitability metrics:
      - Calculated ingredient costs per dish
      - Food cost percentage against current selling price
      - Gross dollar contribution and margin percentage
      - Identifies items without recipes safely
    """
    data = await AnalyticsService.get_food_cost_analytics(session=session)
    return ok(data=data.model_dump())
