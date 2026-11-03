"""
Sales Service
Handles sales transactions, pricing calculations, atomic inventory deductions,
and auditable consumption logging.
"""

from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal
import math
from typing import Optional, Tuple
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    InsufficientStockException,
    NotFoundException,
    ValidationException,
)
from app.models.ingredient import Ingredient
from app.models.inventory_transaction import InventoryTransaction, TransactionType
from app.models.menu_item import MenuItem
from app.models.recipe import RecipeIngredient
from app.models.sale import Sale, SaleItem
from app.schemas.sale import SaleCreate


class SalesService:

    @staticmethod
    async def list_sales(
        session: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Tuple[list[Sale], int, int]:
        """List sales with pagination and optional date filters."""
        stmt = select(Sale)

        if start_date:
            stmt = stmt.where(Sale.sold_at >= start_date)
        if end_date:
            stmt = stmt.where(Sale.sold_at <= end_date)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await session.execute(count_stmt)).scalar_one()

        pages = max(1, math.ceil(total / page_size)) if total > 0 else 1
        offset = (page - 1) * page_size

        stmt = stmt.order_by(Sale.sold_at.desc(), Sale.id.desc()).offset(offset).limit(page_size)
        result = await session.execute(stmt)
        items = list(result.scalars().all())

        return items, total, pages

    @staticmethod
    async def get_by_id(session: AsyncSession, sale_id: int) -> Sale:
        """Retrieve a single sale by ID."""
        stmt = select(Sale).where(Sale.id == sale_id)
        result = await session.execute(stmt)
        sale = result.scalar_one_or_none()
        if not sale:
            raise NotFoundException("Sale", sale_id)
        return sale

    @staticmethod
    async def record_sale(session: AsyncSession, data: SaleCreate) -> Sale:
        """
        Record a sale atomically:
          1. Validate requested menu items exist and are active.
          2. Aggregate items to handle multiple lines of the same menu item.
          3. Calculate total ingredient depletion from recipe mappings.
          4. Check inventory sufficiency. If any ingredient is short, rollback and raise error.
          5. Calculate sale monetary total using Decimal.
          6. Insert Sale and SaleItem records.
          7. Deduct inventory quantities.
          8. Insert SALE_CONSUMPTION inventory audit transactions.
          9. Commit all changes atomically.
        """
        if not data.items:
            raise ValidationException("Sale must contain at least one item.")

        sold_time = data.sold_at or datetime.now(timezone.utc)

        # 1. Aggregate requested quantities by menu_item_id
        requested_items: dict[int, int] = defaultdict(int)
        for item in data.items:
            if item.quantity <= 0:
                raise ValidationException(f"Quantity for menu item {item.menu_item_id} must be greater than 0.")
            requested_items[item.menu_item_id] += item.quantity

        menu_item_ids = list(requested_items.keys())

        # 2. Query all requested menu items
        menu_items_stmt = select(MenuItem).where(MenuItem.id.in_(menu_item_ids))
        menu_items_res = (await session.execute(menu_items_stmt)).scalars().all()
        menu_items_map = {m.id: m for m in menu_items_res}

        # Check for missing or inactive menu items
        missing_menu_items = set(menu_item_ids) - set(menu_items_map.keys())
        if missing_menu_items:
            raise ValidationException(f"Menu item(s) do not exist: {sorted(list(missing_menu_items))}")

        for m_id, m_item in menu_items_map.items():
            if not m_item.is_active:
                raise ValidationException(
                    f"Menu item '{m_item.name}' (ID: {m_id}) is inactive and cannot be sold."
                )

        # 3. Retrieve recipes and compute ingredient consumption
        # Map: ingredient_id -> Decimal required
        required_ingredients: dict[int, Decimal] = defaultdict(lambda: Decimal("0.000"))

        recipes_stmt = select(RecipeIngredient).where(RecipeIngredient.menu_item_id.in_(menu_item_ids))
        recipe_rows = (await session.execute(recipes_stmt)).scalars().all()

        for r in recipe_rows:
            qty_sold = requested_items[r.menu_item_id]
            required_ingredients[r.ingredient_id] += r.quantity_required * Decimal(qty_sold)

        # 4. Check stock availability if any ingredients are required
        if required_ingredients:
            ing_ids = list(required_ingredients.keys())
            ing_stmt = select(Ingredient).where(Ingredient.id.in_(ing_ids))
            ing_res = (await session.execute(ing_stmt)).scalars().all()
            ing_map = {ing.id: ing for ing in ing_res}

            insufficient_items = []
            for ing_id, required_qty in required_ingredients.items():
                ingredient = ing_map.get(ing_id)
                if not ingredient:
                    insufficient_items.append({
                        "ingredient_id": ing_id,
                        "name": f"Unknown (ID: {ing_id})",
                        "available": 0,
                        "required": float(required_qty),
                        "unit": "unknown",
                    })
                elif ingredient.current_quantity < required_qty:
                    insufficient_items.append({
                        "ingredient_id": ingredient.id,
                        "name": ingredient.name,
                        "available": float(ingredient.current_quantity),
                        "required": float(required_qty),
                        "unit": ingredient.unit,
                    })

            if insufficient_items:
                raise InsufficientStockException(details=insufficient_items)

        # 5. Calculate total sale amount & prepare SaleItem rows
        total_sale_amount = Decimal("0.00")
        sale_items_to_create: list[SaleItem] = []

        for item in data.items:
            menu_obj = menu_items_map[item.menu_item_id]
            # Use unit_price from item if provided and positive, else menu item price
            unit_price = item.unit_price if item.unit_price is not None else menu_obj.selling_price
            subtotal = unit_price * item.quantity
            total_sale_amount += subtotal

            sale_items_to_create.append(
                SaleItem(
                    menu_item_id=menu_obj.id,
                    quantity=item.quantity,
                    unit_price=unit_price,
                    subtotal=subtotal,
                )
            )

        # 6. Create Sale record
        sale = Sale(
            total_amount=total_sale_amount,
            sold_at=sold_time,
            created_at=datetime.now(timezone.utc),
        )
        session.add(sale)
        await session.flush()

        # Link sale_id to items
        for s_item in sale_items_to_create:
            s_item.sale_id = sale.id
            session.add(s_item)

        # 7. Deduct stock and record audit transactions
        if required_ingredients:
            for ing_id, required_qty in required_ingredients.items():
                ingredient = ing_map[ing_id]
                ingredient.current_quantity -= required_qty

                # Record inventory transaction
                session.add(
                    InventoryTransaction(
                        ingredient_id=ingredient.id,
                        transaction_type=TransactionType.SALE_CONSUMPTION.value,
                        quantity=required_qty,
                        notes=f"Auto consumption for Sale #{sale.id}",
                        created_at=sold_time,
                    )
                )

        # 8. Commit entire atomic transaction
        await session.commit()
        await session.refresh(sale)
        return sale
