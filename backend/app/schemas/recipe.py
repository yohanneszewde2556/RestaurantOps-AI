"""
Pydantic Schemas: RecipeIngredient
"""

from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.ingredient import IngredientResponse


class RecipeIngredientBase(BaseModel):
    ingredient_id: int = Field(..., gt=0, description="ID of the ingredient used in recipe")
    quantity_required: Decimal = Field(..., gt=0, description="Quantity of ingredient required per menu item")


class RecipeIngredientCreate(RecipeIngredientBase):
    menu_item_id: int = Field(..., gt=0, description="ID of the parent menu item")


class RecipeIngredientUpdate(BaseModel):
    quantity_required: Optional[Decimal] = Field(None, gt=0)


class RecipeIngredientResponse(BaseModel):
    id: int
    menu_item_id: int
    ingredient_id: int
    quantity_required: Decimal
    ingredient: Optional[IngredientResponse] = None

    model_config = ConfigDict(from_attributes=True)


class RecipeSetItem(BaseModel):
    ingredient_id: int = Field(..., gt=0, description="Ingredient ID")
    quantity_required: Decimal = Field(..., gt=0, description="Quantity required per unit of menu item")


class RecipeSetRequest(BaseModel):
    ingredients: List[RecipeSetItem] = Field(
        ..., min_length=1, description="Complete list of ingredient mappings for this menu item"
    )
