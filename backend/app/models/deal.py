import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, DateTime, Numeric, Boolean, ForeignKey, Text, ARRAY, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Deal(Base):
    __tablename__ = "deals"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    dispensary_id: Mapped[str] = mapped_column(String, ForeignKey("dispensaries.id"), nullable=False, index=True)
    source_platform: Mapped[Optional[str]] = mapped_column(String(50))
    external_id: Mapped[Optional[str]] = mapped_column(String(200))
    title: Mapped[Optional[str]] = mapped_column(String(500))
    description: Mapped[Optional[str]] = mapped_column(Text)
    deal_type: Mapped[Optional[str]] = mapped_column(String(50))
    discount_value: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    discount_unit: Mapped[Optional[str]] = mapped_column(String(20))
    minimum_purchase: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    applicable_categories: Mapped[Optional[list]] = mapped_column(ARRAY(String))
    applicable_brands: Mapped[Optional[list]] = mapped_column(ARRAY(String))
    day_of_week: Mapped[Optional[list]] = mapped_column(ARRAY(String))
    starts_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    raw_text: Mapped[Optional[str]] = mapped_column(Text)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    dispensary: Mapped["Dispensary"] = relationship("Dispensary", back_populates="deals")
    history: Mapped[list["DealHistory"]] = relationship("DealHistory", back_populates="deal")

    __table_args__ = (
        UniqueConstraint("dispensary_id", "source_platform", "external_id", name="uq_deal_source"),
    )


class DealHistory(Base):
    __tablename__ = "deal_history"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    deal_id: Mapped[str] = mapped_column(String, ForeignKey("deals.id"), nullable=False, index=True)
    change_type: Mapped[str] = mapped_column(String(30))  # created | modified | deactivated | reactivated
    old_data: Mapped[Optional[dict]] = mapped_column(JSONB)
    new_data: Mapped[Optional[dict]] = mapped_column(JSONB)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    deal: Mapped["Deal"] = relationship("Deal", back_populates="history")
