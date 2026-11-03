"""
App Schemas Package
Exports all domain Pydantic request and response schemas.
"""

from app.schemas.common import PaginatedResponse
from app.schemas.ingredient import (
    IngredientBase,
    IngredientCreate,
    IngredientUpdate,
    IngredientResponse,
)
from app.schemas.menu_item import (
    MenuItemBase,
    MenuItemCreate,
    MenuItemUpdate,
    MenuItemResponse,
    MenuItemDetailResponse,
)
from app.schemas.recipe import (
    RecipeIngredientBase,
    RecipeIngredientCreate,
    RecipeIngredientUpdate,
    RecipeIngredientResponse,
    RecipeSetItem,
    RecipeSetRequest,
)
from app.schemas.sale import (
    SaleCreate,
    SaleResponse,
    SaleItemCreate,
    SaleItemResponse,
)
from app.schemas.inventory_transaction import (
    InventoryTransactionCreate,
    InventoryAdjustmentCreate,
    InventoryTransactionResponse,
)
from app.schemas.procurement import (
    ProcurementRecommendationCreate,
    ProcurementRecommendationResponse,
    ProcurementRecommendationItemCreate,
    ProcurementRecommendationItemResponse,
    ProcurementRecommendationStatusUpdate,
)
from app.schemas.automation import (
    AutomationLogCreate,
    AutomationLogUpdate,
    AutomationLogResponse,
)
from app.schemas.dashboard import DashboardSummaryResponse
from app.schemas.analytics import (
    ConsumptionAnalyticsResponse,
    PopularItemsResponse,
    FoodCostAnalyticsResponse,
)
from app.schemas.agent import (
    ChatMessageInput,
    AgentChatRequest,
    AgentChatResponse,
    AgentStatusResponse,
)

__all__ = [
    "PaginatedResponse",
    "IngredientBase",
    "IngredientCreate",
    "IngredientUpdate",
    "IngredientResponse",
    "MenuItemBase",
    "MenuItemCreate",
    "MenuItemUpdate",
    "MenuItemResponse",
    "MenuItemDetailResponse",
    "RecipeIngredientBase",
    "RecipeIngredientCreate",
    "RecipeIngredientUpdate",
    "RecipeIngredientResponse",
    "RecipeSetItem",
    "RecipeSetRequest",
    "SaleCreate",
    "SaleResponse",
    "SaleItemCreate",
    "SaleItemResponse",
    "InventoryTransactionCreate",
    "InventoryAdjustmentCreate",
    "InventoryTransactionResponse",
    "ProcurementRecommendationCreate",
    "ProcurementRecommendationResponse",
    "ProcurementRecommendationItemCreate",
    "ProcurementRecommendationItemResponse",
    "ProcurementRecommendationStatusUpdate",
    "AutomationLogCreate",
    "AutomationLogUpdate",
    "AutomationLogResponse",
    "DashboardSummaryResponse",
    "ConsumptionAnalyticsResponse",
    "PopularItemsResponse",
    "FoodCostAnalyticsResponse",
    "ChatMessageInput",
    "AgentChatRequest",
    "AgentChatResponse",
    "AgentStatusResponse",
]
