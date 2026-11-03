"""
Pydantic Schemas: Sale and SaleItem
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.menu_item import MenuItemResponse


class SaleItemCreate(BaseModel):
    menu_item_id: int = Field(..., gt=0, description="Sold menu item ID")
    quantity: int = Field(..., gt=0, description="Units sold")
    unit_price: Optional[Decimal] = Field(
        None, ge=0, description="Selling price per unit at sale time (defaults to MenuItem price if omitted)"
    )


class SaleItemResponse(BaseModel):
    id: int
    sale_id: int
    menu_item_id: int
    quantity: int
    unit_price: Decimal
    subtotal: Decimal
    menu_item: Optional[MenuItemResponse] = None

    model_config = ConfigDict(from_attributes=True)


class SaleCreate(BaseModel):
    sold_at: Optional[datetime] = Field(None, description="Timestamp when sale occurred; defaults to now")
    items: List[SaleItemCreate] = Field(..., min_length=1, description="List of items sold")


class SaleResponse(BaseModel):
    id: int
    total_amount: Decimal
    sold_at: datetime
    created_at: datetime
    items: List[SaleItemResponse] = []

    model_config = ConfigDict(from_attributes=True)
