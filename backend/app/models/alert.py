import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, DateTime, Boolean, ForeignKey, Text, ARRAY
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False, index=True)
    org_id: Mapped[str] = mapped_column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    trigger_type: Mapped[str] = mapped_column(String(50))  # new_deal | price_drop | new_product | deal_change | deal_expired
    filter_config: Mapped[dict] = mapped_column(JSONB, default=dict)
    channels: Mapped[list] = mapped_column(ARRAY(String), default=list)  # email | sms | webhook
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user: Mapped["User"] = relationship("User", back_populates="alerts")
    organization: Mapped["Organization"] = relationship("Organization", back_populates="alerts")
    events: Mapped[list["AlertEvent"]] = relationship("AlertEvent", back_populates="alert")


class AlertEvent(Base):
    __tablename__ = "alert_events"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    alert_id: Mapped[str] = mapped_column(String, ForeignKey("alerts.id"), nullable=False, index=True)
    deal_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("deals.id"), nullable=True)
    item_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("menu_items.id"), nullable=True)
    message: Mapped[Optional[str]] = mapped_column(Text)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    channels_used: Mapped[Optional[list]] = mapped_column(ARRAY(String))

    alert: Mapped["Alert"] = relationship("Alert", back_populates="events")
