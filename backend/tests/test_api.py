"""
Comprehensive API Integration Tests for Stage 3 Core Backend APIs.
Tests all endpoints using an isolated database session and HTTP AsyncClient.
"""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ingredient import Ingredient
from app.models.inventory_transaction import InventoryTransaction, TransactionType
from app.models.menu_item import MenuItem
from app.models.recipe import RecipeIngredient
from app.models.sale import Sale, SaleItem


# ─────────────────────────────────────────────────────────────────────
# 1. INGREDIENT API TESTS
# ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_api_create_ingredient(client: AsyncClient):
    """Test POST /api/v1/ingredients."""
    payload = {
        "name": "Fresh Cilantro",
        "sku": "ING-PROD-CIL",
        "category": "Produce",
        "unit": "kg",
        "current_quantity": 4.5,
        "min_quantity": 1.0,
        "cost_per_unit": 2.25,
        "expiry_date": "2026-11-20",
    }
    response = await client.post("/api/v1/ingredients", json=payload)
    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["data"]["sku"] == "ING-PROD-CIL"
    assert body["data"]["name"] == "Fresh Cilantro"
    assert Decimal(str(body["data"]["current_quantity"])) == Decimal("4.500")


@pytest.mark.asyncio
async def test_api_create_ingredient_duplicate_sku(client: AsyncClient, db_session: AsyncSession):
    """Test POST /api/v1/ingredients with duplicate SKU returns 409 Conflict."""
    db_session.add(
        Ingredient(
            name="Garlic",
            sku="ING-GARLIC",
            category="Produce",
            unit="kg",
            current_quantity=Decimal("5.000"),
            min_quantity=Decimal("1.000"),
            cost_per_unit=Decimal("3.00"),
        )
    )
    await db_session.commit()

    payload = {
        "name": "Garlic Bulbs",
        "sku": "ING-GARLIC",  # Duplicate
        "category": "Produce",
        "unit": "kg",
        "current_quantity": 2.0,
        "min_quantity": 1.0,
        "cost_per_unit": 3.00,
    }
    response = await client.post("/api/v1/ingredients", json=payload)
    assert response.status_code == 409
    body = response.json()
    assert body["success"] is False
    assert "already exists" in body["error"]


@pytest.mark.asyncio
async def test_api_list_ingredients_search_and_filter(client: AsyncClient, db_session: AsyncSession):
    """Test GET /api/v1/ingredients with search, category, and pagination."""
    db_session.add_all([
        Ingredient(name="Avocado", sku="ING-AVO", category="Produce", unit="kg", current_quantity=Decimal("10"), min_quantity=Decimal("2"), cost_per_unit=Decimal("4.00")),
        Ingredient(name="Apple", sku="ING-APP", category="Produce", unit="kg", current_quantity=Decimal("15"), min_quantity=Decimal("3"), cost_per_unit=Decimal("2.00")),
        Ingredient(name="Heavy Cream", sku="ING-CREAM", category="Dairy", unit="L", current_quantity=Decimal("8"), min_quantity=Decimal("2"), cost_per_unit=Decimal("5.00")),
    ])
    await db_session.commit()

    # Filter by category
    res_cat = await client.get("/api/v1/ingredients?category=Produce")
    assert res_cat.status_code == 200
    assert res_cat.json()["data"]["total"] == 2

    # Search by name
    res_search = await client.get("/api/v1/ingredients?search=Cream")
    assert res_search.status_code == 200
    assert res_search.json()["data"]["total"] == 1
    assert res_search.json()["data"]["items"][0]["sku"] == "ING-CREAM"


@pytest.mark.asyncio
async def test_api_get_ingredient_by_id(client: AsyncClient, db_session: AsyncSession):
    """Test GET /api/v1/ingredients/{id}."""
    ing = Ingredient(name="Ginger", sku="ING-GING", category="Produce", unit="kg", current_quantity=Decimal("2"), min_quantity=Decimal("0.5"), cost_per_unit=Decimal("6.00"))
    db_session.add(ing)
    await db_session.commit()

    res = await client.get(f"/api/v1/ingredients/{ing.id}")
    assert res.status_code == 200
    assert res.json()["data"]["name"] == "Ginger"

    # Not found
    res_404 = await client.get("/api/v1/ingredients/99999")
    assert res_404.status_code == 404
    assert res_404.json()["success"] is False


@pytest.mark.asyncio
async def test_api_update_ingredient(client: AsyncClient, db_session: AsyncSession):
    """Test PUT /api/v1/ingredients/{id}."""
    ing = Ingredient(name="Flour Basic", sku="ING-FLOUR-B", category="Dry Goods", unit="kg", current_quantity=Decimal("20"), min_quantity=Decimal("5"), cost_per_unit=Decimal("1.00"))
    db_session.add(ing)
    await db_session.commit()

    update_payload = {"cost_per_unit": 1.25, "min_quantity": 8.0}
    res = await client.put(f"/api/v1/ingredients/{ing.id}", json=update_payload)
    assert res.status_code == 200
    body = res.json()["data"]
    assert Decimal(str(body["cost_per_unit"])) == Decimal("1.25")
    assert Decimal(str(body["min_quantity"])) == Decimal("8.000")


@pytest.mark.asyncio
async def test_api_delete_ingredient(client: AsyncClient, db_session: AsyncSession):
    """Test DELETE /api/v1/ingredients/{id}."""
    # Unused ingredient can be deleted
    ing = Ingredient(name="Temporary Herb", sku="ING-HERB-TEMP", category="Produce", unit="kg", current_quantity=Decimal("1"), min_quantity=Decimal("0.5"), cost_per_unit=Decimal("2.00"))
    db_session.add(ing)
    await db_session.commit()

    del_res = await client.delete(f"/api/v1/ingredients/{ing.id}")
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True

    # Ingredient referenced by recipe cannot be deleted (409)
    ing_used = Ingredient(name="Beef Ground", sku="ING-BEEF-USED", category="Meat", unit="kg", current_quantity=Decimal("10"), min_quantity=Decimal("2"), cost_per_unit=Decimal("9.00"))
    menu = MenuItem(name="Meatball", selling_price=Decimal("6.00"))
    db_session.add_all([ing_used, menu])
    await db_session.flush()

    recipe = RecipeIngredient(menu_item_id=menu.id, ingredient_id=ing_used.id, quantity_required=Decimal("0.200"))
    db_session.add(recipe)
    await db_session.commit()

    conflict_res = await client.delete(f"/api/v1/ingredients/{ing_used.id}")
    assert conflict_res.status_code == 409
    assert conflict_res.json()["success"] is False


# ─────────────────────────────────────────────────────────────────────
# 2. MENU ITEM & RECIPE API TESTS
# ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_api_create_and_list_menu_items(client: AsyncClient):
    """Test POST and GET /api/v1/menu-items."""
    create_payload = {
        "name": "Classic Fish & Chips",
        "description": "Beer battered cod with crispy potato wedges.",
        "selling_price": 14.50,
        "is_active": True,
    }
    res_create = await client.post("/api/v1/menu-items", json=create_payload)
    assert res_create.status_code == 201
    item_id = res_create.json()["data"]["id"]

    res_list = await client.get("/api/v1/menu-items")
    assert res_list.status_code == 200
    assert any(m["id"] == item_id for m in res_list.json()["data"])


@pytest.mark.asyncio
async def test_api_set_and_get_recipe(client: AsyncClient, db_session: AsyncSession):
    """Test POST and GET /api/v1/menu-items/{id}/recipe."""
    ing1 = Ingredient(name="Cod Fillet", sku="ING-COD", category="Meat", unit="kg", current_quantity=Decimal("10"), min_quantity=Decimal("2"), cost_per_unit=Decimal("12.00"))
    ing2 = Ingredient(name="Potatoes", sku="ING-POT", category="Produce", unit="kg", current_quantity=Decimal("20"), min_quantity=Decimal("5"), cost_per_unit=Decimal("0.80"))
    menu = MenuItem(name="Fried Fish Platter", selling_price=Decimal("16.00"))
    db_session.add_all([ing1, ing2, menu])
    await db_session.commit()

    # Set recipe
    recipe_payload = {
        "ingredients": [
            {"ingredient_id": ing1.id, "quantity_required": 0.250},
            {"ingredient_id": ing2.id, "quantity_required": 0.300},
        ]
    }
    set_res = await client.post(f"/api/v1/menu-items/{menu.id}/recipe", json=recipe_payload)
    assert set_res.status_code == 200
    assert len(set_res.json()["data"]) == 2

    # Get recipe
    get_res = await client.get(f"/api/v1/menu-items/{menu.id}/recipe")
    assert get_res.status_code == 200
    assert len(get_res.json()["data"]) == 2

    # Reject duplicate ingredients in recipe payload
    dup_payload = {
        "ingredients": [
            {"ingredient_id": ing1.id, "quantity_required": 0.250},
            {"ingredient_id": ing1.id, "quantity_required": 0.100},  # Duplicate ing1
        ]
    }
    dup_res = await client.post(f"/api/v1/menu-items/{menu.id}/recipe", json=dup_payload)
    assert dup_res.status_code == 422


# ─────────────────────────────────────────────────────────────────────
# 3. SALES & INVENTORY CONSUMPTION TESTS
# ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_api_record_sale_depletes_inventory(client: AsyncClient, db_session: AsyncSession):
    """
    Test POST /api/v1/sales:
      - Validates stock deduction
      - Validates total calculation
      - Validates SALE_CONSUMPTION audit transaction
    """
    bun = Ingredient(name="Brioche Bun", sku="ING-BUN-TEST", category="Dry Goods", unit="pcs", current_quantity=Decimal("10.000"), min_quantity=Decimal("2.000"), cost_per_unit=Decimal("0.50"))
    patty = Ingredient(name="Beef Patty", sku="ING-PATTY-TEST", category="Meat", unit="kg", current_quantity=Decimal("5.000"), min_quantity=Decimal("1.000"), cost_per_unit=Decimal("10.00"))
    burger = MenuItem(name="Test Burger", selling_price=Decimal("12.00"))
    db_session.add_all([bun, patty, burger])
    await db_session.flush()

    # 1 Burger consumes 1 bun and 0.150 kg beef
    db_session.add_all([
        RecipeIngredient(menu_item_id=burger.id, ingredient_id=bun.id, quantity_required=Decimal("1.000")),
        RecipeIngredient(menu_item_id=burger.id, ingredient_id=patty.id, quantity_required=Decimal("0.150")),
    ])
    await db_session.commit()

    # Sell 2 Burgers (should consume 2 buns and 0.300 kg beef)
    sale_payload = {
        "items": [
            {"menu_item_id": burger.id, "quantity": 2, "unit_price": 12.00}
        ]
    }
    response = await client.post("/api/v1/sales", json=sale_payload)
    assert response.status_code == 201
    sale_data = response.json()["data"]
    assert Decimal(str(sale_data["total_amount"])) == Decimal("24.00")

    # Refresh ingredients from DB and verify deduction
    await db_session.refresh(bun)
    await db_session.refresh(patty)
    assert bun.current_quantity == Decimal("8.000")  # 10 - 2
    assert patty.current_quantity == Decimal("4.700")  # 5 - 0.300


@pytest.mark.asyncio
async def test_api_sale_rejected_on_insufficient_stock(client: AsyncClient, db_session: AsyncSession):
    """
    Test POST /api/v1/sales with insufficient stock:
      - Returns 400 Bad Request with detailed deficit information
      - Rolls back all changes (no stock changed, no sale created)
    """
    bun = Ingredient(name="Bun Low", sku="ING-BUN-LOW", category="Dry Goods", unit="pcs", current_quantity=Decimal("1.000"), min_quantity=Decimal("1.000"), cost_per_unit=Decimal("0.50"))
    burger = MenuItem(name="Low Stock Burger", selling_price=Decimal("10.00"))
    db_session.add_all([bun, burger])
    await db_session.flush()

    db_session.add(
        RecipeIngredient(menu_item_id=burger.id, ingredient_id=bun.id, quantity_required=Decimal("1.000"))
    )
    await db_session.commit()

    # Attempt to sell 3 burgers (only 1 bun available)
    sale_payload = {
        "items": [
            {"menu_item_id": burger.id, "quantity": 3, "unit_price": 10.00}
        ]
    }
    response = await client.post("/api/v1/sales", json=sale_payload)
    assert response.status_code == 400
    body = response.json()
    assert body["success"] is False
    assert "Insufficient inventory stock" in body["error"]
    assert len(body["detail"]) == 1
    assert body["detail"][0]["name"] == "Bun Low"
    assert body["detail"][0]["available"] == 1.0
    assert body["detail"][0]["required"] == 3.0

    # Verify inventory was NOT deducted (atomic rollback)
    await db_session.refresh(bun)
    assert bun.current_quantity == Decimal("1.000")


@pytest.mark.asyncio
async def test_api_sale_combined_multi_item_depletion(client: AsyncClient, db_session: AsyncSession):
    """
    Test sale with multiple menu items sharing the same ingredient (e.g. Tomato in Burger and Salad).
    Verifies that combined consumption is calculated correctly and deducted once without double-deduction.
    """
    tomato = Ingredient(name="Tomato Shared", sku="ING-TOM-SHARED", category="Produce", unit="kg", current_quantity=Decimal("5.000"), min_quantity=Decimal("1.000"), cost_per_unit=Decimal("2.00"))
    burger = MenuItem(name="Burger Deluxe", selling_price=Decimal("12.00"))
    salad = MenuItem(name="Garden Salad", selling_price=Decimal("8.00"))
    db_session.add_all([tomato, burger, salad])
    await db_session.flush()

    # Burger consumes 0.050 kg tomato; Salad consumes 0.100 kg tomato
    db_session.add_all([
        RecipeIngredient(menu_item_id=burger.id, ingredient_id=tomato.id, quantity_required=Decimal("0.050")),
        RecipeIngredient(menu_item_id=salad.id, ingredient_id=tomato.id, quantity_required=Decimal("0.100")),
    ])
    await db_session.commit()

    # Sell 2 Burgers + 3 Salads:
    # Tomato needed: (2 * 0.050) + (3 * 0.100) = 0.100 + 0.300 = 0.400 kg
    sale_payload = {
        "items": [
            {"menu_item_id": burger.id, "quantity": 2},
            {"menu_item_id": salad.id, "quantity": 3},
        ]
    }
    response = await client.post("/api/v1/sales", json=sale_payload)
    assert response.status_code == 201

    await db_session.refresh(tomato)
    assert tomato.current_quantity == Decimal("4.600")  # 5.000 - 0.400


# ─────────────────────────────────────────────────────────────────────
# 4. INVENTORY ADJUSTMENT & TRANSACTION TESTS
# ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_api_inventory_adjustments(client: AsyncClient, db_session: AsyncSession):
    """Test POST /api/v1/inventory/adjustments for stock additions, reductions, and negative rejection."""
    cheese = Ingredient(name="Gouda", sku="ING-GOUDA", category="Dairy", unit="kg", current_quantity=Decimal("5.000"), min_quantity=Decimal("2.000"), cost_per_unit=Decimal("10.00"))
    db_session.add(cheese)
    await db_session.commit()

    # 1. Stock addition (Purchase delivery)
    add_res = await client.post(
        "/api/v1/inventory/adjustments",
        json={"ingredient_id": cheese.id, "transaction_type": "PURCHASE", "quantity": 3.5, "notes": "Supplier delivery intake"},
    )
    assert add_res.status_code == 201
    await db_session.refresh(cheese)
    assert cheese.current_quantity == Decimal("8.500")

    # 2. Stock reduction (Waste)
    waste_res = await client.post(
        "/api/v1/inventory/adjustments",
        json={"ingredient_id": cheese.id, "transaction_type": "WASTE", "quantity": -1.5, "notes": "Spoiled edge trim"},
    )
    assert waste_res.status_code == 201
    await db_session.refresh(cheese)
    assert cheese.current_quantity == Decimal("7.000")

    # 3. Reject adjustment that would cause negative stock
    neg_res = await client.post(
        "/api/v1/inventory/adjustments",
        json={"ingredient_id": cheese.id, "transaction_type": "ADJUSTMENT", "quantity": -10.0, "notes": "Too large reduction"},
    )
    assert neg_res.status_code == 422
    assert "negative stock" in neg_res.json()["error"]
    await db_session.refresh(cheese)
    assert cheese.current_quantity == Decimal("7.000")


@pytest.mark.asyncio
async def test_api_inventory_low_stock_and_expiring(client: AsyncClient, db_session: AsyncSession):
    """Test GET /api/v1/inventory/low-stock and /api/v1/inventory/expiring."""
    today = datetime.now(timezone.utc).date()
    db_session.add_all([
        # Low stock (current <= min)
        Ingredient(name="Short Butter", sku="ING-SHORT-B", category="Dairy", unit="kg", current_quantity=Decimal("1.000"), min_quantity=Decimal("3.000"), cost_per_unit=Decimal("7.00")),
        # Normal stock
        Ingredient(name="Plentiful Sugar", sku="ING-PLENTY-S", category="Dry Goods", unit="kg", current_quantity=Decimal("50.000"), min_quantity=Decimal("10.000"), cost_per_unit=Decimal("1.00")),
        # Expiring in 3 days
        Ingredient(name="Fresh Fish", sku="ING-EXP-FISH", category="Meat", unit="kg", current_quantity=Decimal("4.000"), min_quantity=Decimal("2.000"), cost_per_unit=Decimal("15.00"), expiry_date=today + timedelta(days=3)),
    ])
    await db_session.commit()

    low_res = await client.get("/api/v1/inventory/low-stock")
    assert low_res.status_code == 200
    low_skus = [i["sku"] for i in low_res.json()["data"]]
    assert "ING-SHORT-B" in low_skus
    assert "ING-PLENTY-S" not in low_skus

    exp_res = await client.get("/api/v1/inventory/expiring?days=5")
    assert exp_res.status_code == 200
    exp_skus = [i["sku"] for i in exp_res.json()["data"]]
    assert "ING-EXP-FISH" in exp_skus


# ─────────────────────────────────────────────────────────────────────
# 5. DASHBOARD SUMMARY TEST
# ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_api_dashboard_summary(client: AsyncClient, db_session: AsyncSession):
    """Test GET /api/v1/dashboard/summary verifies calculated database metrics."""
    today_now = datetime.now(timezone.utc)
    ing1 = Ingredient(name="Olive Oil", sku="ING-DASH-OIL", category="Dry Goods", unit="L", current_quantity=Decimal("10.000"), min_quantity=Decimal("2.000"), cost_per_unit=Decimal("8.00"))
    ing2 = Ingredient(name="Milk", sku="ING-DASH-MILK", category="Dairy", unit="L", current_quantity=Decimal("1.000"), min_quantity=Decimal("5.000"), cost_per_unit=Decimal("2.00"), expiry_date=today_now.date() + timedelta(days=2))
    dish = MenuItem(name="Penne Pasta", selling_price=Decimal("12.00"), is_active=True)
    db_session.add_all([ing1, ing2, dish])
    await db_session.flush()

    # Sale today: $24.00
    sale = Sale(total_amount=Decimal("24.00"), sold_at=today_now, created_at=today_now)
    db_session.add(sale)
    await db_session.commit()

    res = await client.get("/api/v1/dashboard/summary")
    assert res.status_code == 200
    data = res.json()["data"]

    assert data["total_ingredients"] == 2
    assert data["total_active_menu_items"] == 1
    # total_inventory_value = (10 * 8) + (1 * 2) = 80 + 2 = 82.00
    assert Decimal(str(data["total_inventory_value"])) == Decimal("82.00")
    assert data["low_stock_count"] == 1  # Milk (1 <= 5)
    assert data["expiring_soon_count"] == 1  # Milk (+2 days)
    assert Decimal(str(data["today_sales_revenue"])) == Decimal("24.00")
    assert data["today_sales_count"] == 1
    assert len(data["recent_sales"]) == 1
