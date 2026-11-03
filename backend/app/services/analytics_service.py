"""
Analytics Service
Computes ingredient consumption velocity, popular menu item rankings,
and recipe food-cost profitability metrics using real database records.
"""

from collections import defaultdict
from datetime import datetime, time, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.ingredient import Ingredient
from app.models.inventory_transaction import InventoryTransaction, TransactionType
from app.models.menu_item import MenuItem
from app.models.recipe import RecipeIngredient
from app.models.sale import Sale, SaleItem
from app.schemas.analytics import (
    ConsumptionAnalyticsResponse,
    DailyConsumptionTrend,
    DailyIngredientConsumption,
    FoodCostAnalyticsResponse,
    MenuItemFoodCost,
    PeriodConsumptionSummary,
    PopularItemsResponse,
    PopularMenuItem,
    RecipeCostItem,
    TopConsumedIngredient,
)


def _round_decimal(val: Decimal, places: int = 2) -> Decimal:
    """Helper to round Decimal to fixed decimal places safely."""
    q = Decimal("10") ** -places
    return val.quantize(q, rounding=ROUND_HALF_UP)


class AnalyticsService:

    @staticmethod
    async def get_consumption_analytics(
        session: AsyncSession,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 10,
    ) -> ConsumptionAnalyticsResponse:
        """
        Analyze ingredient consumption:
          - Aggregate consumption for today, last 7 days, and last 30 days.
          - Identify top consumed ingredients within the date range.
          - Calculate daily consumption velocity and chronological trends.
        """
        now = datetime.now(timezone.utc)
        today_start = datetime.combine(now.date(), time.min, tzinfo=timezone.utc)
        seven_days_ago = now - timedelta(days=7)
        thirty_days_ago = now - timedelta(days=30)

        # 1. Period totals across all ingredients
        # Today
        today_stmt = select(func.coalesce(func.sum(InventoryTransaction.quantity), 0)).where(
            InventoryTransaction.transaction_type == TransactionType.SALE_CONSUMPTION.value,
            InventoryTransaction.created_at >= today_start,
        )
        today_total = Decimal(str((await session.execute(today_stmt)).scalar_one() or 0))

        # Last 7 days
        seven_stmt = select(func.coalesce(func.sum(InventoryTransaction.quantity), 0)).where(
            InventoryTransaction.transaction_type == TransactionType.SALE_CONSUMPTION.value,
            InventoryTransaction.created_at >= seven_days_ago,
        )
        seven_days_total = Decimal(str((await session.execute(seven_stmt)).scalar_one() or 0))

        # Last 30 days
        thirty_stmt = select(func.coalesce(func.sum(InventoryTransaction.quantity), 0)).where(
            InventoryTransaction.transaction_type == TransactionType.SALE_CONSUMPTION.value,
            InventoryTransaction.created_at >= thirty_days_ago,
        )
        thirty_days_total = Decimal(str((await session.execute(thirty_stmt)).scalar_one() or 0))

        summary = PeriodConsumptionSummary(
            today=_round_decimal(today_total, 3),
            last_7_days=_round_decimal(seven_days_total, 3),
            last_30_days=_round_decimal(thirty_days_total, 3),
        )

        # 2. Establish active date range
        range_start = start_date if start_date is not None else thirty_days_ago
        range_end = end_date if end_date is not None else now
        days_in_period = max(1, (range_end.date() - range_start.date()).days + 1)

        # 3. Query all SALE_CONSUMPTION transactions within the window
        tx_stmt = (
            select(InventoryTransaction)
            .options(selectinload(InventoryTransaction.ingredient))
            .where(
                InventoryTransaction.transaction_type == TransactionType.SALE_CONSUMPTION.value,
                InventoryTransaction.created_at >= range_start,
                InventoryTransaction.created_at <= range_end,
            )
            .order_by(InventoryTransaction.created_at.asc())
        )
        transactions = list((await session.execute(tx_stmt)).scalars().all())

        # 4. Aggregate by ingredient
        ing_totals: dict[int, dict] = {}
        daily_buckets: dict[str, dict] = defaultdict(lambda: {"total": Decimal("0.000"), "count": 0, "by_ing": defaultdict(Decimal), "units": {}})

        for tx in transactions:
            ing = tx.ingredient
            if not ing:
                continue

            # Accumulate per ingredient
            if ing.id not in ing_totals:
                ing_totals[ing.id] = {
                    "ingredient": ing,
                    "total_consumed": Decimal("0.000"),
                }
            ing_totals[ing.id]["total_consumed"] += tx.quantity

            # Accumulate per day
            day_str = tx.created_at.strftime("%Y-%m-%d")
            daily_buckets[day_str]["total"] += tx.quantity
            daily_buckets[day_str]["count"] += 1
            daily_buckets[day_str]["by_ing"][ing.name] += tx.quantity
            daily_buckets[day_str]["units"][ing.name] = ing.unit

        # Sort top consumed
        sorted_ing = sorted(
            ing_totals.values(),
            key=lambda x: x["total_consumed"],
            reverse=True,
        )[:limit]

        top_consumed_items: List[TopConsumedIngredient] = []
        for item in sorted_ing:
            ing = item["ingredient"]
            tot = item["total_consumed"]
            avg_daily = tot / Decimal(days_in_period)
            cost = tot * ing.cost_per_unit
            top_consumed_items.append(
                TopConsumedIngredient(
                    ingredient_id=ing.id,
                    name=ing.name,
                    sku=ing.sku,
                    category=ing.category,
                    unit=ing.unit,
                    total_consumed=_round_decimal(tot, 3),
                    avg_daily_consumption=_round_decimal(avg_daily, 3),
                    total_cost=_round_decimal(cost, 2),
                )
            )

        # Build chronological daily trends
        daily_trends: List[DailyConsumptionTrend] = []
        for day_str in sorted(daily_buckets.keys()):
            bucket = daily_buckets[day_str]
            top_ings = [
                DailyIngredientConsumption(name=name, quantity=_round_decimal(qty, 3), unit=bucket["units"][name])
                for name, qty in sorted(bucket["by_ing"].items(), key=lambda k: k[1], reverse=True)[:3]
            ]
            daily_trends.append(
                DailyConsumptionTrend(
                    date=day_str,
                    total_quantity=_round_decimal(bucket["total"], 3),
                    transaction_count=bucket["count"],
                    top_ingredients=top_ings,
                )
            )

        return ConsumptionAnalyticsResponse(
            date_range={
                "start_date": range_start.isoformat(),
                "end_date": range_end.isoformat(),
                "days_in_period": days_in_period,
            },
            summary=summary,
            top_consumed=top_consumed_items,
            daily_trends=daily_trends,
        )

    @staticmethod
    async def get_popular_items(
        session: AsyncSession,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 10,
    ) -> PopularItemsResponse:
        """
        Identify top-selling menu items by quantity and revenue contribution.
        """
        stmt = (
            select(
                SaleItem.menu_item_id,
                MenuItem.name,
                MenuItem.selling_price,
                func.sum(SaleItem.quantity).label("total_qty"),
                func.sum(SaleItem.subtotal).label("total_rev"),
                func.count(func.distinct(SaleItem.sale_id)).label("order_cnt"),
            )
            .join(Sale, SaleItem.sale_id == Sale.id)
            .join(MenuItem, SaleItem.menu_item_id == MenuItem.id)
        )

        if start_date:
            stmt = stmt.where(Sale.sold_at >= start_date)
        if end_date:
            stmt = stmt.where(Sale.sold_at <= end_date)

        stmt = (
            stmt.group_by(SaleItem.menu_item_id, MenuItem.name, MenuItem.selling_price)
            .order_by(func.sum(SaleItem.quantity).desc())
            .limit(limit)
        )

        result = await session.execute(stmt)
        rows = result.all()

        # Compute overall revenue for percentage calculation
        total_rev_stmt = select(func.coalesce(func.sum(SaleItem.subtotal), 0)).join(Sale, SaleItem.sale_id == Sale.id)
        if start_date:
            total_rev_stmt = total_rev_stmt.where(Sale.sold_at >= start_date)
        if end_date:
            total_rev_stmt = total_rev_stmt.where(Sale.sold_at <= end_date)

        overall_revenue = Decimal(str((await session.execute(total_rev_stmt)).scalar_one() or 0))
        total_items_sold = sum(int(r.total_qty) for r in rows)

        popular_items: List[PopularMenuItem] = []
        for r in rows:
            item_rev = Decimal(str(r.total_rev))
            rev_pct = (
                _round_decimal((item_rev / overall_revenue) * Decimal("100.00"), 2)
                if overall_revenue > 0
                else Decimal("0.00")
            )
            popular_items.append(
                PopularMenuItem(
                    menu_item_id=r.menu_item_id,
                    name=r.name,
                    selling_price=Decimal(str(r.selling_price)),
                    total_quantity_sold=int(r.total_qty),
                    total_revenue=_round_decimal(item_rev, 2),
                    order_count=int(r.order_cnt),
                    revenue_percentage=rev_pct,
                )
            )

        return PopularItemsResponse(
            date_range={
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
            },
            total_items_sold=total_items_sold,
            total_revenue=_round_decimal(overall_revenue, 2),
            items=popular_items,
        )

    @staticmethod
    async def get_food_cost_analytics(session: AsyncSession) -> FoodCostAnalyticsResponse:
        """
        Calculate food costs, margins, and profitability for all menu items:
          - Sum ingredient costs based on RecipeIngredient and current Ingredient.cost_per_unit.
          - Compare with selling_price to determine food cost % and gross contribution.
          - Safely handle items without recipes or zero prices.
        """
        stmt = (
            select(MenuItem)
            .options(
                selectinload(MenuItem.recipe_ingredients).selectinload(RecipeIngredient.ingredient)
            )
            .order_by(MenuItem.name.asc())
        )
        menu_items = list((await session.execute(stmt)).scalars().all())

        items_food_cost: List[MenuItemFoodCost] = []
        total_food_cost_percentages: List[Decimal] = []

        for m in menu_items:
            recipe_items_cost: List[RecipeCostItem] = []
            recipe_total_cost = Decimal("0.00")

            has_recipe = len(m.recipe_ingredients) > 0

            if has_recipe:
                for ri in m.recipe_ingredients:
                    ing = ri.ingredient
                    if not ing:
                        continue
                    line_cost = ri.quantity_required * ing.cost_per_unit
                    recipe_total_cost += line_cost
                    recipe_items_cost.append(
                        RecipeCostItem(
                            ingredient_id=ing.id,
                            ingredient_name=ing.name,
                            sku=ing.sku,
                            unit=ing.unit,
                            quantity_required=_round_decimal(ri.quantity_required, 3),
                            cost_per_unit=_round_decimal(ing.cost_per_unit, 2),
                            ingredient_cost=_round_decimal(line_cost, 4),
                        )
                    )

                recipe_total_cost = _round_decimal(recipe_total_cost, 2)

                if m.selling_price > 0:
                    food_cost_pct = _round_decimal((recipe_total_cost / m.selling_price) * Decimal("100.00"), 2)
                    gross_contrib = _round_decimal(m.selling_price - recipe_total_cost, 2)
                    gross_margin_pct = _round_decimal((gross_contrib / m.selling_price) * Decimal("100.00"), 2)
                    total_food_cost_percentages.append(food_cost_pct)
                    notes = None
                else:
                    food_cost_pct = Decimal("0.00")
                    gross_contrib = Decimal("0.00") - recipe_total_cost
                    gross_margin_pct = Decimal("0.00")
                    notes = "Selling price is 0; margin cannot be computed."
            else:
                food_cost_pct = None
                gross_contrib = m.selling_price
                gross_margin_pct = Decimal("100.00") if m.selling_price > 0 else Decimal("0.00")
                notes = "No recipe defined; ingredient cost estimated at $0.00."

            items_food_cost.append(
                MenuItemFoodCost(
                    menu_item_id=m.id,
                    name=m.name,
                    selling_price=_round_decimal(m.selling_price, 2),
                    is_active=m.is_active,
                    has_recipe=has_recipe,
                    recipe_item_count=len(m.recipe_ingredients),
                    total_cost=recipe_total_cost,
                    food_cost_percentage=food_cost_pct,
                    gross_contribution=gross_contrib,
                    gross_margin_percentage=gross_margin_pct,
                    recipe_items=recipe_items_cost,
                    notes=notes,
                )
            )

        # Average food cost percentage across recipe-mapped items
        avg_fc_pct = (
            _round_decimal(sum(total_food_cost_percentages) / Decimal(len(total_food_cost_percentages)), 2)
            if total_food_cost_percentages
            else None
        )

        tier = "Optimal (< 28%)"
        if avg_fc_pct:
            if avg_fc_pct > Decimal("35.00"):
                tier = "High (> 35% - Review Pricing/Portions)"
            elif avg_fc_pct > Decimal("28.00"):
                tier = "Standard Industry Range (28% - 35%)"

        assumptions = [
            "Food cost calculations reflect current pantry cost_per_unit values. Historical price changes at time of delivery are not stored per transaction.",
            "Recipe ingredient quantities match standard pantry measurement units (kg, L, pcs). Incompatible unit conversions are avoided.",
            "Menu items lacking recipe mappings are assigned $0.00 ingredient cost and marked with a warning note.",
        ]

        return FoodCostAnalyticsResponse(
            total_menu_items=len(menu_items),
            items_with_recipes=len(total_food_cost_percentages),
            average_food_cost_percentage=avg_fc_pct,
            overall_food_cost_tier=tier,
            items=items_food_cost,
            assumptions_and_limitations=assumptions,
        )
