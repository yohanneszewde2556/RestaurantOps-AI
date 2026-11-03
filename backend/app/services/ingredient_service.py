"""
Ingredient Service
Handles ingredient inventory business logic and database queries.
"""

from decimal import Decimal
import math
from typing import Optional, Tuple
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, NotFoundException
from app.models.ingredient import Ingredient
from app.models.inventory_transaction import InventoryTransaction, TransactionType
from app.models.procurement import ProcurementRecommendationItem
from app.models.recipe import RecipeIngredient
from app.schemas.ingredient import IngredientCreate, IngredientUpdate


class IngredientService:

    @staticmethod
    async def list_ingredients(
        session: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        category: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Tuple[list[Ingredient], int, int]:
        """
        List ingredients with pagination, category filter, and search.
        Returns: (items, total_count, total_pages)
        """
        stmt = select(Ingredient)

        if category:
            stmt = stmt.where(Ingredient.category.ilike(f"%{category.strip()}%"))

        if search:
            search_term = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    Ingredient.name.ilike(search_term),
                    Ingredient.sku.ilike(search_term),
                )
            )

        # Count total matching rows
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await session.execute(count_stmt)).scalar_one()

        pages = max(1, math.ceil(total / page_size)) if total > 0 else 1
        offset = (page - 1) * page_size

        stmt = stmt.order_by(Ingredient.category.asc(), Ingredient.name.asc()).offset(offset).limit(page_size)
        result = await session.execute(stmt)
        items = list(result.scalars().all())

        return items, total, pages

    @staticmethod
    async def get_by_id(session: AsyncSession, ingredient_id: int) -> Ingredient:
        """Retrieve a single ingredient by ID or raise NotFoundException."""
        stmt = select(Ingredient).where(Ingredient.id == ingredient_id)
        result = await session.execute(stmt)
        ingredient = result.scalar_one_or_none()

        if not ingredient:
            raise NotFoundException("Ingredient", ingredient_id)
        return ingredient

    @staticmethod
    async def create_ingredient(session: AsyncSession, data: IngredientCreate) -> Ingredient:
        """Create a new ingredient, ensuring unique SKU."""
        # Check SKU uniqueness
        sku_check = select(Ingredient).where(Ingredient.sku == data.sku.strip())
        existing = (await session.execute(sku_check)).scalar_one_or_none()
        if existing:
            raise ConflictException(
                message=f"An ingredient with SKU '{data.sku}' already exists.",
                detail=f"Existing ingredient ID: {existing.id}, Name: {existing.name}",
            )

        ingredient = Ingredient(
            name=data.name.strip(),
            sku=data.sku.strip().upper(),
            category=data.category.strip(),
            unit=data.unit.strip(),
            current_quantity=data.current_quantity,
            min_quantity=data.min_quantity,
            cost_per_unit=data.cost_per_unit,
            expiry_date=data.expiry_date,
        )
        session.add(ingredient)
        await session.flush()

        # If created with initial stock, log an initial PURCHASE transaction
        if data.current_quantity > Decimal("0.000"):
            session.add(
                InventoryTransaction(
                    ingredient_id=ingredient.id,
                    transaction_type=TransactionType.PURCHASE.value,
                    quantity=data.current_quantity,
                    notes=f"Initial stock creation for {ingredient.name}",
                )
            )

        await session.commit()
        await session.refresh(ingredient)
        return ingredient

    @staticmethod
    async def update_ingredient(
        session: AsyncSession, ingredient_id: int, data: IngredientUpdate
    ) -> Ingredient:
        """Update an existing ingredient."""
        ingredient = await IngredientService.get_by_id(session, ingredient_id)

        # Check SKU uniqueness if changing SKU
        if data.sku and data.sku.strip().upper() != ingredient.sku:
            new_sku = data.sku.strip().upper()
            sku_check = select(Ingredient).where(Ingredient.sku == new_sku)
            existing = (await session.execute(sku_check)).scalar_one_or_none()
            if existing and existing.id != ingredient_id:
                raise ConflictException(f"An ingredient with SKU '{new_sku}' already exists.")
            ingredient.sku = new_sku

        if data.name is not None:
            ingredient.name = data.name.strip()
        if data.category is not None:
            ingredient.category = data.category.strip()
        if data.unit is not None:
            ingredient.unit = data.unit.strip()
        if data.current_quantity is not None:
            ingredient.current_quantity = data.current_quantity
        if data.min_quantity is not None:
            ingredient.min_quantity = data.min_quantity
        if data.cost_per_unit is not None:
            ingredient.cost_per_unit = data.cost_per_unit
        if data.expiry_date is not None:
            ingredient.expiry_date = data.expiry_date

        await session.commit()
        await session.refresh(ingredient)
        return ingredient

    @staticmethod
    async def delete_ingredient(session: AsyncSession, ingredient_id: int) -> None:
        """
        Delete an ingredient if not referenced by recipes, inventory transactions,
        or procurement items.
        """
        ingredient = await IngredientService.get_by_id(session, ingredient_id)

        # 1. Check recipes
        recipes_check = select(func.count()).select_from(RecipeIngredient).where(
            RecipeIngredient.ingredient_id == ingredient_id
        )
        recipe_count = (await session.execute(recipes_check)).scalar_one()
        if recipe_count > 0:
            raise ConflictException(
                "Cannot delete ingredient",
                detail=f"Ingredient is referenced in {recipe_count} recipe mapping(s). Remove it from recipes first.",
            )

        # 2. Check inventory transactions
        tx_check = select(func.count()).select_from(InventoryTransaction).where(
            InventoryTransaction.ingredient_id == ingredient_id
        )
        tx_count = (await session.execute(tx_check)).scalar_one()
        if tx_count > 0:
            raise ConflictException(
                "Cannot delete ingredient",
                detail=f"Ingredient has {tx_count} historical audit transaction(s). Historical records cannot be orphaned.",
            )

        # 3. Check procurement recommendations
        proc_check = select(func.count()).select_from(ProcurementRecommendationItem).where(
            ProcurementRecommendationItem.ingredient_id == ingredient_id
        )
        proc_count = (await session.execute(proc_check)).scalar_one()
        if proc_count > 0:
            raise ConflictException(
                "Cannot delete ingredient",
                detail=f"Ingredient is referenced in {proc_count} procurement recommendation line item(s).",
            )

        await session.delete(ingredient)
        await session.commit()
