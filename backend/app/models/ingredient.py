"""
SQLAlchemy ORM Model: Ingredient
"""

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base

if TYPE_CHECKING:
    from app.models.recipe import RecipeIngredient
    from app.models.inventory_transaction import InventoryTransaction
    from app.models.procurement import ProcurementRecommendationItem


class Ingredient(Base):
    __tablename__ = "ingredients"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    sku: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    category: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)  # e.g. kg, g, L, ml, pcs
    current_quantity: Mapped[Decimal] = mapped_column(
        Numeric(10, 3), nullable=False, default=Decimal("0.000")
    )
    min_quantity: Mapped[Decimal] = mapped_column(
        Numeric(10, 3), nullable=False, default=Decimal("0.000")
    )
    cost_per_unit: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=Decimal("0.00")
    )
    expiry_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    recipe_ingredients: Mapped[List["RecipeIngredient"]] = relationship(
        "RecipeIngredient", back_populates="ingredient", lazy="selectin"
    )
    inventory_transactions: Mapped[List["InventoryTransaction"]] = relationship(
        "InventoryTransaction", back_populates="ingredient", lazy="selectin"
    )
    procurement_items: Mapped[List["ProcurementRecommendationItem"]] = relationship(
        "ProcurementRecommendationItem", back_populates="ingredient", lazy="selectin"
    )

    __table_args__ = (
        CheckConstraint("current_quantity >= 0", name="chk_ingredient_current_quantity_positive"),
        CheckConstraint("min_quantity >= 0", name="chk_ingredient_min_quantity_positive"),
        CheckConstraint("cost_per_unit >= 0", name="chk_ingredient_cost_per_unit_positive"),
    )

    def __repr__(self) -> str:
        return f"<Ingredient(id={self.id}, sku='{self.sku}', name='{self.name}', qty={self.current_quantity} {self.unit})>"
