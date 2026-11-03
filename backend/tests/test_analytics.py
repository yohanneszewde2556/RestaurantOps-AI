"""
Integration Tests for Analytics Endpoints:
  - GET /api/v1/analytics/consumption
  - GET /api/v1/analytics/popular-items
  - GET /api/v1/analytics/food-cost
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ingredient import Ingredient
from app.models.inventory_transaction import InventoryTransaction, TransactionType
from app.models.menu_item import MenuItem
from app.models.recipe import RecipeIngredient
from app.models.sale import Sale, SaleItem


@pytest.mark.asyncio
async def test_analytics_empty_database(client: AsyncClient):
    """Verify that all analytics endpoints handle an empty database gracefully without crashing."""
    # 1. Consumption
    resp1 = await client.get("/api/v1/analytics/consumption")
    assert resp1.status_code == 200
    body1 = resp1.json()
    assert body1["success"] is True
    assert Decimal(str(body1["data"]["summary"]["today"])) == Decimal("0.000")
    assert body1["data"]["top_consumed"] == []
    assert body1["data"]["daily_trends"] == []

    # 2. Popular items
    resp2 = await client.get("/api/v1/analytics/popular-items")
    assert resp2.status_code == 200
    body2 = resp2.json()
    assert body2["success"] is True
    assert body2["data"]["total_items_sold"] == 0
    assert Decimal(str(body2["data"]["total_revenue"])) == Decimal("0.00")
    assert body2["data"]["items"] == []

    # 3. Food cost
    resp3 = await client.get("/api/v1/analytics/food-cost")
    assert resp3.status_code == 200
    body3 = resp3.json()
    assert body3["success"] is True
    assert body3["data"]["total_menu_items"] == 0
    assert body3["data"]["items_with_recipes"] == 0
    assert body3["data"]["average_food_cost_percentage"] is None
    assert body3["data"]["items"] == []


@pytest.mark.asyncio
async def test_analytics_consumption_calculations_and_trends(
    client: AsyncClient, db_session: AsyncSession
):
    """Test ingredient consumption aggregation, today vs 7d vs 30d periods, and daily trends."""
    now = datetime.now(timezone.utc)

    # Create ingredients
    beef = Ingredient(
        name="Ground Beef",
        sku="ING-BEEF-TEST",
        category="Meat",
        unit="kg",
        current_quantity=Decimal("20.000"),
        min_quantity=Decimal("5.000"),
        cost_per_unit=Decimal("10.00"),
    )
    buns = Ingredient(
        name="Burger Buns",
        sku="ING-BUNS-TEST",
        category="Bakery",
        unit="pcs",
        current_quantity=Decimal("50.000"),
        min_quantity=Decimal("10.000"),
        cost_per_unit=Decimal("0.50"),
    )
    db_session.add_all([beef, buns])
    await db_session.flush()

    # Record consumption transactions across various days
    # Today: 2.0 kg beef, 10 buns
    tx1 = InventoryTransaction(
        ingredient_id=beef.id,
        transaction_type=TransactionType.SALE_CONSUMPTION.value,
        quantity=Decimal("2.000"),
        created_at=now,
    )
    tx2 = InventoryTransaction(
        ingredient_id=buns.id,
        transaction_type=TransactionType.SALE_CONSUMPTION.value,
        quantity=Decimal("10.000"),
        created_at=now,
    )
    # 3 days ago: 3.0 kg beef, 15 buns
    tx3 = InventoryTransaction(
        ingredient_id=beef.id,
        transaction_type=TransactionType.SALE_CONSUMPTION.value,
        quantity=Decimal("3.000"),
        created_at=now - timedelta(days=3),
    )
    tx4 = InventoryTransaction(
        ingredient_id=buns.id,
        transaction_type=TransactionType.SALE_CONSUMPTION.value,
        quantity=Decimal("15.000"),
        created_at=now - timedelta(days=3),
    )
    # 15 days ago: 5.0 kg beef
    tx5 = InventoryTransaction(
        ingredient_id=beef.id,
        transaction_type=TransactionType.SALE_CONSUMPTION.value,
        quantity=Decimal("5.000"),
        created_at=now - timedelta(days=15),
    )
    # Non-consumption transaction (e.g. PURCHASE) should be excluded
    tx_purch = InventoryTransaction(
        ingredient_id=beef.id,
        transaction_type=TransactionType.PURCHASE.value,
        quantity=Decimal("50.000"),
        created_at=now,
    )

    db_session.add_all([tx1, tx2, tx3, tx4, tx5, tx_purch])
    await db_session.commit()

    # Query endpoint
    resp = await client.get("/api/v1/analytics/consumption")
    assert resp.status_code == 200
    data = resp.json()["data"]

    # Verify summary:
    # Today total: 2.0 + 10.0 = 12.0
    assert Decimal(str(data["summary"]["today"])) == Decimal("12.000")
    # Last 7 days total: today (12.0) + 3 days ago (3.0 + 15.0 = 18.0) = 30.0
    assert Decimal(str(data["summary"]["last_7_days"])) == Decimal("30.000")
    # Last 30 days total: 30.0 + 15 days ago (5.0) = 35.0
    assert Decimal(str(data["summary"]["last_30_days"])) == Decimal("35.000")

    # Verify top consumed ingredients
    top = data["top_consumed"]
    assert len(top) == 2
    # Buns total: 25 pcs
    # Beef total: 10 kg
    buns_entry = next(i for i in top if i["sku"] == "ING-BUNS-TEST")
    beef_entry = next(i for i in top if i["sku"] == "ING-BEEF-TEST")

    assert Decimal(str(buns_entry["total_consumed"])) == Decimal("25.000")
    assert Decimal(str(buns_entry["total_cost"])) == Decimal("12.50") # 25 * 0.50

    assert Decimal(str(beef_entry["total_consumed"])) == Decimal("10.000")
    assert Decimal(str(beef_entry["total_cost"])) == Decimal("100.00") # 10 * 10.00

    # Daily trends should have at least 3 distinct date buckets
    assert len(data["daily_trends"]) == 3


@pytest.mark.asyncio
async def test_analytics_consumption_date_range_filtering(
    client: AsyncClient, db_session: AsyncSession
):
    """Test date-range filtering on consumption analytics."""
    now = datetime.now(timezone.utc)
    milk = Ingredient(
        name="Whole Milk",
        sku="ING-MILK-TEST",
        category="Dairy",
        unit="L",
        current_quantity=Decimal("30.000"),
        min_quantity=Decimal("5.000"),
        cost_per_unit=Decimal("2.00"),
    )
    db_session.add(milk)
    await db_session.flush()

    # 10 days ago: 5 L
    tx_old = InventoryTransaction(
        ingredient_id=milk.id,
        transaction_type=TransactionType.SALE_CONSUMPTION.value,
        quantity=Decimal("5.000"),
        created_at=now - timedelta(days=10),
    )
    # Yesterday: 8 L
    tx_recent = InventoryTransaction(
        ingredient_id=milk.id,
        transaction_type=TransactionType.SALE_CONSUMPTION.value,
        quantity=Decimal("8.000"),
        created_at=now - timedelta(days=1),
    )
    db_session.add_all([tx_old, tx_recent])
    await db_session.commit()

    # Filter to only last 3 days
    start = (now - timedelta(days=3)).isoformat()
    end = now.isoformat()
    resp = await client.get(f"/api/v1/analytics/consumption?start_date={start}&end_date={end}")
    assert resp.status_code == 200
    data = resp.json()["data"]

    # Only tx_recent (8 L) should be in top_consumed
    assert len(data["top_consumed"]) == 1
    assert Decimal(str(data["top_consumed"][0]["total_consumed"])) == Decimal("8.000")
    assert len(data["daily_trends"]) == 1


@pytest.mark.asyncio
async def test_analytics_popular_items_and_revenue(
    client: AsyncClient, db_session: AsyncSession
):
    """Test ranking of popular items, quantities sold, revenue, and revenue percentages."""
    now = datetime.now(timezone.utc)

    item_burger = MenuItem(name="Burger Deluxe", selling_price=Decimal("12.00"), is_active=True)
    item_fries = MenuItem(name="Crispy Fries", selling_price=Decimal("5.00"), is_active=True)
    item_shake = MenuItem(name="Vanilla Shake", selling_price=Decimal("6.00"), is_active=True)
    db_session.add_all([item_burger, item_fries, item_shake])
    await db_session.flush()

    # Sale 1: 3 Burgers, 2 Fries -> 3*12 + 2*5 = 36 + 10 = $46
    s1 = Sale(total_amount=Decimal("46.00"), sold_at=now - timedelta(days=2))
    db_session.add(s1)
    await db_session.flush()
    db_session.add_all([
        SaleItem(sale_id=s1.id, menu_item_id=item_burger.id, quantity=3, unit_price=Decimal("12.00"), subtotal=Decimal("36.00")),
        SaleItem(sale_id=s1.id, menu_item_id=item_fries.id, quantity=2, unit_price=Decimal("5.00"), subtotal=Decimal("10.00")),
    ])

    # Sale 2: 2 Burgers, 4 Fries -> 2*12 + 4*5 = 24 + 20 = $44
    s2 = Sale(total_amount=Decimal("44.00"), sold_at=now - timedelta(days=1))
    db_session.add(s2)
    await db_session.flush()
    db_session.add_all([
        SaleItem(sale_id=s2.id, menu_item_id=item_burger.id, quantity=2, unit_price=Decimal("12.00"), subtotal=Decimal("24.00")),
        SaleItem(sale_id=s2.id, menu_item_id=item_fries.id, quantity=4, unit_price=Decimal("5.00"), subtotal=Decimal("20.00")),
    ])

    await db_session.commit()

    resp = await client.get("/api/v1/analytics/popular-items")
    assert resp.status_code == 200
    data = resp.json()["data"]

    # Overall:
    # Fries: 6 sold, $30 revenue
    # Burger: 5 sold, $60 revenue
    # Total revenue = $90
    assert Decimal(str(data["total_revenue"])) == Decimal("90.00")
    assert data["total_items_sold"] == 11
    assert len(data["items"]) == 2 # shake was never sold

    # Fries should be #1 by quantity sold (6 > 5)
    assert data["items"][0]["name"] == "Crispy Fries"
    assert data["items"][0]["total_quantity_sold"] == 6
    assert Decimal(str(data["items"][0]["total_revenue"])) == Decimal("30.00")
    # Revenue percentage: 30 / 90 * 100 = 33.33%
    assert Decimal(str(data["items"][0]["revenue_percentage"])) == Decimal("33.33")

    # Burger should be #2 by quantity sold (5), but higher revenue ($60, 66.67%)
    assert data["items"][1]["name"] == "Burger Deluxe"
    assert data["items"][1]["total_quantity_sold"] == 5
    assert Decimal(str(data["items"][1]["total_revenue"])) == Decimal("60.00")
    assert Decimal(str(data["items"][1]["revenue_percentage"])) == Decimal("66.67")


@pytest.mark.asyncio
async def test_analytics_food_cost_and_profitability(
    client: AsyncClient, db_session: AsyncSession
):
    """
    Test recipe food cost calculation, food cost percentage, gross margin,
    safe handling of missing recipes and zero price items.
    """
    # 1. Ingredients
    pasta = Ingredient(name="Pasta", sku="ING-PST", category="Dry", unit="kg", current_quantity=Decimal("10"), min_quantity=Decimal("2"), cost_per_unit=Decimal("4.00"))
    sauce = Ingredient(name="Truffle Sauce", sku="ING-TRF", category="Dry", unit="kg", current_quantity=Decimal("10"), min_quantity=Decimal("2"), cost_per_unit=Decimal("20.00"))
    db_session.add_all([pasta, sauce])
    await db_session.flush()

    # 2. Menu Item with recipe: Truffle Pasta ($25.00)
    # Recipe: 0.200 kg pasta (0.2 * 4.00 = 0.80) + 0.100 kg sauce (0.1 * 20.00 = 2.00) = Total Cost: $2.80
    # Food cost % = 2.80 / 25.00 * 100 = 11.20%
    # Gross contribution = 25.00 - 2.80 = $22.20 (88.80% margin)
    m_pasta = MenuItem(name="Truffle Pasta", selling_price=Decimal("25.00"), is_active=True)
    db_session.add(m_pasta)
    await db_session.flush()

    db_session.add_all([
        RecipeIngredient(menu_item_id=m_pasta.id, ingredient_id=pasta.id, quantity_required=Decimal("0.200")),
        RecipeIngredient(menu_item_id=m_pasta.id, ingredient_id=sauce.id, quantity_required=Decimal("0.100")),
    ])

    # 3. Menu Item WITHOUT recipe: "Secret Special" ($15.00)
    m_no_recipe = MenuItem(name="Secret Special", selling_price=Decimal("15.00"), is_active=True)
    # 4. Menu Item with ZERO price: "Complimentary Bread" ($0.00)
    m_zero_price = MenuItem(name="Complimentary Bread", selling_price=Decimal("0.00"), is_active=True)

    db_session.add_all([m_no_recipe, m_zero_price])
    await db_session.commit()

    resp = await client.get("/api/v1/analytics/food-cost")
    assert resp.status_code == 200
    data = resp.json()["data"]

    assert data["total_menu_items"] == 3
    assert data["items_with_recipes"] == 1
    assert Decimal(str(data["average_food_cost_percentage"])) == Decimal("11.20")
    assert "Optimal" in data["overall_food_cost_tier"]
    assert len(data["assumptions_and_limitations"]) == 3

    # Inspect Truffle Pasta item
    pasta_data = next(i for i in data["items"] if i["name"] == "Truffle Pasta")
    assert pasta_data["has_recipe"] is True
    assert Decimal(str(pasta_data["total_cost"])) == Decimal("2.80")
    assert Decimal(str(pasta_data["food_cost_percentage"])) == Decimal("11.20")
    assert Decimal(str(pasta_data["gross_contribution"])) == Decimal("22.20")
    assert Decimal(str(pasta_data["gross_margin_percentage"])) == Decimal("88.80")
    assert len(pasta_data["recipe_items"]) == 2

    # Inspect item with no recipe
    no_recipe_data = next(i for i in data["items"] if i["name"] == "Secret Special")
    assert no_recipe_data["has_recipe"] is False
    assert Decimal(str(no_recipe_data["total_cost"])) == Decimal("0.00")
    assert no_recipe_data["food_cost_percentage"] is None
    assert "No recipe defined" in no_recipe_data["notes"]

    # Inspect item with zero price
    zero_price_data = next(i for i in data["items"] if i["name"] == "Complimentary Bread")
    assert zero_price_data["has_recipe"] is False
    assert Decimal(str(zero_price_data["total_cost"])) == Decimal("0.00")
