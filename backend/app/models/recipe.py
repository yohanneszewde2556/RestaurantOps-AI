"""
SQLAlchemy ORM Model: RecipeIngredient
Maps MenuItems to the required Ingredients and consumption quantities.
"""

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Numeric,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base

if TYPE_CHECKING:
    from app.models.ingredient import Ingredient
    from app.models.menu_item import MenuItem


class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    menu_item_id: Mapped[int] = mapped_column(
        ForeignKey("menu_items.id", ondelete="CASCADE"), nullable=False, index=True
    )
    ingredient_id: Mapped[int] = mapped_column(
        ForeignKey("ingredients.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    quantity_required: Mapped[Decimal] = mapped_column(
        Numeric(10, 3), nullable=False
    )

    # Relationships
    menu_item: Mapped["MenuItem"] = relationship("MenuItem", back_populates="recipe_ingredients", lazy="selectin")
    ingredient: Mapped["Ingredient"] = relationship("Ingredient", back_populates="recipe_ingredients", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("menu_item_id", "ingredient_id", name="uq_recipe_menu_item_ingredient"),
        CheckConstraint("quantity_required > 0", name="chk_recipe_quantity_positive"),
    )

    def __repr__(self) -> str:
        return f"<RecipeIngredient(menu_item_id={self.menu_item_id}, ingredient_id={self.ingredient_id}, qty={self.quantity_required})>"
