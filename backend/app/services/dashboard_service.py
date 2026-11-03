"""
Dashboard Service
Calculates real-time operational statistics and KPIs directly from database tables.
"""

from datetime import datetime, time, timedelta, timezone
from decimal import Decimal
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ingredient import Ingredient
from app.models.inventory_transaction import InventoryTransaction
from app.models.menu_item import MenuItem
from app.models.sale import Sale


class DashboardService:

    @staticmethod
    async def get_summary(session: AsyncSession) -> dict:
        """
        Aggregate operational statistics across inventory, sales, and menu items.
        Returns live metrics without hardcoding.
        """
        now = datetime.now(timezone.utc)
        today_date = now.date()
        today_start = datetime.combine(today_date, time.min, tzinfo=timezone.utc)
        expiring_threshold_date = today_date + timedelta(days=7)

        # 1. Total ingredients
        total_ing_res = await session.execute(select(func.count(Ingredient.id)))
        total_ingredients = total_ing_res.scalar_one() or 0

        # 2. Total active menu items
        active_items_res = await session.execute(
            select(func.count(MenuItem.id)).where(MenuItem.is_active.is_(True))
        )
        total_active_menu_items = active_items_res.scalar_one() or 0

        # 3. Total estimated inventory value (sum of current_quantity * cost_per_unit)
        value_res = await session.execute(
            select(func.coalesce(func.sum(Ingredient.current_quantity * Ingredient.cost_per_unit), 0))
        )
        total_inventory_value = Decimal(str(value_res.scalar_one() or 0))

        # 4. Low stock count (current_quantity <= min_quantity)
        low_stock_res = await session.execute(
            select(func.count(Ingredient.id)).where(Ingredient.current_quantity <= Ingredient.min_quantity)
        )
        low_stock_count = low_stock_res.scalar_one() or 0

        # 5. Expiring soon count (within next 7 days)
        expiring_res = await session.execute(
            select(func.count(Ingredient.id)).where(
                Ingredient.expiry_date.is_not(None),
                Ingredient.expiry_date <= expiring_threshold_date,
            )
        )
        expiring_soon_count = expiring_res.scalar_one() or 0

        # 6. Today sales revenue and count
        today_sales_stmt = select(
            func.coalesce(func.sum(Sale.total_amount), 0),
            func.count(Sale.id),
        ).where(Sale.sold_at >= today_start)
        today_sales_row = (await session.execute(today_sales_stmt)).one()
        today_sales_revenue = Decimal(str(today_sales_row[0]))
        today_sales_count = today_sales_row[1] or 0

        # 7. Recent 5 inventory transactions
        recent_tx_stmt = (
            select(InventoryTransaction)
            .order_by(InventoryTransaction.created_at.desc(), InventoryTransaction.id.desc())
            .limit(5)
        )
        recent_transactions = list((await session.execute(recent_tx_stmt)).scalars().all())

        # 8. Recent 5 sales
        recent_sales_stmt = (
            select(Sale)
            .order_by(Sale.sold_at.desc(), Sale.id.desc())
            .limit(5)
        )
        recent_sales = list((await session.execute(recent_sales_stmt)).scalars().all())

        return {
            "total_ingredients": total_ingredients,
            "total_active_menu_items": total_active_menu_items,
            "total_inventory_value": total_inventory_value,
            "low_stock_count": low_stock_count,
            "expiring_soon_count": expiring_soon_count,
            "today_sales_revenue": today_sales_revenue,
            "today_sales_count": today_sales_count,
            "recent_transactions": recent_transactions,
            "recent_sales": recent_sales,
        }
