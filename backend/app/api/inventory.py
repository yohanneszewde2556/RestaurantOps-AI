"""
Inventory & Adjustments API Router
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.responses import ok
from app.database.session import get_db
from app.schemas.common import PaginatedResponse
from app.schemas.ingredient import IngredientResponse
from app.schemas.inventory_transaction import (
    InventoryAdjustmentCreate,
    InventoryTransactionResponse,
)
from app.services.inventory_service import InventoryService

router = APIRouter(prefix="/inventory", tags=["Inventory"])


@router.get(
    "/transactions",
    summary="List inventory audit transactions with pagination and filters",
)
async def list_transactions(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    ingredient_id: Optional[int] = Query(None, description="Filter by ingredient ID"),
    transaction_type: Optional[str] = Query(None, description="Filter by type (PURCHASE, SALE_CONSUMPTION, ADJUSTMENT, WASTE)"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    session: AsyncSession = Depends(get_db),
):
    items, total, pages = await InventoryService.list_transactions(
        session=session,
        page=page,
        page_size=page_size,
        ingredient_id=ingredient_id,
        transaction_type=transaction_type,
        start_date=start_date,
        end_date=end_date,
    )
    payload = PaginatedResponse[InventoryTransactionResponse](
        items=[InventoryTransactionResponse.model_validate(t) for t in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )
    return ok(data=payload.model_dump())


@router.post(
    "/adjustments",
    status_code=status.HTTP_201_CREATED,
    summary="Record a manual inventory adjustment (purchase, correction, or waste)",
)
async def adjust_inventory(
    data: InventoryAdjustmentCreate,
    session: AsyncSession = Depends(get_db),
):
    tx = await InventoryService.adjust_stock(session, data)
    return ok(
        data=InventoryTransactionResponse.model_validate(tx).model_dump(),
        message="Inventory adjusted successfully",
    )


@router.get(
    "/low-stock",
    summary="Get ingredients at or below their minimum reorder threshold",
)
async def get_low_stock(
    session: AsyncSession = Depends(get_db),
):
    low_stock_items = await InventoryService.get_low_stock(session)
    payload = [IngredientResponse.model_validate(i).model_dump() for i in low_stock_items]
    return ok(data=payload)


@router.get(
    "/expiring",
    summary="Get ingredients expiring within the specified number of days",
)
async def get_expiring(
    days: int = Query(7, ge=0, description="Expiration threshold horizon in days"),
    session: AsyncSession = Depends(get_db),
):
    expiring_items = await InventoryService.get_expiring(session, days=days)
    payload = [IngredientResponse.model_validate(i).model_dump() for i in expiring_items]
    return ok(data=payload)
