"""
Pydantic Schemas: ProcurementRecommendation and ProcurementRecommendationItem
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.procurement import RecommendationStatus
from app.schemas.ingredient import IngredientResponse


class ProcurementRecommendationItemCreate(BaseModel):
    ingredient_id: int = Field(..., gt=0, description="Ingredient to procure")
    recommended_quantity: Decimal = Field(..., gt=0, description="Suggested reorder amount")
    estimated_unit_cost: Decimal = Field(..., ge=0, description="Estimated unit cost")


class ProcurementRecommendationItemResponse(BaseModel):
    id: int
    recommendation_id: int
    ingredient_id: int
    recommended_quantity: Decimal
    estimated_unit_cost: Decimal
    estimated_total_cost: Decimal
    ingredient: Optional[IngredientResponse] = None

    model_config = ConfigDict(from_attributes=True)


class ProcurementRecommendationCreate(BaseModel):
    reason: str = Field(..., min_length=1, description="Trigger rationale (e.g. low stock, upcoming weekend forecast)")
    items: List[ProcurementRecommendationItemCreate] = Field(..., min_length=1, description="List of items to order")


class ProcurementRecommendationStatusUpdate(BaseModel):
    status: RecommendationStatus = Field(..., description="New review status (APPROVED or REJECTED)")


class ProcurementRecommendationResponse(BaseModel):
    id: int
    status: str
    total_estimated_cost: Decimal
    reason: str
    created_at: datetime
    reviewed_at: Optional[datetime] = None
    items: List[ProcurementRecommendationItemResponse] = []

    model_config = ConfigDict(from_attributes=True)
