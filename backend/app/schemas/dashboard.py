"""
Pydantic Schemas: Dashboard Summary
"""

from decimal import Decimal
from typing import List
from pydantic import BaseModel, ConfigDict

from app.schemas.inventory_transaction import InventoryTransactionResponse
from app.schemas.sale import SaleResponse


class DashboardSummaryResponse(BaseModel):
    total_ingredients: int
    total_active_menu_items: int
    total_inventory_value: Decimal
    low_stock_count: int
    expiring_soon_count: int
    today_sales_revenue: Decimal
    today_sales_count: int
    recent_transactions: List[InventoryTransactionResponse] = []
    recent_sales: List[SaleResponse] = []

    model_config = ConfigDict(from_attributes=True)
