"""
Procurement Service
Generates, tracks, and manages procurement recommendations with human approval gates.
"""

from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
import math
from typing import List, Optional, Tuple
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundException, ValidationException
from app.models.ingredient import Ingredient
from app.models.procurement import (
    ProcurementRecommendation,
    ProcurementRecommendationItem,
    RecommendationStatus,
)


def _round_decimal(val: Decimal, places: int = 2) -> Decimal:
    q = Decimal("10") ** -places
    return val.quantize(q, rounding=ROUND_HALF_UP)


class ProcurementService:

    @staticmethod
    async def generate_recommendations(
        session: AsyncSession,
        reason: str = "Automated AI inventory restock assessment",
        force_all_low: bool = False,
    ) -> ProcurementRecommendation:
        """
        Evaluate pantry stock levels and generate a deterministic procurement recommendation:
          - Target ingredients at or below min_quantity threshold.
          - Recommended quantity: Q = max((2 * min_quantity) - current_quantity, min_quantity)
          - Saves recommendation strictly in PENDING status.
          - Never executes automated external purchases.
        """
        # Query ingredients at or below min_quantity
        stmt = (
            select(Ingredient)
            .where(Ingredient.current_quantity <= Ingredient.min_quantity)
            .order_by((Ingredient.current_quantity / func.nullif(Ingredient.min_quantity, 0)).asc())
        )
        low_stock_ingredients = list((await session.execute(stmt)).scalars().all())

        # If pantry has no items strictly <= min_quantity, check items with less than 1.5x min_quantity
        if not low_stock_ingredients and not force_all_low:
            alt_stmt = (
                select(Ingredient)
                .where(Ingredient.current_quantity <= (Ingredient.min_quantity * Decimal("1.500")))
                .order_by((Ingredient.current_quantity / func.nullif(Ingredient.min_quantity, 0)).asc())
                .limit(5)
            )
            low_stock_ingredients = list((await session.execute(alt_stmt)).scalars().all())

        total_cost = Decimal("0.00")
        items_to_create: List[ProcurementRecommendationItem] = []

        for ing in low_stock_ingredients:
            # Deterministic restock quantity calculation
            raw_qty = (ing.min_quantity * Decimal("2.000")) - ing.current_quantity
            recommended_qty = max(raw_qty, ing.min_quantity)
            # Ensure at least 1 unit if min_quantity is somehow 0
            if recommended_qty <= Decimal("0.000"):
                recommended_qty = Decimal("1.000")

            recommended_qty = _round_decimal(recommended_qty, 3)
            unit_cost = _round_decimal(ing.cost_per_unit, 2)
            item_total = _round_decimal(recommended_qty * unit_cost, 2)
            total_cost += item_total

            item = ProcurementRecommendationItem(
                ingredient_id=ing.id,
                recommended_quantity=recommended_qty,
                estimated_unit_cost=unit_cost,
                estimated_total_cost=item_total,
            )
            items_to_create.append(item)

        rec = ProcurementRecommendation(
            status=RecommendationStatus.PENDING.value,
            total_estimated_cost=_round_decimal(total_cost, 2),
            reason=reason if items_to_create else "Pantry stocks are currently optimal; no urgent procurement required.",
            created_at=datetime.now(timezone.utc),
        )
        session.add(rec)
        await session.flush()

        for item in items_to_create:
            item.recommendation_id = rec.id
            session.add(item)

        await session.commit()
        await session.refresh(rec)
        return rec

    @staticmethod
    async def list_recommendations(
        session: AsyncSession,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[ProcurementRecommendation], int, int]:
        """List procurement recommendations with pagination and status filtering."""
        stmt = select(ProcurementRecommendation).options(
            selectinload(ProcurementRecommendation.items).selectinload(ProcurementRecommendationItem.ingredient)
        )
        if status:
            stmt = stmt.where(ProcurementRecommendation.status == status.upper())

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await session.execute(count_stmt)).scalar_one()

        pages = max(1, math.ceil(total / page_size)) if total > 0 else 1
        offset = (page - 1) * page_size
        stmt = stmt.order_by(ProcurementRecommendation.created_at.desc()).offset(offset).limit(page_size)

        items = list((await session.execute(stmt)).scalars().all())
        return items, total, pages

    @staticmethod
    async def get_by_id(session: AsyncSession, rec_id: int) -> ProcurementRecommendation:
        """Fetch single procurement recommendation by ID with items and ingredients."""
        stmt = (
            select(ProcurementRecommendation)
            .options(
                selectinload(ProcurementRecommendation.items).selectinload(ProcurementRecommendationItem.ingredient)
            )
            .where(ProcurementRecommendation.id == rec_id)
        )
        rec = (await session.execute(stmt)).scalar_one_or_none()
        if not rec:
            raise NotFoundException("ProcurementRecommendation", rec_id)
        return rec

    @staticmethod
    async def approve_recommendation(session: AsyncSession, rec_id: int) -> ProcurementRecommendation:
        """Manager approves procurement recommendation. AI is prohibited from calling this directly."""
        rec = await ProcurementService.get_by_id(session, rec_id)
        if rec.status != RecommendationStatus.PENDING.value:
            raise ValidationException(f"Cannot approve recommendation in status '{rec.status}'.")

        rec.status = RecommendationStatus.APPROVED.value
        rec.reviewed_at = datetime.now(timezone.utc)
        await session.commit()
        await session.refresh(rec)
        return rec

    @staticmethod
    async def reject_recommendation(
        session: AsyncSession, rec_id: int, reason: Optional[str] = None
    ) -> ProcurementRecommendation:
        """Manager rejects procurement recommendation. AI is prohibited from calling this directly."""
        rec = await ProcurementService.get_by_id(session, rec_id)
        if rec.status != RecommendationStatus.PENDING.value:
            raise ValidationException(f"Cannot reject recommendation in status '{rec.status}'.")

        rec.status = RecommendationStatus.REJECTED.value
        rec.reviewed_at = datetime.now(timezone.utc)
        if reason:
            rec.reason = f"{rec.reason} [Rejection note: {reason}]"
        await session.commit()
        await session.refresh(rec)
        return rec
