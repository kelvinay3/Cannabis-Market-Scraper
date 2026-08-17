from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.dispensary import Dispensary
from app.models.deal import Deal
from app.schemas.dispensary import DispensaryOut, DispensaryNearby, DispensaryCreate
from app.schemas.common import PaginatedResponse
from app.api.deps import get_current_user, require_admin
from app.models.user import User

router = APIRouter(prefix="/dispensaries", tags=["dispensaries"])


@router.get("/", response_model=PaginatedResponse[DispensaryOut])
async def list_dispensaries(
    page: int = 1,
    per_page: int = 50,
    county: Optional[str] = None,
    city: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    med_only: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = select(Dispensary)
    count_q = select(func.count()).select_from(Dispensary)

    if county:
        q = q.where(func.lower(Dispensary.county) == county.lower())
        count_q = count_q.where(func.lower(Dispensary.county) == county.lower())
    if city:
        q = q.where(func.lower(Dispensary.city) == city.lower())
        count_q = count_q.where(func.lower(Dispensary.city) == city.lower())
    if status:
        q = q.where(Dispensary.status == status)
        count_q = count_q.where(Dispensary.status == status)
    if search:
        pattern = f"%{search}%"
        q = q.where(Dispensary.name.ilike(pattern))
        count_q = count_q.where(Dispensary.name.ilike(pattern))
    if med_only is not None:
        q = q.where(Dispensary.med_only == med_only)
        count_q = count_q.where(Dispensary.med_only == med_only)

    total = (await db.execute(count_q)).scalar()
    dispensaries = (await db.execute(q.offset((page - 1) * per_page).limit(per_page).order_by(Dispensary.county, Dispensary.city, Dispensary.name))).scalars().all()

    # Get active deal counts
    deal_counts = {}
    if dispensaries:
        ids = [d.id for d in dispensaries]
        dc_q = select(Deal.dispensary_id, func.count(Deal.id)).where(Deal.dispensary_id.in_(ids), Deal.is_active == True).group_by(Deal.dispensary_id)
        for row in (await db.execute(dc_q)).all():
            deal_counts[row[0]] = row[1]

    result = []
    for d in dispensaries:
        out = DispensaryOut.model_validate(d)
        out.active_deal_count = deal_counts.get(d.id, 0)
        result.append(out)

    return PaginatedResponse(data=result, total=total, page=page, per_page=per_page, pages=-(-total // per_page))


@router.get("/counties", response_model=List[str])
async def list_counties(db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    result = await db.execute(
        select(Dispensary.county).where(Dispensary.county.isnot(None)).distinct().order_by(Dispensary.county)
    )
    return [r[0] for r in result.all() if r[0]]


@router.get("/cities", response_model=List[str])
async def list_cities(
    county: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = select(Dispensary.city).where(Dispensary.city.isnot(None)).distinct().order_by(Dispensary.city)
    if county:
        q = q.where(func.lower(Dispensary.county) == county.lower())
    result = await db.execute(q)
    return [r[0] for r in result.all() if r[0]]


@router.get("/nearby", response_model=List[DispensaryNearby])
async def get_nearby(
    lat: float = Query(...),
    lng: float = Query(...),
    radius_miles: float = Query(default=10, ge=0.5, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    radius_meters = radius_miles * 1609.34
    sql = text("""
        SELECT d.*,
               ST_Distance(d.geom, ST_MakePoint(:lng, :lat)::geography) / 1609.34 AS distance_miles
        FROM dispensaries d
        WHERE d.geom IS NOT NULL
          AND ST_DWithin(d.geom, ST_MakePoint(:lng, :lat)::geography, :radius)
          AND d.status = 'active'
        ORDER BY distance_miles
        LIMIT 100
    """)
    rows = (await db.execute(sql, {"lat": lat, "lng": lng, "radius": radius_meters})).mappings().all()

    return [DispensaryNearby(
        **{k: v for k, v in row.items() if k != "distance_miles"},
        distance_miles=round(float(row["distance_miles"]), 2),
    ) for row in rows]


@router.get("/{dispensary_id}", response_model=DispensaryOut)
async def get_dispensary(
    dispensary_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    from fastapi import HTTPException
    result = await db.execute(select(Dispensary).where(Dispensary.id == dispensary_id))
    d = result.scalar_one_or_none()
    if not d:
        raise HTTPException(status_code=404, detail="Dispensary not found")

    count = (await db.execute(select(func.count()).select_from(Deal).where(Deal.dispensary_id == d.id, Deal.is_active == True))).scalar()
    out = DispensaryOut.model_validate(d)
    out.active_deal_count = count
    return out


@router.post("/", response_model=DispensaryOut)
async def create_dispensary(
    body: DispensaryCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    import uuid
    from geoalchemy2 import WKTElement
    d = Dispensary(
        id=str(uuid.uuid4()),
        **body.model_dump(exclude={"lat", "lng"}),
    )
    if body.lat and body.lng:
        d.lat = body.lat
        d.lng = body.lng
        d.geom = WKTElement(f"POINT({body.lng} {body.lat})", srid=4326)
    db.add(d)
    await db.commit()
    await db.refresh(d)
    return DispensaryOut.model_validate(d)
