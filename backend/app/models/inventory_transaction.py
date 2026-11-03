"""
SQLAlchemy ORM Model: InventoryTransaction
Audit log tracking every ingredient level change (purchases, sales consumption, adjustments, waste).
"""

from datetime import datetime, timezone
from decimal import Decimal
import enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base

if TYPE_CHECKING:
    from app.models.ingredient import Ingredient


class TransactionType(str, enum.Enum):
    PURCHASE = "PURCHASE"
    SALE_CONSUMPTION = "SALE_CONSUMPTION"
    ADJUSTMENT = "ADJUSTMENT"
    WASTE = "WASTE"


class InventoryTransaction(Base):
    __tablename__ = "inventory_transactions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ingredient_id: Mapped[int] = mapped_column(
        ForeignKey("ingredients.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    transaction_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # Relationships
    ingredient: Mapped["Ingredient"] = relationship("Ingredient", back_populates="inventory_transactions", lazy="selectin")

    def __repr__(self) -> str:
        return f"<InventoryTransaction(id={self.id}, ingredient_id={self.ingredient_id}, type='{self.transaction_type}', qty={self.quantity})>"
