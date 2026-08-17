import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, DateTime, Numeric, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class MenuItem(Base):
    __tablename__ = "menu_items"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    dispensary_id: Mapped[str] = mapped_column(String, ForeignKey("dispensaries.id"), nullable=False, index=True)
    external_id: Mapped[Optional[str]] = mapped_column(String(200))
    name: Mapped[Optional[str]] = mapped_column(String(500))
    brand: Mapped[Optional[str]] = mapped_column(String(200), index=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    subcategory: Mapped[Optional[str]] = mapped_column(String(100))
    thc_percent: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    cbd_percent: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    weight: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    current_price: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    sale_price: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    dispensary: Mapped["Dispensary"] = relationship("Dispensary", back_populates="menu_items")
    price_changes: Mapped[list["PriceChange"]] = relationship("PriceChange", back_populates="item")

    __table_args__ = (
        UniqueConstraint("dispensary_id", "external_id", name="uq_menu_item"),
    )


class PriceChange(Base):
    __tablename__ = "price_changes"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    item_id: Mapped[str] = mapped_column(String, ForeignKey("menu_items.id"), nullable=False, index=True)
    dispensary_id: Mapped[str] = mapped_column(String, ForeignKey("dispensaries.id"), nullable=False, index=True)
    old_price: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    new_price: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    change_amount: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    change_pct: Mapped[Optional[float]] = mapped_column(Numeric(6, 2))
    change_type: Mapped[str] = mapped_column(String(20))  # increase | decrease
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    item: Mapped["MenuItem"] = relationship("MenuItem", back_populates="price_changes")
