"""
Sales API Router
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.responses import ok
from app.database.session import get_db
from app.schemas.common import PaginatedResponse
from app.schemas.sale import SaleCreate, SaleResponse
from app.services.sales_service import SalesService

router = APIRouter(prefix="/sales", tags=["Sales"])


@router.get(
    "",
    summary="List sales with pagination and optional date filters",
)
async def list_sales(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    start_date: Optional[datetime] = Query(None, description="Start date filter (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date filter (ISO format)"),
    session: AsyncSession = Depends(get_db),
):
    items, total, pages = await SalesService.list_sales(
        session=session,
        page=page,
        page_size=page_size,
        start_date=start_date,
        end_date=end_date,
    )
    payload = PaginatedResponse[SaleResponse](
        items=[SaleResponse.model_validate(sale) for sale in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )
    return ok(data=payload.model_dump())


@router.get(
    "/{sale_id}",
    summary="Get single sale by ID with sold items",
)
async def get_sale(
    sale_id: int,
    session: AsyncSession = Depends(get_db),
):
    sale = await SalesService.get_by_id(session, sale_id)
    return ok(data=SaleResponse.model_validate(sale).model_dump())


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Record a sale and atomically deduct ingredient inventory",
)
async def record_sale(
    data: SaleCreate,
    session: AsyncSession = Depends(get_db),
):
    sale = await SalesService.record_sale(session, data)
    return ok(
        data=SaleResponse.model_validate(sale).model_dump(),
        message="Sale recorded and inventory depleted successfully",
    )
