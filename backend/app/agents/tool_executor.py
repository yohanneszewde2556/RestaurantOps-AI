"""
Tool Executor for RestaurantOps AI Agent
Routes validated Gemini tool calls to dedicated service-layer methods.
The agent interacts with the system exclusively through this service-backed dispatcher.
"""

from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ValidationException
from app.services.analytics_service import AnalyticsService
from app.services.ingredient_service import IngredientService
from app.services.inventory_service import InventoryService
from app.services.procurement_service import ProcurementService
from app.services.sales_service import SalesService


def _parse_date(val: Optional[str], is_end: bool = False) -> Optional[datetime]:
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
            return None


class ToolExecutor:
    """
    Executes permitted tools via backend services.
    Enforces strict access control and serializes outputs safely for LLM consumption.
    """

    ALLOWED_TOOLS = {
        "get_inventory",
        "get_sales_history",
        "get_low_stock_ingredients",
        "get_expiring_ingredients",
        "analyze_stock_levels",
        "generate_purchase_plan",
        "get_consumption_analytics",
        "get_food_cost_analytics",
    }

    @classmethod
    async def execute(
        cls, session: AsyncSession, tool_name: str, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Dispatch a tool call to the appropriate service-layer method."""
        if tool_name not in cls.ALLOWED_TOOLS:
            raise ValidationException(f"Unauthorized or unknown tool: '{tool_name}'")

        handler = getattr(cls, f"_tool_{tool_name}", None)
        if not handler:
            raise ValidationException(f"No execution handler configured for tool: '{tool_name}'")

        return await handler(session, args)

    # 1. get_inventory
    @classmethod
    async def _tool_get_inventory(cls, session: AsyncSession, args: Dict[str, Any]) -> Dict[str, Any]:
        category = args.get("category")
        search = args.get("search")
        limit = min(int(args.get("limit", 50)), 100)

        items, total, _ = await IngredientService.list_ingredients(
            session=session,
            page=1,
            page_size=limit,
            category=category,
            search=search,
        )

        serialized = [
            {
                "id": i.id,
                "name": i.name,
                "sku": i.sku,
                "category": i.category,
                "unit": i.unit,
                "current_quantity": float(i.current_quantity),
                "min_quantity": float(i.min_quantity),
                "cost_per_unit": float(i.cost_per_unit),
                "is_low_stock": i.current_quantity <= i.min_quantity,
                "expiry_date": i.expiry_date.isoformat() if i.expiry_date else None,
            }
            for i in items
        ]
        return {
            "total_ingredients_in_catalog": total,
            "returned_count": len(serialized),
            "ingredients": serialized,
        }

    # 2. get_sales_history
    @classmethod
    async def _tool_get_sales_history(cls, session: AsyncSession, args: Dict[str, Any]) -> Dict[str, Any]:
        start_date = _parse_date(args.get("start_date"), is_end=False)
        end_date = _parse_date(args.get("end_date"), is_end=True)
        limit = min(int(args.get("limit", 20)), 50)

        sales, total, _ = await SalesService.list_sales(
            session=session,
            page=1,
            page_size=limit,
            start_date=start_date,
            end_date=end_date,
        )

        serialized_sales = []
        for s in sales:
            items_summary = [
                {
                    "menu_item_id": it.menu_item_id,
                    "menu_item_name": it.menu_item.name if it.menu_item else "Unknown",
                    "quantity": it.quantity,
                    "unit_price": float(it.unit_price),
                    "subtotal": float(it.subtotal),
                }
                for it in s.items
            ]
            serialized_sales.append(
                {
                    "sale_id": s.id,
                    "sold_at": s.sold_at.isoformat(),
                    "total_amount": float(s.total_amount),
                    "items_count": len(s.items),
                    "items": items_summary,
                }
            )

        return {
            "total_sales_in_period": total,
            "returned_sales": len(serialized_sales),
            "sales": serialized_sales,
        }

    # 3. get_low_stock_ingredients
    @classmethod
    async def _tool_get_low_stock_ingredients(cls, session: AsyncSession, args: Dict[str, Any]) -> Dict[str, Any]:
        low_items = await InventoryService.get_low_stock(session)
        serialized = [
            {
                "id": i.id,
                "name": i.name,
                "sku": i.sku,
                "category": i.category,
                "current_quantity": float(i.current_quantity),
                "min_quantity": float(i.min_quantity),
                "unit": i.unit,
                "cost_per_unit": float(i.cost_per_unit),
                "deficit": float(i.min_quantity - i.current_quantity),
            }
            for i in low_items
        ]
        return {
            "low_stock_count": len(serialized),
            "items": serialized,
        }

    # 4. get_expiring_ingredients
    @classmethod
    async def _tool_get_expiring_ingredients(cls, session: AsyncSession, args: Dict[str, Any]) -> Dict[str, Any]:
        days = int(args.get("days", 7))
        expiring_items = await InventoryService.get_expiring(session, days=days)
        today = datetime.now(timezone.utc).date()

        serialized = [
            {
                "id": i.id,
                "name": i.name,
                "sku": i.sku,
                "category": i.category,
                "current_quantity": float(i.current_quantity),
                "unit": i.unit,
                "cost_per_unit": float(i.cost_per_unit),
                "expiry_date": i.expiry_date.isoformat() if i.expiry_date else None,
                "days_remaining": (i.expiry_date - today).days if i.expiry_date else None,
                "estimated_at_risk_value": float(i.current_quantity * i.cost_per_unit),
            }
            for i in expiring_items
        ]
        return {
            "lookahead_days": days,
            "expiring_count": len(serialized),
            "items": serialized,
        }

    # 5. analyze_stock_levels
    @classmethod
    async def _tool_analyze_stock_levels(cls, session: AsyncSession, args: Dict[str, Any]) -> Dict[str, Any]:
        days = int(args.get("days", 30))
        now = datetime.now(timezone.utc)
        start_date = now - timedelta(days=days)

        low_items = await InventoryService.get_low_stock(session)
        consumption = await AnalyticsService.get_consumption_analytics(session, start_date=start_date, limit=10)

        # Map top consumed run rates
        run_rates = {c.ingredient_id: float(c.avg_daily_consumption) for c in consumption.top_consumed}

        low_stock_analysis = []
        for i in low_items:
            daily_burn = run_rates.get(i.id, 0.0)
            days_left = round(float(i.current_quantity) / daily_burn, 1) if daily_burn > 0 else "Insufficient sales velocity data"
            low_stock_analysis.append(
                {
                    "name": i.name,
                    "current_quantity": float(i.current_quantity),
                    "min_quantity": float(i.min_quantity),
                    "unit": i.unit,
                    "avg_daily_burn": daily_burn,
                    "estimated_days_of_stock_left": days_left,
                    "urgency": "CRITICAL" if float(i.current_quantity) <= 0 else "WARNING",
                }
            )

        return {
            "assessment_window_days": days,
            "total_low_stock_items": len(low_items),
            "items_analyzed": low_stock_analysis,
            "top_consumed_pantry_items": [
                {
                    "name": c.name,
                    "total_consumed": float(c.total_consumed),
                    "avg_daily": float(c.avg_daily_consumption),
                    "unit": c.unit,
                }
                for c in consumption.top_consumed[:5]
            ],
        }

    # 6. generate_purchase_plan
    @classmethod
    async def _tool_generate_purchase_plan(cls, session: AsyncSession, args: Dict[str, Any]) -> Dict[str, Any]:
        reason = args.get("reason", "Replenishment recommendation generated via AI Assistant")
        rec = await ProcurementService.generate_recommendations(session, reason=reason)

        items_serialized = [
            {
                "ingredient_id": it.ingredient_id,
                "ingredient_name": it.ingredient.name if it.ingredient else "Unknown",
                "recommended_quantity": float(it.recommended_quantity),
                "unit": it.ingredient.unit if it.ingredient else "",
                "estimated_unit_cost": float(it.estimated_unit_cost),
                "estimated_total_cost": float(it.estimated_total_cost),
            }
            for it in rec.items
        ]

        return {
            "recommendation_id": rec.id,
            "status": rec.status,
            "total_estimated_cost": float(rec.total_estimated_cost),
            "reason": rec.reason,
            "items_count": len(rec.items),
            "items": items_serialized,
            "governance_note": "CRITICAL: This procurement recommendation is saved with PENDING status. The restaurant manager must review and explicitly approve this order on the dashboard before any purchase can be executed.",
        }

    # 7. get_consumption_analytics
    @classmethod
    async def _tool_get_consumption_analytics(cls, session: AsyncSession, args: Dict[str, Any]) -> Dict[str, Any]:
        start_date = _parse_date(args.get("start_date"), is_end=False)
        end_date = _parse_date(args.get("end_date"), is_end=True)
        limit = min(int(args.get("limit", 10)), 50)

        data = await AnalyticsService.get_consumption_analytics(
            session=session, start_date=start_date, end_date=end_date, limit=limit
        )

        return {
            "period_summary": {
                "today": float(data.summary.today),
                "last_7_days": float(data.summary.last_7_days),
                "last_30_days": float(data.summary.last_30_days),
            },
            "top_consumed_ingredients": [
                {
                    "name": i.name,
                    "sku": i.sku,
                    "category": i.category,
                    "unit": i.unit,
                    "total_consumed": float(i.total_consumed),
                    "avg_daily_consumption": float(i.avg_daily_consumption),
                    "total_cost": float(i.total_cost),
                }
                for i in data.top_consumed
            ],
            "days_analyzed": data.date_range["days_in_period"],
        }

    # 8. get_food_cost_analytics
    @classmethod
    async def _tool_get_food_cost_analytics(cls, session: AsyncSession, args: Dict[str, Any]) -> Dict[str, Any]:
        data = await AnalyticsService.get_food_cost_analytics(session)
        items_summary = [
            {
                "name": it.name,
                "selling_price": float(it.selling_price),
                "recipe_cost": float(it.total_cost),
                "food_cost_percentage": float(it.food_cost_percentage) if it.food_cost_percentage is not None else None,
                "gross_contribution": float(it.gross_contribution),
                "has_recipe": it.has_recipe,
            }
            for it in data.items
        ]

        return {
            "total_menu_items": data.total_menu_items,
            "items_with_recipes": data.items_with_recipes,
            "average_food_cost_percentage": float(data.average_food_cost_percentage) if data.average_food_cost_percentage else None,
            "overall_tier": data.overall_food_cost_tier,
            "menu_items": items_summary,
        }
