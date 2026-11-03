"""
Pydantic Schemas: Ingredient
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class IngredientBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=150, description="Name of the ingredient")
    sku: str = Field(..., min_length=1, max_length=50, description="Unique stock keeping unit")
    category: str = Field(..., min_length=1, max_length=50, description="Ingredient category (e.g., Produce, Dairy)")
    unit: str = Field(..., min_length=1, max_length=20, description="Measurement unit (e.g., kg, L, pcs)")
    min_quantity: Decimal = Field(..., ge=0, description="Threshold minimum quantity for low-stock alerts")
    cost_per_unit: Decimal = Field(..., ge=0, description="Unit acquisition cost")
    expiry_date: Optional[date] = Field(None, description="Expiration date of current stock, if applicable")


class IngredientCreate(IngredientBase):
    current_quantity: Decimal = Field(default=Decimal("0.000"), ge=0, description="Initial stock level")


class IngredientUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    sku: Optional[str] = Field(None, min_length=1, max_length=50)
    category: Optional[str] = Field(None, min_length=1, max_length=50)
    unit: Optional[str] = Field(None, min_length=1, max_length=20)
    current_quantity: Optional[Decimal] = Field(None, ge=0)
    min_quantity: Optional[Decimal] = Field(None, ge=0)
    cost_per_unit: Optional[Decimal] = Field(None, ge=0)
    expiry_date: Optional[date] = None


class IngredientResponse(IngredientBase):
    id: int
    current_quantity: Decimal
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
