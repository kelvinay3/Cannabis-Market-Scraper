from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class DispensaryOut(BaseModel):
    id: str
    name: str
    slug: Optional[str]
    license_number: Optional[str]
    address: Optional[str]
    city: Optional[str]
    county: Optional[str]
    state: str
    zip_code: Optional[str]
    lat: Optional[float]
    lng: Optional[float]
    primary_platform: Optional[str]
    website: Optional[str]
    phone: Optional[str]
    instagram: Optional[str]
    status: str
    med_only: bool
    weedmaps_id: Optional[str]
    leafly_slug: Optional[str]
    jane_store_id: Optional[str]
    dutchie_id: Optional[str]
    active_deal_count: Optional[int] = 0

    class Config:
        from_attributes = True


class DispensaryNearby(DispensaryOut):
    distance_miles: Optional[float] = None


class DispensaryCreate(BaseModel):
    name: str
    address: Optional[str] = None
    city: Optional[str] = None
    county: Optional[str] = None
    zip_code: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    license_number: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    jane_store_id: Optional[str] = None
    dutchie_id: Optional[str] = None
    weedmaps_id: Optional[str] = None
    leafly_slug: Optional[str] = None
    primary_platform: Optional[str] = None
    med_only: bool = False
