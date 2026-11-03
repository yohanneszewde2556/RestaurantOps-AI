"""
Database Seed Script for RestaurantOps AI.

Populates the database with realistic, internally consistent restaurant operational data:
  - 19 ingredients across 5 categories (Produce, Dairy, Meat, Dry Goods, Beverages)
  - 6 menu items with complete recipe-ingredient consumption mappings
  - Historical inventory transactions (initial purchases)
  - 12 realistic sales across multiple days with sale items and consumption transactions
  - 1 low-stock procurement recommendation with recommendation items
  - Sample automation logs

Idempotent: Safe to execute repeatedly without duplicating data.
Can be executed directly: `python -m app.database.seed`
"""

import asyncio
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import AsyncSessionLocal
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


async def seed_data(session: AsyncSession) -> None:
    now = datetime.now(timezone.utc)
    today = now.date()

    # ─────────────────────────────────────────────────────────────────
    # 1. INGREDIENTS
    # ─────────────────────────────────────────────────────────────────
    ingredients_data = [
        # Produce
        {"sku": "ING-PROD-001", "name": "Roma Tomatoes", "category": "Produce", "unit": "kg", "current": "14.500", "min": "5.000", "cost": "2.50", "expiry": today + timedelta(days=6)},
        {"sku": "ING-PROD-002", "name": "Iceberg Lettuce", "category": "Produce", "unit": "kg", "current": "7.800", "min": "3.000", "cost": "1.80", "expiry": today + timedelta(days=4)},
        {"sku": "ING-PROD-003", "name": "Yellow Onions", "category": "Produce", "unit": "kg", "current": "24.000", "min": "8.000", "cost": "1.20", "expiry": today + timedelta(days=21)},
        {"sku": "ING-PROD-004", "name": "Russet Potatoes", "category": "Produce", "unit": "kg", "current": "38.500", "min": "15.000", "cost": "0.95", "expiry": today + timedelta(days=30)},
        # Dairy
        {"sku": "ING-DAIR-001", "name": "Cheddar Cheese", "category": "Dairy", "unit": "kg", "current": "11.200", "min": "4.000", "cost": "9.50", "expiry": today + timedelta(days=16)},
        {"sku": "ING-DAIR-002", "name": "Whole Milk", "category": "Dairy", "unit": "L", "current": "16.500", "min": "6.000", "cost": "1.40", "expiry": today + timedelta(days=7)},
        {"sku": "ING-DAIR-003", "name": "Unsalted Butter", "category": "Dairy", "unit": "kg", "current": "5.600", "min": "2.000", "cost": "8.20", "expiry": today + timedelta(days=28)},
        {"sku": "ING-DAIR-004", "name": "Heavy Cream", "category": "Dairy", "unit": "L", "current": "4.800", "min": "2.000", "cost": "4.50", "expiry": today + timedelta(days=9)},
        # Meat
        {"sku": "ING-MEAT-001", "name": "Ground Beef (80/20)", "category": "Meat", "unit": "kg", "current": "18.200", "min": "8.000", "cost": "11.50", "expiry": today + timedelta(days=5)},
        {"sku": "ING-MEAT-002", "name": "Chicken Breast", "category": "Meat", "unit": "kg", "current": "16.000", "min": "7.000", "cost": "8.75", "expiry": today + timedelta(days=4)},
        {"sku": "ING-MEAT-003", "name": "Smoked Bacon", "category": "Meat", "unit": "kg", "current": "6.400", "min": "3.000", "cost": "12.00", "expiry": today + timedelta(days=14)},
        # Dry Goods
        {"sku": "ING-DRY-001", "name": "Brioche Burger Buns", "category": "Dry Goods", "unit": "pcs", "current": "74.000", "min": "30.000", "cost": "0.45", "expiry": today + timedelta(days=6)},
        {"sku": "ING-DRY-002", "name": "All-Purpose Flour", "category": "Dry Goods", "unit": "kg", "current": "45.000", "min": "15.000", "cost": "1.10", "expiry": today + timedelta(days=120)},
        {"sku": "ING-DRY-003", "name": "Extra Virgin Olive Oil", "category": "Dry Goods", "unit": "L", "current": "12.500", "min": "4.000", "cost": "9.20", "expiry": today + timedelta(days=180)},
        {"sku": "ING-DRY-004", "name": "Fettuccine Pasta", "category": "Dry Goods", "unit": "kg", "current": "28.000", "min": "10.000", "cost": "2.30", "expiry": today + timedelta(days=150)},
        {"sku": "ING-DRY-005", "name": "Sea Salt & Spices Blend", "category": "Dry Goods", "unit": "kg", "current": "9.200", "min": "2.000", "cost": "14.00", "expiry": today + timedelta(days=365)},
        # Beverages
        {"sku": "ING-BEV-001", "name": "Espresso Roast Coffee Beans", "category": "Beverages", "unit": "kg", "current": "10.500", "min": "4.000", "cost": "18.50", "expiry": today + timedelta(days=60)},
        {"sku": "ING-BEV-002", "name": "Cola Craft Syrup", "category": "Beverages", "unit": "L", "current": "18.000", "min": "5.000", "cost": "6.50", "expiry": today + timedelta(days=120)},
        {"sku": "ING-BEV-003", "name": "Earl Grey Tea Leaves", "category": "Beverages", "unit": "kg", "current": "3.800", "min": "1.500", "cost": "14.50", "expiry": today + timedelta(days=180)},
    ]

    ingredient_map: dict[str, Ingredient] = {}
    for item in ingredients_data:
        stmt = select(Ingredient).where(Ingredient.sku == item["sku"])
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing is None:
            ing = Ingredient(
                sku=item["sku"],
                name=item["name"],
                category=item["category"],
                unit=item["unit"],
                current_quantity=Decimal(item["current"]),
                min_quantity=Decimal(item["min"]),
                cost_per_unit=Decimal(item["cost"]),
                expiry_date=item["expiry"],
            )
            session.add(ing)
            await session.flush()
            ingredient_map[item["sku"]] = ing

            # Initial stock purchase transaction
            session.add(
                InventoryTransaction(
                    ingredient_id=ing.id,
                    transaction_type=TransactionType.PURCHASE.value,
                    quantity=Decimal(item["current"]),
                    notes=f"Initial stock balance intake for {item['name']}",
                    created_at=now - timedelta(days=7),
                )
            )
        else:
            ingredient_map[item["sku"]] = existing

    # ─────────────────────────────────────────────────────────────────
    # 2. MENU ITEMS
    # ─────────────────────────────────────────────────────────────────
    menu_items_data = [
        {"name": "Classic Cheeseburger", "price": "12.50", "desc": "Prime 80/20 beef patty, melted cheddar, roma tomato, iceberg lettuce on brioche bun.", "active": True},
        {"name": "Crispy Chicken Sandwich", "price": "11.00", "desc": "Hand-breaded chicken breast with fresh tomato and crisp lettuce on toasted brioche.", "active": True},
        {"name": "Loaded Bacon Fries", "price": "6.75", "desc": "Crispy russet fries smothered in melted cheddar cheese and smoked bacon crumbles.", "active": True},
        {"name": "Creamy Chicken Fettuccine", "price": "14.50", "desc": "Al dente fettuccine in a rich heavy cream and butter sauce with seared chicken breast.", "active": True},
        {"name": "Artisan Latte", "price": "4.50", "desc": "Double shot of rich espresso with steamed whole milk and velvety microfoam.", "active": True},
        {"name": "Fountain Craft Soda", "price": "3.00", "desc": "Refreshing craft soda made from premium real cane sugar syrup.", "active": True},
    ]

    menu_item_map: dict[str, MenuItem] = {}
    for item in menu_items_data:
        stmt = select(MenuItem).where(MenuItem.name == item["name"])
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing is None:
            m_item = MenuItem(
                name=item["name"],
                selling_price=Decimal(item["price"]),
                description=item["desc"],
                is_active=item["active"],
            )
            session.add(m_item)
            await session.flush()
            menu_item_map[item["name"]] = m_item
        else:
            menu_item_map[item["name"]] = existing

    # ─────────────────────────────────────────────────────────────────
    # 3. RECIPES (Menu Item -> Ingredient Consumption)
    # ─────────────────────────────────────────────────────────────────
    recipes = [
        # Classic Cheeseburger
        ("Classic Cheeseburger", "ING-MEAT-001", "0.180"),  # 180g beef
        ("Classic Cheeseburger", "ING-DRY-001", "1.000"),   # 1 bun
        ("Classic Cheeseburger", "ING-DAIR-001", "0.035"),  # 35g cheddar
        ("Classic Cheeseburger", "ING-PROD-001", "0.040"),  # 40g tomato
        ("Classic Cheeseburger", "ING-PROD-002", "0.025"),  # 25g lettuce
        # Crispy Chicken Sandwich
        ("Crispy Chicken Sandwich", "ING-MEAT-002", "0.160"), # 160g chicken
        ("Crispy Chicken Sandwich", "ING-DRY-001", "1.000"),   # 1 bun
        ("Crispy Chicken Sandwich", "ING-PROD-001", "0.030"),  # 30g tomato
        ("Crispy Chicken Sandwich", "ING-PROD-002", "0.025"),  # 25g lettuce
        # Loaded Bacon Fries
        ("Loaded Bacon Fries", "ING-PROD-004", "0.300"),       # 300g potatoes
        ("Loaded Bacon Fries", "ING-DAIR-001", "0.040"),       # 40g cheddar
        ("Loaded Bacon Fries", "ING-MEAT-003", "0.030"),       # 30g bacon
        # Creamy Chicken Fettuccine
        ("Creamy Chicken Fettuccine", "ING-DRY-004", "0.150"),  # 150g pasta
        ("Creamy Chicken Fettuccine", "ING-MEAT-002", "0.120"), # 120g chicken
        ("Creamy Chicken Fettuccine", "ING-DAIR-004", "0.080"), # 80ml heavy cream
        ("Creamy Chicken Fettuccine", "ING-DAIR-003", "0.020"), # 20g butter
        ("Creamy Chicken Fettuccine", "ING-DRY-003", "0.015"),  # 15ml olive oil
        # Artisan Latte
        ("Artisan Latte", "ING-BEV-001", "0.018"),             # 18g coffee
        ("Artisan Latte", "ING-DAIR-002", "0.180"),            # 180ml milk
        # Fountain Craft Soda
        ("Fountain Craft Soda", "ING-BEV-002", "0.050"),       # 50ml syrup
    ]

    for menu_name, ing_sku, qty in recipes:
        menu_obj = menu_item_map[menu_name]
        ing_obj = ingredient_map[ing_sku]

        stmt = select(RecipeIngredient).where(
            RecipeIngredient.menu_item_id == menu_obj.id,
            RecipeIngredient.ingredient_id == ing_obj.id,
        )
        result = await session.execute(stmt)
        if result.scalar_one_or_none() is None:
            session.add(
                RecipeIngredient(
                    menu_item_id=menu_obj.id,
                    ingredient_id=ing_obj.id,
                    quantity_required=Decimal(qty),
                )
            )

    await session.flush()

    # ─────────────────────────────────────────────────────────────────
    # 4. SAMPLE SALES (12 historical sales across past 3 days)
    # ─────────────────────────────────────────────────────────────────
    # Only seed sales if none exist
    sales_count_stmt = select(Sale)
    existing_sales = (await session.execute(sales_count_stmt)).scalars().first()

    if existing_sales is None:
        sales_schedule = [
            # Day -3
            (now - timedelta(days=3, hours=7), [("Classic Cheeseburger", 2), ("Fountain Craft Soda", 2)]),
            (now - timedelta(days=3, hours=5), [("Crispy Chicken Sandwich", 1), ("Loaded Bacon Fries", 1), ("Artisan Latte", 1)]),
            (now - timedelta(days=3, hours=2), [("Creamy Chicken Fettuccine", 2), ("Artisan Latte", 2)]),
            # Day -2
            (now - timedelta(days=2, hours=8), [("Classic Cheeseburger", 3), ("Loaded Bacon Fries", 2), ("Fountain Craft Soda", 3)]),
            (now - timedelta(days=2, hours=6), [("Crispy Chicken Sandwich", 2), ("Fountain Craft Soda", 2)]),
            (now - timedelta(days=2, hours=3), [("Creamy Chicken Fettuccine", 1), ("Artisan Latte", 1)]),
            (now - timedelta(days=2, hours=1), [("Classic Cheeseburger", 1), ("Loaded Bacon Fries", 1)]),
            # Day -1
            (now - timedelta(days=1, hours=7), [("Classic Cheeseburger", 4), ("Loaded Bacon Fries", 2), ("Fountain Craft Soda", 4)]),
            (now - timedelta(days=1, hours=5), [("Creamy Chicken Fettuccine", 3), ("Artisan Latte", 2)]),
            (now - timedelta(days=1, hours=2), [("Crispy Chicken Sandwich", 2), ("Loaded Bacon Fries", 1)]),
            # Today
            (now - timedelta(hours=4), [("Classic Cheeseburger", 2), ("Artisan Latte", 2)]),
            (now - timedelta(hours=1), [("Crispy Chicken Sandwich", 1), ("Fountain Craft Soda", 1)]),
        ]

        for sold_time, items_list in sales_schedule:
            total_sale = Decimal("0.00")
            sale_items_to_add: list[SaleItem] = []

            for item_name, count in items_list:
                m_obj = menu_item_map[item_name]
                subtotal = m_obj.selling_price * count
                total_sale += subtotal
                sale_items_to_add.append(
                    SaleItem(
                        menu_item_id=m_obj.id,
                        quantity=count,
                        unit_price=m_obj.selling_price,
                        subtotal=subtotal,
                    )
                )

            sale = Sale(total_amount=total_sale, sold_at=sold_time, created_at=sold_time)
            session.add(sale)
            await session.flush()

            for s_item in sale_items_to_add:
                s_item.sale_id = sale.id
                session.add(s_item)

            # Record inventory consumption audit transaction
            for item_name, count in items_list:
                m_obj = menu_item_map[item_name]
                recipe_stmt = select(RecipeIngredient).where(RecipeIngredient.menu_item_id == m_obj.id)
                r_rows = (await session.execute(recipe_stmt)).scalars().all()
                for r in r_rows:
                    consumed = r.quantity_required * count
                    session.add(
                        InventoryTransaction(
                            ingredient_id=r.ingredient_id,
                            transaction_type=TransactionType.SALE_CONSUMPTION.value,
                            quantity=consumed,
                            notes=f"Sold {count}x {m_obj.name} (Sale #{sale.id})",
                            created_at=sold_time,
                        )
                    )

    # ─────────────────────────────────────────────────────────────────
    # 5. PROCUREMENT RECOMMENDATION
    # ─────────────────────────────────────────────────────────────────
    rec_check = await session.execute(select(ProcurementRecommendation))
    if rec_check.scalars().first() is None:
        rec = ProcurementRecommendation(
            status=RecommendationStatus.PENDING.value,
            total_estimated_cost=Decimal("184.50"),
            reason="Automated daily stock check: Chicken Breast and Brioche Buns are below safe weekend operating thresholds.",
            created_at=now - timedelta(hours=6),
        )
        session.add(rec)
        await session.flush()

        rec_items = [
            (ingredient_map["ING-MEAT-002"].id, Decimal("10.000"), Decimal("8.75"), Decimal("87.50")),
            (ingredient_map["ING-DRY-001"].id, Decimal("50.000"), Decimal("0.45"), Decimal("22.50")),
            (ingredient_map["ING-DAIR-001"].id, Decimal("5.000"), Decimal("9.50"), Decimal("47.50")),
            (ingredient_map["ING-PROD-001"].id, Decimal("10.800"), Decimal("2.50"), Decimal("27.00")),
        ]
        for ing_id, qty, unit_cost, total_cost in rec_items:
            session.add(
                ProcurementRecommendationItem(
                    recommendation_id=rec.id,
                    ingredient_id=ing_id,
                    recommended_quantity=qty,
                    estimated_unit_cost=unit_cost,
                    estimated_total_cost=total_cost,
                )
            )

    # ─────────────────────────────────────────────────────────────────
    # 6. AUTOMATION LOGS
    # ─────────────────────────────────────────────────────────────────
    log_check = await session.execute(select(AutomationLog))
    if log_check.scalars().first() is None:
        logs = [
            AutomationLog(
                task_name="daily_inventory_threshold_check",
                status=AutomationStatus.SUCCESS.value,
                message="Checked 19 ingredients: 2 low stock flags detected, 1 procurement draft generated.",
                started_at=now - timedelta(hours=6, minutes=2),
                completed_at=now - timedelta(hours=6),
            ),
            AutomationLog(
                task_name="daily_sales_consumption_sync",
                status=AutomationStatus.SUCCESS.value,
                message="Synchronized 12 sales records; calculated ingredient depletion across 20 recipe mappings.",
                started_at=now - timedelta(hours=1, minutes=1),
                completed_at=now - timedelta(hours=1),
            ),
        ]
        session.add_all(logs)

    await session.commit()
    print(" Database successfully seeded with restaurant operations data.")


async def main() -> None:
    async with AsyncSessionLocal() as session:
        await seed_data(session)


if __name__ == "__main__":
    asyncio.run(main())
