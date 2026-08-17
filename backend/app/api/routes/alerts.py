from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.models.alert import Alert, AlertEvent
from app.schemas.alert import AlertCreate, AlertUpdate, AlertOut, AlertEventOut
from app.schemas.common import PaginatedResponse
from app.api.deps import get_current_user
from app.models.user import User

import uuid

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("/", response_model=List[AlertOut])
async def list_alerts(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    q = select(Alert).where(Alert.user_id == current_user.id).order_by(Alert.created_at.desc())
    rows = (await db.execute(q)).scalars().all()
    return [AlertOut.model_validate(r) for r in rows]


@router.post("/", response_model=AlertOut)
async def create_alert(body: AlertCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    VALID_TRIGGERS = ["new_deal", "price_drop", "new_product", "deal_change", "deal_expired"]
    if body.trigger_type not in VALID_TRIGGERS:
        raise HTTPException(status_code=400, detail=f"Invalid trigger_type. Must be one of: {', '.join(VALID_TRIGGERS)}")

    alert = Alert(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        org_id=current_user.org_id or current_user.id,
        name=body.name,
        trigger_type=body.trigger_type,
        filter_config=body.filter_config,
        channels=body.channels,
    )
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    return AlertOut.model_validate(alert)


@router.patch("/{alert_id}", response_model=AlertOut)
async def update_alert(
    alert_id: str,
    body: AlertUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Alert).where(Alert.id == alert_id, Alert.user_id == current_user.id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    if body.name is not None:
        alert.name = body.name
    if body.trigger_type is not None:
        alert.trigger_type = body.trigger_type
    if body.filter_config is not None:
        alert.filter_config = body.filter_config
    if body.channels is not None:
        alert.channels = body.channels
    if body.is_active is not None:
        alert.is_active = body.is_active

    await db.commit()
    await db.refresh(alert)
    return AlertOut.model_validate(alert)


@router.delete("/{alert_id}")
async def delete_alert(alert_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Alert).where(Alert.id == alert_id, Alert.user_id == current_user.id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    await db.delete(alert)
    await db.commit()
    return {"message": "Alert deleted"}


@router.post("/{alert_id}/test")
async def test_alert(alert_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    from app.services.email import send_deal_alert_email
    result = await db.execute(select(Alert).where(Alert.id == alert_id, Alert.user_id == current_user.id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    if "email" in (alert.channels or []):
        await send_deal_alert_email(
            to=current_user.email,
            name=current_user.name or "",
            alert_name=f"[TEST] {alert.name}",
            deals=[{"dispensary_name": "Test Dispensary", "city": "Newark", "county": "Essex", "title": "20% Off All Flower — Test Alert"}],
        )

    return {"message": f"Test notification sent to {current_user.email}"}


@router.get("/history", response_model=PaginatedResponse[AlertEventOut])
async def alert_history(
    page: int = 1,
    per_page: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user_alert_ids = (await db.execute(select(Alert.id).where(Alert.user_id == current_user.id))).scalars().all()
    if not user_alert_ids:
        return PaginatedResponse(data=[], total=0, page=page, per_page=per_page, pages=0)

    count_q = select(func.count()).select_from(AlertEvent).where(AlertEvent.alert_id.in_(user_alert_ids))
    total = (await db.execute(count_q)).scalar()

    rows = (await db.execute(
        select(AlertEvent, Alert)
        .join(Alert, AlertEvent.alert_id == Alert.id)
        .where(AlertEvent.alert_id.in_(user_alert_ids))
        .offset((page - 1) * per_page).limit(per_page)
        .order_by(AlertEvent.sent_at.desc())
    )).all()

    data = []
    for event, alert in rows:
        out = AlertEventOut.model_validate(event)
        out.alert_name = alert.name
        data.append(out)

    return PaginatedResponse(data=data, total=total, page=page, per_page=per_page, pages=-(-total // per_page))
