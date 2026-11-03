"""
Recipe Service
Handles recipe ingredient consumption mappings for menu items.
"""

from typing import List
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, ValidationException
from app.models.ingredient import Ingredient
from app.models.menu_item import MenuItem
from app.models.recipe import RecipeIngredient
from app.schemas.recipe import RecipeSetItem


class RecipeService:

    @staticmethod
    async def get_recipe(session: AsyncSession, menu_item_id: int) -> List[RecipeIngredient]:
        """Retrieve all recipe ingredients for a menu item."""
        # Check menu item exists
        item_check = select(MenuItem).where(MenuItem.id == menu_item_id)
        menu_item = (await session.execute(item_check)).scalar_one_or_none()
        if not menu_item:
            raise NotFoundException("MenuItem", menu_item_id)

        stmt = (
            select(RecipeIngredient)
            .where(RecipeIngredient.menu_item_id == menu_item_id)
            .order_by(RecipeIngredient.id.asc())
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def set_recipe(
        session: AsyncSession, menu_item_id: int, ingredients: List[RecipeSetItem]
    ) -> List[RecipeIngredient]:
        """
        Set or update complete recipe mappings for a menu item.
        Validates ingredients existence and ensures no duplicate mappings.
        """
        # 1. Check menu item exists
        item_check = select(MenuItem).where(MenuItem.id == menu_item_id)
        menu_item = (await session.execute(item_check)).scalar_one_or_none()
        if not menu_item:
            raise NotFoundException("MenuItem", menu_item_id)

        # 2. Check for duplicate ingredient IDs in request
        ingredient_ids = [item.ingredient_id for item in ingredients]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise ValidationException(
                "Duplicate ingredients detected in recipe mapping. Each ingredient can only be added once per recipe."
            )

        # 3. Validate all referenced ingredients exist
        ing_check = select(Ingredient.id).where(Ingredient.id.in_(ingredient_ids))
        existing_ids = set((await session.execute(ing_check)).scalars().all())
        missing_ids = set(ingredient_ids) - existing_ids
        if missing_ids:
            raise ValidationException(
                f"Referenced ingredient ID(s) do not exist: {sorted(list(missing_ids))}"
            )

        # 4. Remove previous recipe ingredient rows
        await session.execute(
            delete(RecipeIngredient).where(RecipeIngredient.menu_item_id == menu_item_id)
        )

        # 5. Insert updated mappings
        new_mappings = [
            RecipeIngredient(
                menu_item_id=menu_item_id,
                ingredient_id=item.ingredient_id,
                quantity_required=item.quantity_required,
            )
            for item in ingredients
        ]
        session.add_all(new_mappings)
        await session.commit()

        # Reload with relationships
        return await RecipeService.get_recipe(session, menu_item_id)
