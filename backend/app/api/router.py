"""
Central API Router
Aggregates and mounts all domain sub-routers.
"""

from fastapi import APIRouter
from app.api.health import router as health_router
from app.api.ingredients import router as ingredients_router
from app.api.menu_items import router as menu_items_router
from app.api.sales import router as sales_router
from app.api.inventory import router as inventory_router
from app.api.dashboard import router as dashboard_router
from app.api.analytics import router as analytics_router
from app.api.agent import router as agent_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(ingredients_router)
api_router.include_router(menu_items_router)
api_router.include_router(sales_router)
api_router.include_router(inventory_router)
api_router.include_router(dashboard_router)
api_router.include_router(analytics_router)
api_router.include_router(agent_router)
