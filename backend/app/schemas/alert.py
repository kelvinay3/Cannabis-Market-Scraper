from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class AlertCreate(BaseModel):
    name: str
    trigger_type: str  # new_deal | price_drop | new_product | deal_change | deal_expired
    filter_config: Dict[str, Any] = {}
    channels: List[str] = ["email"]


class AlertUpdate(BaseModel):
    name: Optional[str] = None
    trigger_type: Optional[str] = None
    filter_config: Optional[Dict[str, Any]] = None
    channels: Optional[List[str]] = None
    is_active: Optional[bool] = None


class AlertOut(BaseModel):
    id: str
    user_id: str
    org_id: str
    name: str
    trigger_type: str
    filter_config: dict
    channels: List[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AlertEventOut(BaseModel):
    id: str
    alert_id: str
    alert_name: Optional[str] = None
    deal_id: Optional[str]
    item_id: Optional[str]
    message: Optional[str]
    sent_at: datetime
    channels_used: Optional[List[str]]

    class Config:
        from_attributes = True
