from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.core.database import get_db
from app.models.deal import Deal, DealHistory
from app.models.menu_item import PriceChange, MenuItem
from app.models.dispensary import Dispensary
from app.schemas.deal import DealOut, DealHistoryOut, PriceChangeOut
from app.schemas.common import PaginatedResponse
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/deals", tags=["deals"])


def _build_deal_out(deal: Deal, dispensary: Dispensary = None) -> DealOut:
    d = DealOut.model_validate(deal)
    if dispensary:
        d.dispensary_name = dispensary.name
        d.dispensary_city = dispensary.city
        d.dispensary_county = dispensary.county
    return d


@router.get("/", response_model=PaginatedResponse[DealOut])
async def list_deals(
    page: int = 1,
    per_page: int = 50,
    county: Optional[str] = None,
    city: Optional[str] = None,
    category: Optional[str] = None,
    deal_type: Optional[str] = None,
    min_discount: Optional[float] = None,
    platform: Optional[str] = None,
    active_only: bool = True,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = select(Deal, Dispensary).join(Dispensary, Deal.dispensary_id == Dispensary.id)
    count_q = select(func.count()).select_from(Deal).join(Dispensary, Deal.dispensary_id == Dispensary.id)

    if active_only:
        q = q.where(Deal.is_active == True)
        count_q = count_q.where(Deal.is_active == True)
    if county:
        q = q.where(func.lower(Dispensary.county) == county.lower())
        count_q = count_q.where(func.lower(Dispensary.county) == county.lower())
    if city:
        q = q.where(func.lower(Dispensary.city) == city.lower())
        count_q = count_q.where(func.lower(Dispensary.city) == city.lower())
    if category:
        q = q.where(Deal.applicable_categories.contains([category]))
        count_q = count_q.where(Deal.applicable_categories.contains([category]))
    if deal_type:
        q = q.where(Deal.deal_type == deal_type)
        count_q = count_q.where(Deal.deal_type == deal_type)
    if min_discount:
        q = q.where(Deal.discount_value >= min_discount)
        count_q = count_q.where(Deal.discount_value >= min_discount)
    if platform:
        q = q.where(Deal.source_platform == platform)
        count_q = count_q.where(Deal.source_platform == platform)
    if search:
        pattern = f"%{search}%"
        q = q.where(Deal.title.ilike(pattern))
        count_q = count_q.where(Deal.title.ilike(pattern))

    total = (await db.execute(count_q)).scalar()
    rows = (await db.execute(q.offset((page - 1) * per_page).limit(per_page).order_by(Deal.last_seen_at.desc()))).all()

    data = [_build_deal_out(row[0], row[1]) for row in rows]
    return PaginatedResponse(data=data, total=total, page=page, per_page=per_page, pages=-(-total // per_page))


@router.get("/new", response_model=PaginatedResponse[DealOut])
async def new_deals(
    hours: int = Query(default=24, ge=1, le=168),
    county: Optional[str] = None,
    page: int = 1,
    per_page: int = 50,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    from datetime import datetime, timezone, timedelta
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    q = select(Deal, Dispensary).join(Dispensary, Deal.dispensary_id == Dispensary.id).where(Deal.first_seen_at >= cutoff, Deal.is_active == True)
    count_q = select(func.count()).select_from(Deal).join(Dispensary, Deal.dispensary_id == Dispensary.id).where(Deal.first_seen_at >= cutoff, Deal.is_active == True)

    if county:
        q = q.where(func.lower(Dispensary.county) == county.lower())
        count_q = count_q.where(func.lower(Dispensary.county) == county.lower())

    total = (await db.execute(count_q)).scalar()
    rows = (await db.execute(q.offset((page - 1) * per_page).limit(per_page).order_by(Deal.first_seen_at.desc()))).all()
    data = [_build_deal_out(r[0], r[1]) for r in rows]
    return PaginatedResponse(data=data, total=total, page=page, per_page=per_page, pages=-(-total // per_page))


@router.get("/expiring", response_model=List[DealOut])
async def expiring_deals(
    hours: int = Query(default=48, ge=1, le=168),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    from datetime import datetime, timezone, timedelta
    now = datetime.now(timezone.utc)
    cutoff = now + timedelta(hours=hours)
    rows = (await db.execute(
        select(Deal, Dispensary)
        .join(Dispensary, Deal.dispensary_id == Dispensary.id)
        .where(Deal.is_active == True, Deal.ends_at.isnot(None), Deal.ends_at.between(now, cutoff))
        .order_by(Deal.ends_at)
        .limit(100)
    )).all()
    return [_build_deal_out(r[0], r[1]) for r in rows]


@router.get("/dispensary/{dispensary_id}", response_model=List[DealOut])
async def deals_by_dispensary(
    dispensary_id: str,
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = select(Deal, Dispensary).join(Dispensary, Deal.dispensary_id == Dispensary.id).where(Deal.dispensary_id == dispensary_id)
    if active_only:
        q = q.where(Deal.is_active == True)
    rows = (await db.execute(q.order_by(Deal.last_seen_at.desc()))).all()
    return [_build_deal_out(r[0], r[1]) for r in rows]


@router.get("/{deal_id}", response_model=DealOut)
async def get_deal(deal_id: str, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    from fastapi import HTTPException
    row = (await db.execute(
        select(Deal, Dispensary).join(Dispensary, Deal.dispensary_id == Dispensary.id).where(Deal.id == deal_id)
    )).first()
    if not row:
        raise HTTPException(status_code=404, detail="Deal not found")
    return _build_deal_out(row[0], row[1])


@router.get("/{deal_id}/history", response_model=List[DealHistoryOut])
async def deal_history(deal_id: str, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    rows = (await db.execute(
        select(DealHistory).where(DealHistory.deal_id == deal_id).order_by(DealHistory.changed_at.desc())
    )).scalars().all()
    return [DealHistoryOut.model_validate(r) for r in rows]


@router.get("/prices/changes", response_model=PaginatedResponse[PriceChangeOut])
async def price_changes(
    hours: int = Query(default=48),
    direction: Optional[str] = None,
    page: int = 1,
    per_page: int = 50,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    from datetime import datetime, timezone, timedelta
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    q = select(PriceChange, MenuItem, Dispensary).join(MenuItem, PriceChange.item_id == MenuItem.id).join(Dispensary, PriceChange.dispensary_id == Dispensary.id).where(PriceChange.detected_at >= cutoff)
    count_q = select(func.count()).select_from(PriceChange).where(PriceChange.detected_at >= cutoff)
    if direction:
        q = q.where(PriceChange.change_type == direction)
        count_q = count_q.where(PriceChange.change_type == direction)

    total = (await db.execute(count_q)).scalar()
    rows = (await db.execute(q.offset((page - 1) * per_page).limit(per_page).order_by(PriceChange.detected_at.desc()))).all()

    data = []
    for pc, item, disp in rows:
        out = PriceChangeOut.model_validate(pc)
        out.item_name = item.name
        out.dispensary_name = disp.name
        out.dispensary_city = disp.city
        data.append(out)

    return PaginatedResponse(data=data, total=total, page=page, per_page=per_page, pages=-(-total // per_page))
