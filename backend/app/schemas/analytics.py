"""
Pydantic Schemas: Analytics
Request and response schemas for consumption trends, popular items, and food cost analytics.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field


# ── Consumption Analytics ──────────────────────────────────────────

class PeriodConsumptionSummary(BaseModel):
    today: Decimal = Field(default=Decimal("0.000"), description="Total consumption recorded today")
    last_7_days: Decimal = Field(default=Decimal("0.000"), description="Total consumption over the last 7 days")
    last_30_days: Decimal = Field(default=Decimal("0.000"), description="Total consumption over the last 30 days")


class TopConsumedIngredient(BaseModel):
    ingredient_id: int
    name: str
    sku: str
    category: str
    unit: str
    total_consumed: Decimal = Field(ge=0, description="Total units consumed in period")
    avg_daily_consumption: Decimal = Field(ge=0, description="Average units consumed per day")
    total_cost: Decimal = Field(ge=0, description="Estimated total cost based on current unit cost")


class DailyIngredientConsumption(BaseModel):
    name: str
    quantity: Decimal
    unit: str


class DailyConsumptionTrend(BaseModel):
    date: str = Field(description="Date in YYYY-MM-DD format")
    total_quantity: Decimal = Field(ge=0, description="Total volume consumed on this date")
    transaction_count: int = Field(ge=0, description="Number of consumption events")
    top_ingredients: List[DailyIngredientConsumption] = Field(default_factory=list)


class ConsumptionAnalyticsResponse(BaseModel):
    date_range: dict
    summary: PeriodConsumptionSummary
    top_consumed: List[TopConsumedIngredient]
    daily_trends: List[DailyConsumptionTrend]


# ── Popular Items Analytics ────────────────────────────────────────

class PopularMenuItem(BaseModel):
    menu_item_id: int
    name: str
    selling_price: Decimal
    total_quantity_sold: int = Field(ge=0)
    total_revenue: Decimal = Field(ge=0)
    order_count: int = Field(ge=0)
    revenue_percentage: Decimal = Field(ge=0, le=100)


class PopularItemsResponse(BaseModel):
    date_range: dict
    total_items_sold: int
    total_revenue: Decimal
    items: List[PopularMenuItem]


# ── Food Cost & Profitability ──────────────────────────────────────

class RecipeCostItem(BaseModel):
    ingredient_id: int
    ingredient_name: str
    sku: str
    unit: str
    quantity_required: Decimal
    cost_per_unit: Decimal
    ingredient_cost: Decimal


class MenuItemFoodCost(BaseModel):
    menu_item_id: int
    name: str
    selling_price: Decimal
    is_active: bool
    has_recipe: bool
    recipe_item_count: int
    total_cost: Decimal
    food_cost_percentage: Optional[Decimal] = None
    gross_contribution: Decimal
    gross_margin_percentage: Optional[Decimal] = None
    recipe_items: List[RecipeCostItem] = Field(default_factory=list)
    notes: Optional[str] = None


class FoodCostAnalyticsResponse(BaseModel):
    total_menu_items: int
    items_with_recipes: int
    average_food_cost_percentage: Optional[Decimal] = None
    overall_food_cost_tier: str
    items: List[MenuItemFoodCost]
    assumptions_and_limitations: List[str]
