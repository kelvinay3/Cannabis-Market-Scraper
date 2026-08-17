import asyncio
import json
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

from celery import shared_task
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.models.scrape import ScrapeSource, ScrapeJob
from app.models.deal import Deal, DealHistory
from app.models.menu_item import MenuItem, PriceChange
from app.models.dispensary import Dispensary
from app.models.alert import Alert, AlertEvent
from app.scrapers import SCRAPER_MAP
from app.scrapers.crc_registry import CRCRegistryScraper
from app.tasks.celery_app import celery_app

settings = get_settings()


def get_async_session():
    engine = create_async_engine(settings.database_url, echo=False)
    return sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


def run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, name="app.tasks.scrape_tasks.scrape_all_sources", max_retries=3)
def scrape_all_sources(self):
    async def _run():
        Session = get_async_session()
        async with Session() as db:
            sources = (await db.execute(
                select(ScrapeSource).where(ScrapeSource.is_active == True)
            )).scalars().all()
            for source in sources:
                next_at = source.next_scrape_at
                if next_at and next_at > datetime.now(timezone.utc):
                    continue
                run_scrape_source.delay(str(source.id))
    run_async(_run())


@celery_app.task(bind=True, name="app.tasks.scrape_tasks.run_scrape_source", max_retries=3)
def run_scrape_source(self, source_id: str):
    async def _run():
        Session = get_async_session()
        async with Session() as db:
            source = (await db.execute(select(ScrapeSource).where(ScrapeSource.id == source_id))).scalar_one_or_none()
            if not source:
                return

            job = ScrapeJob(
                id=str(uuid.uuid4()),
                source_id=source_id,
                status="running",
                started_at=datetime.now(timezone.utc),
            )
            db.add(job)
            await db.commit()

            errors = []
            deals_found = 0
            items_found = 0

            try:
                ScraperClass = SCRAPER_MAP.get(source.platform)
                if not ScraperClass:
                    raise ValueError(f"Unknown platform: {source.platform}")

                dispensary = (await db.execute(
                    select(Dispensary).where(Dispensary.id == source.dispensary_id)
                )).scalar_one_or_none()
                if not dispensary:
                    raise ValueError(f"Dispensary not found: {source.dispensary_id}")

                store_config = {**(source.config or {}), "dispensary_id": str(dispensary.id)}
                if source.platform == "jane":
                    store_config["jane_store_id"] = dispensary.jane_store_id
                elif source.platform == "dutchie":
                    store_config["dutchie_id"] = dispensary.dutchie_id
                elif source.platform == "weedmaps":
                    store_config["weedmaps_id"] = dispensary.weedmaps_id
                elif source.platform == "leafly":
                    store_config["leafly_slug"] = dispensary.leafly_slug
                elif source.platform == "treez":
                    store_config["treez_endpoint"] = dispensary.treez_id

                async with ScraperClass() as scraper:
                    raw_deals = await scraper.fetch_deals(store_config)
                    raw_menu = await scraper.fetch_menu(store_config)

                deals_found = await _upsert_deals(db, dispensary, source, raw_deals)
                items_found = await _upsert_menu(db, dispensary, source, raw_menu)

                now = datetime.now(timezone.utc)
                source.last_scrape_at = now
                source.next_scrape_at = now + timedelta(minutes=15)
                job.status = "completed"
                job.completed_at = now
                job.deals_found = deals_found
                job.items_found = items_found

            except Exception as e:
                errors.append(str(e))
                job.status = "failed"
                job.completed_at = datetime.now(timezone.utc)
                job.errors = errors
                print(f"[scrape_task] Error for source {source_id}: {e}")
                raise self.retry(exc=e, countdown=60)

            finally:
                job.errors = errors or None
                await db.commit()

    run_async(_run())


async def _upsert_deals(db: AsyncSession, dispensary: Dispensary, source: ScrapeSource, raw_deals: list[dict]) -> int:
    count = 0
    now = datetime.now(timezone.utc)
    new_deals = []

    for raw in raw_deals:
        external_id = raw.get("external_id", "")
        existing = (await db.execute(
            select(Deal).where(
                and_(
                    Deal.dispensary_id == dispensary.id,
                    Deal.source_platform == source.platform,
                    Deal.external_id == external_id,
                )
            )
        )).scalar_one_or_none()

        if existing:
            changed_fields = {}
            for field in ["title", "description", "deal_type", "discount_value", "discount_unit",
                          "minimum_purchase", "applicable_categories", "applicable_brands",
                          "day_of_week", "starts_at", "ends_at"]:
                new_val = raw.get(field)
                old_val = getattr(existing, field, None)
                if new_val != old_val:
                    changed_fields[field] = {"old": old_val, "new": new_val}

            if changed_fields:
                old_data = {f: v["old"] for f, v in changed_fields.items()}
                for field, vals in changed_fields.items():
                    setattr(existing, field, vals["new"])
                existing.updated_at = now
                history = DealHistory(
                    id=str(uuid.uuid4()),
                    deal_id=existing.id,
                    change_type="modified",
                    old_data=old_data,
                    new_data={f: v["new"] for f, v in changed_fields.items()},
                    changed_at=now,
                )
                db.add(history)

            if not existing.is_active:
                existing.is_active = True
                db.add(DealHistory(
                    id=str(uuid.uuid4()),
                    deal_id=existing.id,
                    change_type="reactivated",
                    changed_at=now,
                ))
        else:
            deal = Deal(
                id=str(uuid.uuid4()),
                dispensary_id=dispensary.id,
                source_platform=source.platform,
                external_id=external_id,
                title=raw.get("title", ""),
                description=raw.get("description", ""),
                deal_type=raw.get("deal_type", "other"),
                discount_value=raw.get("discount_value"),
                discount_unit=raw.get("discount_unit", "other"),
                minimum_purchase=raw.get("minimum_purchase"),
                applicable_categories=raw.get("applicable_categories", []),
                applicable_brands=raw.get("applicable_brands", []),
                day_of_week=raw.get("day_of_week", []),
                starts_at=raw.get("starts_at"),
                ends_at=raw.get("ends_at"),
                raw_text=raw.get("raw_text", ""),
                is_active=True,
                first_seen_at=now,
            )
            db.add(deal)
            db.add(DealHistory(
                id=str(uuid.uuid4()),
                deal_id=deal.id,
                change_type="created",
                new_data=raw,
                changed_at=now,
            ))
            new_deals.append(deal)
            count += 1

    seen_external_ids = {r.get("external_id") for r in raw_deals}
    active_deals = (await db.execute(
        select(Deal).where(
            and_(
                Deal.dispensary_id == dispensary.id,
                Deal.source_platform == source.platform,
                Deal.is_active == True,
            )
        )
    )).scalars().all()

    for d in active_deals:
        if d.external_id not in seen_external_ids:
            d.is_active = False
            db.add(DealHistory(
                id=str(uuid.uuid4()),
                deal_id=d.id,
                change_type="deactivated",
                changed_at=now,
            ))

    await db.commit()

    if new_deals:
        evaluate_pending_alerts.delay(
            new_deal_ids=[d.id for d in new_deals],
            dispensary_id=str(dispensary.id),
        )

    return count


async def _upsert_menu(db: AsyncSession, dispensary: Dispensary, source: ScrapeSource, raw_items: list[dict]) -> int:
    count = 0
    now = datetime.now(timezone.utc)

    for raw in raw_items:
        external_id = raw.get("external_id", "")
        existing = (await db.execute(
            select(MenuItem).where(
                and_(
                    MenuItem.dispensary_id == dispensary.id,
                    MenuItem.external_id == external_id,
                )
            )
        )).scalar_one_or_none()

        if existing:
            old_price = float(existing.current_price) if existing.current_price else None
            new_price = raw.get("current_price")
            if new_price and old_price and float(new_price) != old_price:
                change_amount = float(new_price) - old_price
                change_pct = (change_amount / old_price) * 100 if old_price else 0
                db.add(PriceChange(
                    id=str(uuid.uuid4()),
                    item_id=existing.id,
                    dispensary_id=dispensary.id,
                    old_price=old_price,
                    new_price=float(new_price),
                    change_amount=change_amount,
                    change_pct=change_pct,
                    change_type="increase" if change_amount > 0 else "decrease",
                    detected_at=now,
                ))
            for field in ["name", "brand", "category", "thc_percent", "cbd_percent",
                          "weight", "current_price", "sale_price"]:
                setattr(existing, field, raw.get(field))
            existing.updated_at = now
        else:
            item = MenuItem(
                id=str(uuid.uuid4()),
                dispensary_id=dispensary.id,
                external_id=external_id,
                name=raw.get("name", ""),
                brand=raw.get("brand", ""),
                category=raw.get("category", ""),
                thc_percent=raw.get("thc_percent"),
                cbd_percent=raw.get("cbd_percent"),
                weight=raw.get("weight"),
                current_price=raw.get("current_price"),
                sale_price=raw.get("sale_price"),
                is_active=True,
                first_seen_at=now,
            )
            db.add(item)
            count += 1

    await db.commit()
    return count


@celery_app.task(name="app.tasks.scrape_tasks.sync_crc_registry")
def sync_crc_registry():
    async def _run():
        Session = get_async_session()
        async with Session() as db:
            async with CRCRegistryScraper() as scraper:
                listings = await scraper.get_all_nj_dispensaries()

            for listing in listings:
                name = listing.get("name", "").strip()
                if not name:
                    continue
                existing = (await db.execute(
                    select(Dispensary).where(Dispensary.name.ilike(f"%{name}%"))
                )).scalar_one_or_none()
                if not existing:
                    d = Dispensary(
                        id=str(uuid.uuid4()),
                        name=name,
                        address=listing.get("address", ""),
                        city=listing.get("city", ""),
                        county=listing.get("county", ""),
                        zip_code=listing.get("zip", ""),
                        state="NJ",
                        phone=listing.get("phone", ""),
                        website=listing.get("website", ""),
                        email=listing.get("email", ""),
                        status="pending",
                        med_only=listing.get("med_only", False),
                        license_number=listing.get("license_number", ""),
                    )
                    db.add(d)
            await db.commit()
    run_async(_run())


@celery_app.task(name="app.tasks.scrape_tasks.expire_stale_deals")
def expire_stale_deals():
    async def _run():
        Session = get_async_session()
        async with Session() as db:
            now = datetime.now(timezone.utc)
            stale = (await db.execute(
                select(Deal).where(
                    and_(
                        Deal.is_active == True,
                        Deal.ends_at != None,
                        Deal.ends_at < now,
                    )
                )
            )).scalars().all()
            for d in stale:
                d.is_active = False
                db.add(DealHistory(
                    id=str(uuid.uuid4()),
                    deal_id=d.id,
                    change_type="deactivated",
                    changed_at=now,
                ))
            await db.commit()
    run_async(_run())


@celery_app.task(name="app.tasks.scrape_tasks.evaluate_pending_alerts")
def evaluate_pending_alerts(new_deal_ids: list[str] = None, dispensary_id: str = None):
    async def _run():
        from app.services.email import send_deal_alert_email
        Session = get_async_session()
        async with Session() as db:
            alerts = (await db.execute(
                select(Alert).where(Alert.is_active == True)
            )).scalars().all()

            if not alerts or not new_deal_ids:
                return

            deals = (await db.execute(
                select(Deal, Dispensary)
                .join(Dispensary, Deal.dispensary_id == Dispensary.id)
                .where(Deal.id.in_(new_deal_ids))
            )).all()

            now = datetime.now(timezone.utc)

            for alert in alerts:
                from app.models.user import User
                user = (await db.execute(select(User).where(User.id == alert.user_id))).scalar_one_or_none()
                if not user:
                    continue

                matched = []
                for deal, disp in deals:
                    if not _deal_matches_alert(deal, disp, alert):
                        continue
                    matched.append({
                        "dispensary_name": disp.name,
                        "city": disp.city,
                        "county": disp.county,
                        "title": deal.title,
                        "deal_type": deal.deal_type,
                        "discount_value": deal.discount_value,
                    })

                if not matched:
                    continue

                if "email" in (alert.channels or []) and user.email:
                    await send_deal_alert_email(
                        to=user.email,
                        name=user.name or "",
                        alert_name=alert.name,
                        deals=matched,
                    )

                for deal, _ in [(d, di) for d, di in deals if _deal_matches_alert(d, di, alert)]:
                    db.add(AlertEvent(
                        id=str(uuid.uuid4()),
                        alert_id=alert.id,
                        deal_id=deal.id,
                        channels_used=alert.channels or [],
                        sent_at=now,
                    ))

            await db.commit()
    run_async(_run())


def _deal_matches_alert(deal: Deal, dispensary: Dispensary, alert: Alert) -> bool:
    if alert.trigger_type not in ("new_deal", "deal_change"):
        return False

    fconfig = alert.filter_config or {}

    if county_filter := fconfig.get("county"):
        if isinstance(county_filter, str):
            county_filter = [county_filter]
        if dispensary.county not in county_filter:
            return False

    if city_filter := fconfig.get("city"):
        if isinstance(city_filter, str):
            city_filter = [city_filter]
        if dispensary.city not in city_filter:
            return False

    if cat_filter := fconfig.get("categories"):
        deal_cats = deal.applicable_categories or []
        if not any(c in deal_cats for c in cat_filter):
            return False

    if deal_type_filter := fconfig.get("deal_types"):
        if deal.deal_type not in deal_type_filter:
            return False

    if min_discount := fconfig.get("min_discount"):
        if not deal.discount_value or deal.discount_value < min_discount:
            return False

    return True
