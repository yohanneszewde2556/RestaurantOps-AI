"""
SQLAlchemy ORM Models: ProcurementRecommendation and ProcurementRecommendationItem
Recommendation and approval workflow for replenishing low-stock or expiring ingredients.
"""

from datetime import datetime, timezone
from decimal import Decimal
import enum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    CheckConstraint,
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


class RecommendationStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ProcurementRecommendation(Base):
    __tablename__ = "procurement_recommendations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    status: Mapped[str] = mapped_column(
        String(20),
        default=RecommendationStatus.PENDING.value,
        nullable=False,
        index=True,
    )
    total_estimated_cost: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=Decimal("0.00")
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    items: Mapped[List["ProcurementRecommendationItem"]] = relationship(
        "ProcurementRecommendationItem",
        back_populates="recommendation",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        CheckConstraint("total_estimated_cost >= 0", name="chk_procurement_total_cost_positive"),
    )

    def __repr__(self) -> str:
        return f"<ProcurementRecommendation(id={self.id}, status='{self.status}', total={self.total_estimated_cost})>"


class ProcurementRecommendationItem(Base):
    __tablename__ = "procurement_recommendation_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    recommendation_id: Mapped[int] = mapped_column(
        ForeignKey("procurement_recommendations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ingredient_id: Mapped[int] = mapped_column(
        ForeignKey("ingredients.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    recommended_quantity: Mapped[Decimal] = mapped_column(
        Numeric(10, 3), nullable=False
    )
    estimated_unit_cost: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False
    )
    estimated_total_cost: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False
    )

    # Relationships
    recommendation: Mapped["ProcurementRecommendation"] = relationship(
        "ProcurementRecommendation", back_populates="items", lazy="selectin"
    )
    ingredient: Mapped["Ingredient"] = relationship(
        "Ingredient", back_populates="procurement_items", lazy="selectin"
    )

    __table_args__ = (
        CheckConstraint("recommended_quantity > 0", name="chk_procurement_item_qty_positive"),
        CheckConstraint("estimated_unit_cost >= 0", name="chk_procurement_item_unit_cost_positive"),
        CheckConstraint("estimated_total_cost >= 0", name="chk_procurement_item_total_cost_positive"),
    )

    def __repr__(self) -> str:
        return f"<ProcurementRecommendationItem(id={self.id}, ingredient_id={self.ingredient_id}, qty={self.recommended_quantity})>"
