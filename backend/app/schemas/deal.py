from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class DealOut(BaseModel):
    id: str
    dispensary_id: str
    dispensary_name: Optional[str] = None
    dispensary_city: Optional[str] = None
    dispensary_county: Optional[str] = None
    source_platform: Optional[str]
    title: Optional[str]
    description: Optional[str]
    deal_type: Optional[str]
    discount_value: Optional[float]
    discount_unit: Optional[str]
    minimum_purchase: Optional[float]
    applicable_categories: Optional[List[str]]
    applicable_brands: Optional[List[str]]
    day_of_week: Optional[List[str]]
    starts_at: Optional[datetime]
    ends_at: Optional[datetime]
    is_active: bool
    first_seen_at: datetime
    last_seen_at: datetime

    class Config:
        from_attributes = True


class DealHistoryOut(BaseModel):
    id: str
    deal_id: str
    change_type: str
    old_data: Optional[dict]
    new_data: Optional[dict]
    changed_at: datetime

    class Config:
        from_attributes = True


class PriceChangeOut(BaseModel):
    id: str
    item_id: str
    item_name: Optional[str] = None
    dispensary_id: str
    dispensary_name: Optional[str] = None
    dispensary_city: Optional[str] = None
    old_price: Optional[float]
    new_price: Optional[float]
    change_amount: Optional[float]
    change_pct: Optional[float]
    change_type: str
    detected_at: datetime

    class Config:
        from_attributes = True
