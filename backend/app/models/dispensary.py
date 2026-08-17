import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, DateTime, Numeric, Boolean, Index, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from geoalchemy2 import Geography
from app.core.database import Base


class Dispensary(Base):
    __tablename__ = "dispensaries"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    slug: Mapped[Optional[str]] = mapped_column(String(200), unique=True, index=True)
    license_number: Mapped[Optional[str]] = mapped_column(String(100))
    address: Mapped[Optional[str]] = mapped_column(String(500))
    city: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    county: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    state: Mapped[str] = mapped_column(String(2), default="NJ")
    zip_code: Mapped[Optional[str]] = mapped_column(String(10))
    lat: Mapped[Optional[float]] = mapped_column(Numeric(10, 7))
    lng: Mapped[Optional[float]] = mapped_column(Numeric(10, 7))
    geom: Mapped[Optional[object]] = mapped_column(Geography(geometry_type="POINT", srid=4326), nullable=True)

    weedmaps_id: Mapped[Optional[str]] = mapped_column(String(100))
    leafly_slug: Mapped[Optional[str]] = mapped_column(String(200))
    jane_store_id: Mapped[Optional[str]] = mapped_column(String(100))
    dutchie_id: Mapped[Optional[str]] = mapped_column(String(200))
    treez_id: Mapped[Optional[str]] = mapped_column(String(100))
    dispense_slug: Mapped[Optional[str]] = mapped_column(String(200))

    primary_platform: Mapped[Optional[str]] = mapped_column(String(50))
    website: Mapped[Optional[str]] = mapped_column(String(500))
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    instagram: Mapped[Optional[str]] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(20), default="active")
    med_only: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    deals: Mapped[list["Deal"]] = relationship("Deal", back_populates="dispensary")
    menu_items: Mapped[list["MenuItem"]] = relationship("MenuItem", back_populates="dispensary")
    scrape_sources: Mapped[list["ScrapeSource"]] = relationship("ScrapeSource", back_populates="dispensary")

    __table_args__ = (
        Index("idx_dispensaries_geom", "geom", postgresql_using="gist"),
    )
