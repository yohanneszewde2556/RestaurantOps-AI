"""
Inventory Service
Handles inventory transactions, manual adjustments, low-stock monitoring,
and expiration tracking.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import math
from typing import List, Optional, Tuple
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, ValidationException
from app.models.ingredient import Ingredient
from app.models.inventory_transaction import InventoryTransaction
from app.schemas.inventory_transaction import InventoryAdjustmentCreate


class InventoryService:

    @staticmethod
    async def list_transactions(
        session: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        ingredient_id: Optional[int] = None,
        transaction_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Tuple[list[InventoryTransaction], int, int]:
        """List inventory transactions with pagination and optional filters."""
        stmt = select(InventoryTransaction)

        if ingredient_id:
            stmt = stmt.where(InventoryTransaction.ingredient_id == ingredient_id)
        if transaction_type:
            stmt = stmt.where(InventoryTransaction.transaction_type == transaction_type.upper())
        if start_date:
            stmt = stmt.where(InventoryTransaction.created_at >= start_date)
        if end_date:
            stmt = stmt.where(InventoryTransaction.created_at <= end_date)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await session.execute(count_stmt)).scalar_one()

        pages = max(1, math.ceil(total / page_size)) if total > 0 else 1
        offset = (page - 1) * page_size

        stmt = (
            stmt.order_by(InventoryTransaction.created_at.desc(), InventoryTransaction.id.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await session.execute(stmt)
        items = list(result.scalars().all())

        return items, total, pages

    @staticmethod
    async def adjust_stock(
        session: AsyncSession, data: InventoryAdjustmentCreate
    ) -> InventoryTransaction:
        """
        Record a manual stock adjustment (purchase intake, cycle count correction, or waste).
        Ensures resulting ingredient quantity cannot become negative.
        """
        ing_stmt = select(Ingredient).where(Ingredient.id == data.ingredient_id)
        ingredient = (await session.execute(ing_stmt)).scalar_one_or_none()
        if not ingredient:
            raise NotFoundException("Ingredient", data.ingredient_id)

        new_quantity = ingredient.current_quantity + data.quantity
        if new_quantity < Decimal("0.000"):
            raise ValidationException(
                f"Adjustment of {data.quantity} {ingredient.unit} would result in negative stock "
                f"({new_quantity} {ingredient.unit}). Current stock is {ingredient.current_quantity} {ingredient.unit}."
            )

        ingredient.current_quantity = new_quantity

        tx = InventoryTransaction(
            ingredient_id=ingredient.id,
            transaction_type=data.transaction_type.value,
            quantity=data.quantity,
            notes=data.notes,
            created_at=datetime.now(timezone.utc),
        )
        session.add(tx)
        await session.commit()
        await session.refresh(tx)
        return tx

    @staticmethod
    async def get_low_stock(session: AsyncSession) -> List[Ingredient]:
        """Retrieve all ingredients currently at or below their minimum quantity threshold."""
        stmt = (
            select(Ingredient)
            .where(Ingredient.current_quantity <= Ingredient.min_quantity)
            .order_by((Ingredient.current_quantity - Ingredient.min_quantity).asc())
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_expiring(session: AsyncSession, days: int = 7) -> List[Ingredient]:
        """Retrieve ingredients whose expiration date falls on or before the threshold date."""
        if days < 0:
            raise ValidationException("Threshold days must be a non-negative integer.")

        target_date = datetime.now(timezone.utc).date() + timedelta(days=days)
        stmt = (
            select(Ingredient)
            .where(
                Ingredient.expiry_date.is_not(None),
                Ingredient.expiry_date <= target_date,
            )
            .order_by(Ingredient.expiry_date.asc())
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())
