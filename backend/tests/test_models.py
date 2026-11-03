"""
Automated Tests for Database Models, Relationships, Constraints, and Pydantic Schemas.
"""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

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
from app.schemas.ingredient import IngredientCreate, IngredientResponse
from app.schemas.menu_item import MenuItemCreate
from app.schemas.recipe import RecipeIngredientCreate
from app.schemas.sale import SaleCreate, SaleItemCreate
from pydantic import ValidationError


# ── 1. INGREDIENT TESTS ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_ingredient(db_session: AsyncSession):
    """Test creating an ingredient and reading it back."""
    ing = Ingredient(
        name="Organic Basil",
        sku="ING-PROD-BASIL",
        category="Produce",
        unit="kg",
        current_quantity=Decimal("3.500"),
        min_quantity=Decimal("1.000"),
        cost_per_unit=Decimal("12.00"),
        expiry_date=date(2026, 11, 20),
    )
    db_session.add(ing)
    await db_session.commit()
    await db_session.refresh(ing)

    assert ing.id is not None
    assert ing.name == "Organic Basil"
    assert ing.sku == "ING-PROD-BASIL"
    assert ing.current_quantity == Decimal("3.500")


@pytest.mark.asyncio
async def test_update_ingredient(db_session: AsyncSession):
    """Test modifying ingredient stock levels and unit costs."""
    ing = Ingredient(
        name="Mozzarella",
        sku="ING-DAIR-MOZZ",
        category="Dairy",
        unit="kg",
        current_quantity=Decimal("10.000"),
        min_quantity=Decimal("2.000"),
        cost_per_unit=Decimal("8.50"),
    )
    db_session.add(ing)
    await db_session.commit()

    # Update stock
    ing.current_quantity = Decimal("15.500")
    ing.cost_per_unit = Decimal("8.00")
    await db_session.commit()
    await db_session.refresh(ing)

    assert ing.current_quantity == Decimal("15.500")
    assert ing.cost_per_unit == Decimal("8.00")


@pytest.mark.asyncio
async def test_prevent_negative_ingredient_quantity(db_session: AsyncSession):
    """Ensure CheckConstraint prevents negative ingredient quantity at DB level."""
    ing = Ingredient(
        name="Salt",
        sku="ING-DRY-SALT",
        category="Dry Goods",
        unit="kg",
        current_quantity=Decimal("-1.000"),  # Invalid negative quantity
        min_quantity=Decimal("0.500"),
        cost_per_unit=Decimal("1.00"),
    )
    db_session.add(ing)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_prevent_duplicate_sku(db_session: AsyncSession):
    """Ensure uniqueness constraint on sku is enforced."""
    ing1 = Ingredient(
        name="Olive Oil Extra",
        sku="ING-OIL-01",
        category="Dry Goods",
        unit="L",
        current_quantity=Decimal("5.000"),
        min_quantity=Decimal("1.000"),
        cost_per_unit=Decimal("10.00"),
    )
    ing2 = Ingredient(
        name="Olive Oil Regular",
        sku="ING-OIL-01",  # Duplicate sku
        category="Dry Goods",
        unit="L",
        current_quantity=Decimal("2.000"),
        min_quantity=Decimal("1.000"),
        cost_per_unit=Decimal("8.00"),
    )
    db_session.add(ing1)
    await db_session.commit()

    db_session.add(ing2)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


# ── 2. MENU ITEM & RECIPE TESTS ──────────────────────────────────────

@pytest.mark.asyncio
async def test_create_menu_item_and_recipe(db_session: AsyncSession):
    """Test creating menu item and linking recipe ingredients."""
    # Create ingredients
    patty = Ingredient(name="Beef Patty", sku="ING-PATTY", category="Meat", unit="pcs", current_quantity=Decimal("50"), min_quantity=Decimal("10"), cost_per_unit=Decimal("2.00"))
    bun = Ingredient(name="Sesame Bun", sku="ING-BUN", category="Dry Goods", unit="pcs", current_quantity=Decimal("60"), min_quantity=Decimal("15"), cost_per_unit=Decimal("0.50"))
    db_session.add_all([patty, bun])
    await db_session.flush()

    # Create menu item
    burger = MenuItem(
        name="Signature Burger",
        selling_price=Decimal("9.99"),
        description="Freshly grilled beef patty with soft sesame bun.",
        is_active=True,
    )
    db_session.add(burger)
    await db_session.flush()

    # Create recipe mappings
    recipe1 = RecipeIngredient(menu_item_id=burger.id, ingredient_id=patty.id, quantity_required=Decimal("1.000"))
    recipe2 = RecipeIngredient(menu_item_id=burger.id, ingredient_id=bun.id, quantity_required=Decimal("1.000"))
    db_session.add_all([recipe1, recipe2])
    await db_session.commit()

    # Verify traversal
    stmt = select(MenuItem).where(MenuItem.id == burger.id)
    res = (await db_session.execute(stmt)).scalar_one()
    assert len(res.recipe_ingredients) == 2
    assert res.recipe_ingredients[0].ingredient.name in ["Beef Patty", "Sesame Bun"]


@pytest.mark.asyncio
async def test_prevent_duplicate_recipe_mapping(db_session: AsyncSession):
    """Ensure duplicate recipe ingredient mapping raises UniqueConstraint error."""
    ing = Ingredient(name="Sugar", sku="ING-SUGAR", category="Dry Goods", unit="kg", current_quantity=Decimal("10"), min_quantity=Decimal("2"), cost_per_unit=Decimal("1.50"))
    item = MenuItem(name="Sweet Tea", selling_price=Decimal("2.50"))
    db_session.add_all([ing, item])
    await db_session.flush()

    r1 = RecipeIngredient(menu_item_id=item.id, ingredient_id=ing.id, quantity_required=Decimal("0.050"))
    r2 = RecipeIngredient(menu_item_id=item.id, ingredient_id=ing.id, quantity_required=Decimal("0.030"))  # Duplicate pair
    db_session.add_all([r1, r2])

    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


# ── 3. SALES & INVENTORY TRANSACTIONS ────────────────────────────────

@pytest.mark.asyncio
async def test_create_sale_and_sale_items(db_session: AsyncSession):
    """Test creating a sale with line items and computing total amount."""
    item1 = MenuItem(name="Taco", selling_price=Decimal("4.50"))
    item2 = MenuItem(name="Horchata", selling_price=Decimal("3.00"))
    db_session.add_all([item1, item2])
    await db_session.flush()

    sale = Sale(total_amount=Decimal("15.00"), sold_at=datetime.now(timezone.utc))
    db_session.add(sale)
    await db_session.flush()

    s_item1 = SaleItem(sale_id=sale.id, menu_item_id=item1.id, quantity=2, unit_price=Decimal("4.50"), subtotal=Decimal("9.00"))
    s_item2 = SaleItem(sale_id=sale.id, menu_item_id=item2.id, quantity=2, unit_price=Decimal("3.00"), subtotal=Decimal("6.00"))
    db_session.add_all([s_item1, s_item2])
    await db_session.commit()

    # Verify relationship
    stmt = select(Sale).where(Sale.id == sale.id)
    saved_sale = (await db_session.execute(stmt)).scalar_one()
    assert len(saved_sale.items) == 2
    assert sum(si.subtotal for si in saved_sale.items) == Decimal("15.00")


@pytest.mark.asyncio
async def test_create_inventory_transaction(db_session: AsyncSession):
    """Test creating auditable inventory transactions."""
    ing = Ingredient(name="Flour", sku="ING-FLOUR-01", category="Dry Goods", unit="kg", current_quantity=Decimal("20"), min_quantity=Decimal("5"), cost_per_unit=Decimal("1.20"))
    db_session.add(ing)
    await db_session.flush()

    tx = InventoryTransaction(
        ingredient_id=ing.id,
        transaction_type=TransactionType.PURCHASE.value,
        quantity=Decimal("25.000"),
        notes="Weekly bulk delivery",
    )
    db_session.add(tx)
    await db_session.commit()
    await db_session.refresh(tx)

    assert tx.id is not None
    assert tx.transaction_type == "PURCHASE"
    assert tx.ingredient.name == "Flour"


# ── 4. PROCUREMENT RECOMMENDATION TESTS ──────────────────────────────

@pytest.mark.asyncio
async def test_create_procurement_recommendation(db_session: AsyncSession):
    """Test creating a procurement recommendation with items."""
    ing = Ingredient(name="Butter", sku="ING-BUTTER-01", category="Dairy", unit="kg", current_quantity=Decimal("1.000"), min_quantity=Decimal("3.000"), cost_per_unit=Decimal("7.00"))
    db_session.add(ing)
    await db_session.flush()

    rec = ProcurementRecommendation(
        status=RecommendationStatus.PENDING.value,
        total_estimated_cost=Decimal("70.00"),
        reason="Stock is below reorder threshold",
    )
    db_session.add(rec)
    await db_session.flush()

    rec_item = ProcurementRecommendationItem(
        recommendation_id=rec.id,
        ingredient_id=ing.id,
        recommended_quantity=Decimal("10.000"),
        estimated_unit_cost=Decimal("7.00"),
        estimated_total_cost=Decimal("70.00"),
    )
    db_session.add(rec_item)
    await db_session.commit()

    # Query back
    stmt = select(ProcurementRecommendation).where(ProcurementRecommendation.id == rec.id)
    saved_rec = (await db_session.execute(stmt)).scalar_one()
    assert saved_rec.status == "PENDING"
    assert len(saved_rec.items) == 1
    assert saved_rec.items[0].recommended_quantity == Decimal("10.000")


# ── 5. AUTOMATION LOG TESTS ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_automation_log(db_session: AsyncSession):
    """Test recording an automation log entry."""
    now = datetime.now(timezone.utc)
    log = AutomationLog(
        task_name="inventory_check_cron",
        status=AutomationStatus.SUCCESS.value,
        message="Checked 15 items, all healthy",
        started_at=now - timedelta(seconds=5),
        completed_at=now,
    )
    db_session.add(log)
    await db_session.commit()
    await db_session.refresh(log)

    assert log.id is not None
    assert log.status == "SUCCESS"
    assert log.task_name == "inventory_check_cron"


# ── 6. FOREIGN KEY INTEGRITY & CASCADING ──────────────────────────────

@pytest.mark.asyncio
async def test_restrict_delete_ingredient_in_use(db_session: AsyncSession):
    """Ensure an ingredient used in recipes cannot be deleted (ondelete=RESTRICT)."""
    ing = Ingredient(name="Cocoa", sku="ING-COCOA", category="Dry Goods", unit="kg", current_quantity=Decimal("5"), min_quantity=Decimal("1"), cost_per_unit=Decimal("15.00"))
    item = MenuItem(name="Hot Chocolate", selling_price=Decimal("4.00"))
    db_session.add_all([ing, item])
    await db_session.flush()

    recipe = RecipeIngredient(menu_item_id=item.id, ingredient_id=ing.id, quantity_required=Decimal("0.030"))
    db_session.add(recipe)
    await db_session.commit()

    # Attempting to delete ingredient should fail due to RESTRICT FK constraint
    await db_session.delete(ing)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


# ── 7. PYDANTIC SCHEMA VALIDATION TESTS ──────────────────────────────

def test_pydantic_ingredient_validation():
    """Ensure Pydantic schemas validate input rules."""
    # Negative quantity should fail
    with pytest.raises(ValidationError):
        IngredientCreate(
            name="Milk",
            sku="ING-MILK",
            category="Dairy",
            unit="L",
            current_quantity=Decimal("-2.000"),  # ge=0 violation
            min_quantity=Decimal("1.000"),
            cost_per_unit=Decimal("1.50"),
        )

    # Valid schema succeeds
    valid = IngredientCreate(
        name="Milk",
        sku="ING-MILK",
        category="Dairy",
        unit="L",
        current_quantity=Decimal("10.000"),
        min_quantity=Decimal("2.000"),
        cost_per_unit=Decimal("1.50"),
    )
    assert valid.current_quantity == Decimal("10.000")


def test_pydantic_sale_validation():
    """Ensure SaleCreate enforces at least one line item."""
    with pytest.raises(ValidationError):
        SaleCreate(items=[])  # min_length=1 violation
