"""
App Models Package
Exports all SQLAlchemy models for clean imports and Alembic discovery.
"""

from app.models.ingredient import Ingredient
from app.models.menu_item import MenuItem
from app.models.recipe import RecipeIngredient
from app.models.sale import Sale, SaleItem
from app.models.inventory_transaction import InventoryTransaction, TransactionType
from app.models.procurement import (
    ProcurementRecommendation,
    ProcurementRecommendationItem,
    RecommendationStatus,
)
from app.models.automation import AutomationLog, AutomationStatus

__all__ = [
    "Ingredient",
    "MenuItem",
    "RecipeIngredient",
    "Sale",
    "SaleItem",
    "InventoryTransaction",
    "TransactionType",
    "ProcurementRecommendation",
    "ProcurementRecommendationItem",
    "RecommendationStatus",
    "AutomationLog",
    "AutomationStatus",
]
