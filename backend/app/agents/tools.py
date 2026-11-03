"""
Declarations of Gemini AI tools for RestaurantOps AI.
Defines function declarations and parameters according to the google-genai SDK specification.
"""

from typing import List
from google.genai import types

# 1. get_inventory
fn_get_inventory = types.FunctionDeclaration(
    name="get_inventory",
    description="Retrieve current ingredient inventory levels, categories, units of measurement, safety thresholds, and costs per unit.",
    parameters=types.Schema(
        type="OBJECT",
        properties={
            "category": types.Schema(
                type="STRING",
                description="Optional culinary category filter, e.g. 'Produce', 'Dairy', 'Meat', 'Dry Goods', 'Beverages'.",
            ),
            "search": types.Schema(
                type="STRING",
                description="Optional search term to match against ingredient name or SKU.",
            ),
            "limit": types.Schema(
                type="INTEGER",
                description="Maximum number of ingredients to return (default 50).",
            ),
        },
    ),
)

# 2. get_sales_history
fn_get_sales_history = types.FunctionDeclaration(
    name="get_sales_history",
    description="Retrieve customer sales receipts and ordered menu items within an optional date range.",
    parameters=types.Schema(
        type="OBJECT",
        properties={
            "start_date": types.Schema(
                type="STRING",
                description="Optional start date in YYYY-MM-DD or ISO format.",
            ),
            "end_date": types.Schema(
                type="STRING",
                description="Optional end date in YYYY-MM-DD or ISO format.",
            ),
            "limit": types.Schema(
                type="INTEGER",
                description="Maximum number of sales records to return (default 20).",
            ),
        },
    ),
)

# 3. get_low_stock_ingredients
fn_get_low_stock_ingredients = types.FunctionDeclaration(
    name="get_low_stock_ingredients",
    description="Identify all ingredients whose current stock is at or below their configured minimum safety reorder threshold.",
    parameters=types.Schema(
        type="OBJECT",
        properties={},
    ),
)

# 4. get_expiring_ingredients
fn_get_expiring_ingredients = types.FunctionDeclaration(
    name="get_expiring_ingredients",
    description="Retrieve perishable ingredients approaching expiration date within a lookahead window.",
    parameters=types.Schema(
        type="OBJECT",
        properties={
            "days": types.Schema(
                type="INTEGER",
                description="Lookahead horizon in days (default 7 days).",
            ),
        },
    ),
)

# 5. analyze_stock_levels
fn_analyze_stock_levels = types.FunctionDeclaration(
    name="analyze_stock_levels",
    description="Synthesize current pantry stock against recent consumption velocity to evaluate burn rates and stockout risk.",
    parameters=types.Schema(
        type="OBJECT",
        properties={
            "days": types.Schema(
                type="INTEGER",
                description="Number of past days of consumption history to evaluate (default 30).",
            ),
        },
    ),
)

# 6. generate_purchase_plan
fn_generate_purchase_plan = types.FunctionDeclaration(
    name="generate_purchase_plan",
    description="Draft a procurement replenishment recommendation for low-stock ingredients using deterministic reorder formulas. Saves recommendation with PENDING status for manager approval.",
    parameters=types.Schema(
        type="OBJECT",
        properties={
            "reason": types.Schema(
                type="STRING",
                description="Context or business justification for this replenishment order.",
            ),
        },
    ),
)

# 7. get_consumption_analytics
fn_get_consumption_analytics = types.FunctionDeclaration(
    name="get_consumption_analytics",
    description="Retrieve ingredient consumption totals (today, last 7 days, last 30 days) and top depleted ingredients.",
    parameters=types.Schema(
        type="OBJECT",
        properties={
            "start_date": types.Schema(
                type="STRING",
                description="Optional start date filter in YYYY-MM-DD or ISO format.",
            ),
            "end_date": types.Schema(
                type="STRING",
                description="Optional end date filter in YYYY-MM-DD or ISO format.",
            ),
            "limit": types.Schema(
                type="INTEGER",
                description="Max top consumed ingredients to return (default 10).",
            ),
        },
    ),
)

# 8. get_food_cost_analytics
fn_get_food_cost_analytics = types.FunctionDeclaration(
    name="get_food_cost_analytics",
    description="Retrieve menu item recipe ingredient costs, menu selling prices, food cost percentages, and gross contribution margins.",
    parameters=types.Schema(
        type="OBJECT",
        properties={},
    ),
)

ALL_TOOL_DECLARATIONS = [
    fn_get_inventory,
    fn_get_sales_history,
    fn_get_low_stock_ingredients,
    fn_get_expiring_ingredients,
    fn_analyze_stock_levels,
    fn_generate_purchase_plan,
    fn_get_consumption_analytics,
    fn_get_food_cost_analytics,
]

GEMINI_TOOLS = [types.Tool(function_declarations=ALL_TOOL_DECLARATIONS)]
