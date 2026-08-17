from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text

from app.core.database import get_db
from app.models.scrape import ScrapeSource, ScrapeJob
from app.models.dispensary import Dispensary
from app.models.deal import Deal
from app.models.user import User
from app.models.organization import Organization
from app.schemas.user import UserOut
from app.schemas.common import PaginatedResponse
from app.api.deps import require_super_admin, require_admin, get_current_user

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats")
async def platform_stats(db: AsyncSession = Depends(get_db), _: User = Depends(require_admin)):
    stats = {}
    stats["dispensaries"] = (await db.execute(select(func.count()).select_from(Dispensary).where(Dispensary.status == "active"))).scalar()
    stats["active_deals"] = (await db.execute(select(func.count()).select_from(Deal).where(Deal.is_active == True))).scalar()
    stats["total_deals_ever"] = (await db.execute(select(func.count()).select_from(Deal))).scalar()
    stats["users"] = (await db.execute(select(func.count()).select_from(User))).scalar()
    stats["scrape_sources"] = (await db.execute(select(func.count()).select_from(ScrapeSource).where(ScrapeSource.is_active == True))).scalar()

    last_job = (await db.execute(select(ScrapeJob).order_by(ScrapeJob.created_at.desc()).limit(1))).scalar_one_or_none()
    stats["last_scrape"] = last_job.completed_at.isoformat() if last_job and last_job.completed_at else None

    return stats


@router.get("/scrapers")
async def list_scrapers(db: AsyncSession = Depends(get_db), _: User = Depends(require_admin)):
    rows = (await db.execute(
        select(ScrapeSource, Dispensary)
        .join(Dispensary, ScrapeSource.dispensary_id == Dispensary.id)
        .order_by(Dispensary.name)
    )).all()

    return [{
        "id": src.id,
        "dispensary_id": src.dispensary_id,
        "dispensary_name": disp.name,
        "platform": src.platform,
        "source_url": src.source_url,
        "is_active": src.is_active,
        "last_scrape_at": src.last_scrape_at,
        "next_scrape_at": src.next_scrape_at,
    } for src, disp in rows]


@router.post("/scrapers/{source_id}/run")
async def trigger_scrape(source_id: str, db: AsyncSession = Depends(get_db), _: User = Depends(require_admin)):
    from app.tasks.scrape_tasks import run_scrape_source
    result = await db.execute(select(ScrapeSource).where(ScrapeSource.id == source_id))
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Scrape source not found")

    run_scrape_source.delay(source_id)
    return {"message": f"Scrape triggered for source {source_id}"}


@router.get("/scrape-jobs")
async def list_scrape_jobs(
    page: int = 1,
    per_page: int = 50,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    q = select(ScrapeJob, ScrapeSource, Dispensary).join(ScrapeSource, ScrapeJob.source_id == ScrapeSource.id).join(Dispensary, ScrapeSource.dispensary_id == Dispensary.id)
    count_q = select(func.count()).select_from(ScrapeJob)

    if status:
        q = q.where(ScrapeJob.status == status)
        count_q = count_q.where(ScrapeJob.status == status)

    total = (await db.execute(count_q)).scalar()
    rows = (await db.execute(q.offset((page - 1) * per_page).limit(per_page).order_by(ScrapeJob.created_at.desc()))).all()

    data = [{
        "id": job.id,
        "dispensary_name": disp.name,
        "platform": src.platform,
        "status": job.status,
        "deals_found": job.deals_found,
        "items_found": job.items_found,
        "started_at": job.started_at,
        "completed_at": job.completed_at,
        "errors": job.errors,
    } for job, src, disp in rows]

    return PaginatedResponse(data=data, total=total, page=page, per_page=per_page, pages=-(-total // per_page))


@router.get("/users", response_model=PaginatedResponse[UserOut])
async def list_all_users(
    page: int = 1,
    per_page: int = 50,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_super_admin),
):
    total = (await db.execute(select(func.count()).select_from(User))).scalar()
    users = (await db.execute(select(User).offset((page - 1) * per_page).limit(per_page).order_by(User.created_at.desc()))).scalars().all()
    return PaginatedResponse(data=[UserOut.model_validate(u) for u in users], total=total, page=page, per_page=per_page, pages=-(-total // per_page))
