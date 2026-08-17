import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, DateTime, Boolean, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class ScrapeSource(Base):
    __tablename__ = "scrape_sources"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    dispensary_id: Mapped[str] = mapped_column(String, ForeignKey("dispensaries.id"), nullable=False, index=True)
    platform: Mapped[str] = mapped_column(String(50))  # jane | dutchie | weedmaps | leafly | treez | custom
    source_url: Mapped[Optional[str]] = mapped_column(String(1000))
    config: Mapped[dict] = mapped_column(JSONB, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_scrape_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    next_scrape_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    dispensary: Mapped["Dispensary"] = relationship("Dispensary", back_populates="scrape_sources")
    jobs: Mapped[list["ScrapeJob"]] = relationship("ScrapeJob", back_populates="source")


class ScrapeJob(Base):
    __tablename__ = "scrape_jobs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    source_id: Mapped[str] = mapped_column(String, ForeignKey("scrape_sources.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending | running | success | error
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    deals_found: Mapped[int] = mapped_column(Integer, default=0)
    items_found: Mapped[int] = mapped_column(Integer, default=0)
    errors: Mapped[Optional[dict]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    source: Mapped["ScrapeSource"] = relationship("ScrapeSource", back_populates="jobs")
