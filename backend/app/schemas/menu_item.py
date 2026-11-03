"""
Pydantic Schemas: MenuItem
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.recipe import RecipeIngredientResponse


class MenuItemBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=150, description="Menu item display name")
    description: Optional[str] = Field(None, description="Detailed dish description")
    selling_price: Decimal = Field(..., ge=0, description="Retail selling price")
    is_active: bool = Field(default=True, description="Whether item is currently offered")


class MenuItemCreate(MenuItemBase):
    pass


class MenuItemUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    description: Optional[str] = None
    selling_price: Optional[Decimal] = Field(None, ge=0)
    is_active: Optional[bool] = None


class MenuItemResponse(MenuItemBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MenuItemDetailResponse(MenuItemResponse):
    recipe_ingredients: List[RecipeIngredientResponse] = Field(
        default_factory=list, description="Ingredient consumption recipe mappings"
    )

    model_config = ConfigDict(from_attributes=True)
