"""
Pydantic Schemas: InventoryTransaction and Inventory Adjustments
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.inventory_transaction import TransactionType
from app.schemas.ingredient import IngredientResponse


class InventoryTransactionCreate(BaseModel):
    ingredient_id: int = Field(..., gt=0, description="ID of ingredient being changed")
    transaction_type: TransactionType = Field(..., description="Reason for quantity adjustment")
    quantity: Decimal = Field(..., description="Quantity changed")
    notes: Optional[str] = Field(None, description="Optional audit notes")


class InventoryAdjustmentCreate(BaseModel):
    ingredient_id: int = Field(..., gt=0, description="ID of ingredient to adjust")
    transaction_type: TransactionType = Field(
        ..., description="Transaction classification (PURCHASE, ADJUSTMENT, or WASTE)"
    )
    quantity: Decimal = Field(
        ..., description="Quantity delta: positive to increase inventory, negative to decrease"
    )
    notes: Optional[str] = Field(
        None, description="Reason for adjustment (e.g., 'Spoiled batch', 'Supplier delivery intake')"
    )


class InventoryTransactionResponse(BaseModel):
    id: int
    ingredient_id: int
    transaction_type: str
    quantity: Decimal
    notes: Optional[str] = None
    created_at: datetime
    ingredient: Optional[IngredientResponse] = None

    model_config = ConfigDict(from_attributes=True)
