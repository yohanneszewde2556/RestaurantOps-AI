"""
Ingredients API Router
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.responses import ok
from app.database.session import get_db
from app.schemas.common import PaginatedResponse
from app.schemas.ingredient import (
    IngredientCreate,
    IngredientResponse,
    IngredientUpdate,
)
from app.services.ingredient_service import IngredientService

router = APIRouter(prefix="/ingredients", tags=["Ingredients"])


@router.get(
    "",
    summary="List ingredients with pagination, category filter, and search",
)
async def list_ingredients(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search by ingredient name or SKU"),
    session: AsyncSession = Depends(get_db),
):
    items, total, pages = await IngredientService.list_ingredients(
        session=session,
        page=page,
        page_size=page_size,
        category=category,
        search=search,
    )
    payload = PaginatedResponse[IngredientResponse](
        items=[IngredientResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )
    return ok(data=payload.model_dump())


@router.get(
    "/{ingredient_id}",
    summary="Get single ingredient by ID",
)
async def get_ingredient(
    ingredient_id: int,
    session: AsyncSession = Depends(get_db),
):
    ingredient = await IngredientService.get_by_id(session, ingredient_id)
    return ok(data=IngredientResponse.model_validate(ingredient).model_dump())


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new ingredient",
)
async def create_ingredient(
    data: IngredientCreate,
    session: AsyncSession = Depends(get_db),
):
    ingredient = await IngredientService.create_ingredient(session, data)
    return ok(
        data=IngredientResponse.model_validate(ingredient).model_dump(),
        message="Ingredient created successfully",
    )


@router.put(
    "/{ingredient_id}",
    summary="Update an existing ingredient",
)
async def update_ingredient(
    ingredient_id: int,
    data: IngredientUpdate,
    session: AsyncSession = Depends(get_db),
):
    ingredient = await IngredientService.update_ingredient(session, ingredient_id, data)
    return ok(
        data=IngredientResponse.model_validate(ingredient).model_dump(),
        message="Ingredient updated successfully",
    )


@router.delete(
    "/{ingredient_id}",
    summary="Delete an unreferenced ingredient",
)
async def delete_ingredient(
    ingredient_id: int,
    session: AsyncSession = Depends(get_db),
):
    await IngredientService.delete_ingredient(session, ingredient_id)
    return ok(data={"id": ingredient_id}, message="Ingredient deleted successfully")
