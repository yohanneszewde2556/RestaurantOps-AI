"""
Menu Items & Recipes API Router
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.responses import ok
from app.database.session import get_db
from app.schemas.menu_item import (
    MenuItemCreate,
    MenuItemDetailResponse,
    MenuItemUpdate,
)
from app.schemas.recipe import (
    RecipeIngredientResponse,
    RecipeSetRequest,
)
from app.services.menu_service import MenuService
from app.services.recipe_service import RecipeService

router = APIRouter(prefix="/menu-items", tags=["Menu & Recipes"])


@router.get(
    "",
    summary="List all menu items with recipe mappings",
)
async def list_menu_items(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    session: AsyncSession = Depends(get_db),
):
    items = await MenuService.list_menu_items(session, is_active=is_active)
    payload = [MenuItemDetailResponse.model_validate(item).model_dump() for item in items]
    return ok(data=payload)


@router.get(
    "/{menu_item_id}",
    summary="Get single menu item by ID with recipe mappings",
)
async def get_menu_item(
    menu_item_id: int,
    session: AsyncSession = Depends(get_db),
):
    menu_item = await MenuService.get_by_id(session, menu_item_id)
    return ok(data=MenuItemDetailResponse.model_validate(menu_item).model_dump())


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new menu item",
)
async def create_menu_item(
    data: MenuItemCreate,
    session: AsyncSession = Depends(get_db),
):
    menu_item = await MenuService.create_menu_item(session, data)
    return ok(
        data=MenuItemDetailResponse.model_validate(menu_item).model_dump(),
        message="Menu item created successfully",
    )


@router.put(
    "/{menu_item_id}",
    summary="Update an existing menu item",
)
async def update_menu_item(
    menu_item_id: int,
    data: MenuItemUpdate,
    session: AsyncSession = Depends(get_db),
):
    menu_item = await MenuService.update_menu_item(session, menu_item_id, data)
    return ok(
        data=MenuItemDetailResponse.model_validate(menu_item).model_dump(),
        message="Menu item updated successfully",
    )


@router.get(
    "/{menu_item_id}/recipe",
    summary="Get recipe ingredient mappings for a menu item",
)
async def get_menu_item_recipe(
    menu_item_id: int,
    session: AsyncSession = Depends(get_db),
):
    recipe = await RecipeService.get_recipe(session, menu_item_id)
    payload = [RecipeIngredientResponse.model_validate(r).model_dump() for r in recipe]
    return ok(data=payload)


@router.post(
    "/{menu_item_id}/recipe",
    summary="Set or replace recipe ingredient mappings for a menu item",
)
async def set_menu_item_recipe(
    menu_item_id: int,
    data: RecipeSetRequest,
    session: AsyncSession = Depends(get_db),
):
    recipe = await RecipeService.set_recipe(session, menu_item_id, data.ingredients)
    payload = [RecipeIngredientResponse.model_validate(r).model_dump() for r in recipe]
    return ok(data=payload, message="Recipe mappings saved successfully")
