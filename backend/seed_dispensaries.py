"""
Seeds known NJ cannabis dispensaries into the database.
Run after setup_admin.py: python seed_dispensaries.py
"""
import asyncio
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, text

from app.core.config import get_settings
from app.models.dispensary import Dispensary
from app.models.scrape import ScrapeSource

settings = get_settings()

NJ_DISPENSARIES = [
    {
        "name": "Curaleaf Bellmawr",
        "address": "810 S. Black Horse Pike",
        "city": "Bellmawr",
        "county": "Camden",
        "zip_code": "08031",
        "state": "NJ",
        "latitude": 39.8676,
        "longitude": -75.0966,
        "phone": "856-200-0700",
        "website": "https://curaleaf.com/shop/new-jersey/curaleaf-nj-bellmawr",
        "jane_store_id": "1150",
        "weedmaps_id": "curaleaf-bellmawr",
        "leafly_slug": "curaleaf-bellmawr",
        "med_only": False,
        "status": "active",
    },
    {
        "name": "Curaleaf Bordentown",
        "address": "2001 Route 206",
        "city": "Bordentown",
        "county": "Burlington",
        "zip_code": "08505",
        "state": "NJ",
        "latitude": 40.1376,
        "longitude": -74.7121,
        "phone": "609-291-0696",
        "website": "https://curaleaf.com/shop/new-jersey/curaleaf-nj-bordentown",
        "jane_store_id": "1152",
        "weedmaps_id": "curaleaf-bordentown",
        "leafly_slug": "curaleaf-bordentown",
        "med_only": False,
        "status": "active",
    },
    {
        "name": "Zen Leaf Elizabeth",
        "address": "250 US-1",
        "city": "Elizabeth",
        "county": "Union",
        "zip_code": "07208",
        "state": "NJ",
        "latitude": 40.6640,
        "longitude": -74.2107,
        "phone": "908-351-0011",
        "website": "https://zenleaf.com/elizabeth-nj",
        "jane_store_id": "1900",
        "weedmaps_id": "zen-leaf-elizabeth",
        "leafly_slug": "zen-leaf-elizabeth-nj",
        "med_only": False,
        "status": "active",
    },
    {
        "name": "Ascend Montclair",
        "address": "620 Bloomfield Ave",
        "city": "Montclair",
        "county": "Essex",
        "zip_code": "07042",
        "state": "NJ",
        "latitude": 40.8259,
        "longitude": -74.2088,
        "website": "https://ascendwellness.com/dispensary/montclair-nj",
        "jane_store_id": "2100",
        "weedmaps_id": "ascend-montclair",
        "leafly_slug": "ascend-wellness-montclair",
        "med_only": False,
        "status": "active",
    },
    {
        "name": "Columbia Care Vineland",
        "address": "2120 W. Landis Ave",
        "city": "Vineland",
        "county": "Cumberland",
        "zip_code": "08360",
        "state": "NJ",
        "latitude": 39.4868,
        "longitude": -74.9860,
        "website": "https://columbiacare.com/locations/nj-vineland",
        "weedmaps_id": "columbia-care-vineland",
        "leafly_slug": "columbia-care-vineland",
        "med_only": False,
        "status": "active",
    },
    {
        "name": "GTI/Rise Paterson",
        "address": "320 Getty Ave",
        "city": "Paterson",
        "county": "Passaic",
        "zip_code": "07503",
        "state": "NJ",
        "latitude": 40.9168,
        "longitude": -74.1715,
        "website": "https://risecannabisstores.com/dispensary/nj/paterson",
        "jane_store_id": "2400",
        "weedmaps_id": "rise-paterson",
        "leafly_slug": "rise-paterson-nj",
        "med_only": False,
        "status": "active",
    },
    {
        "name": "Greenleaf Compassion Center Boonton",
        "address": "66 Wootton St",
        "city": "Boonton",
        "county": "Morris",
        "zip_code": "07005",
        "state": "NJ",
        "latitude": 40.9018,
        "longitude": -74.4060,
        "website": "https://www.greenleafnj.com",
        "jane_store_id": "3100",
        "weedmaps_id": "greenleaf-boonton",
        "leafly_slug": "greenleaf-compassion-center-boonton",
        "med_only": False,
        "status": "active",
    },
    {
        "name": "Garden State Dispensary Woodbridge",
        "address": "2 Cotters Lane",
        "city": "Woodbridge",
        "county": "Middlesex",
        "zip_code": "08830",
        "state": "NJ",
        "latitude": 40.5576,
        "longitude": -74.2846,
        "website": "https://gsdispensary.com/woodbridge",
        "jane_store_id": "3500",
        "weedmaps_id": "garden-state-dispensary-woodbridge",
        "leafly_slug": "garden-state-dispensary-woodbridge",
        "med_only": False,
        "status": "active",
    },
    {
        "name": "Ayr Wellness Neptune",
        "address": "2108 NJ-66",
        "city": "Neptune",
        "county": "Monmouth",
        "zip_code": "07753",
        "state": "NJ",
        "latitude": 40.2087,
        "longitude": -74.0688,
        "website": "https://www.ayrwellness.com/locations/new-jersey/neptune",
        "jane_store_id": "4000",
        "weedmaps_id": "ayr-wellness-neptune",
        "leafly_slug": "ayr-neptune-nj",
        "med_only": False,
        "status": "active",
    },
    {
        "name": "Acreage Holdings / The Botanist Williamstown",
        "address": "1020 N. Black Horse Pike",
        "city": "Williamstown",
        "county": "Gloucester",
        "zip_code": "08094",
        "state": "NJ",
        "latitude": 39.6862,
        "longitude": -74.9985,
        "website": "https://www.thebotanist.com/locations/nj/williamstown",
        "jane_store_id": "4500",
        "weedmaps_id": "the-botanist-williamstown",
        "leafly_slug": "the-botanist-williamstown-nj",
        "med_only": False,
        "status": "active",
    },
    {
        "name": "Lume Cannabis Co. Cherry Hill",
        "address": "1000 Route 38",
        "city": "Cherry Hill",
        "county": "Camden",
        "zip_code": "08002",
        "state": "NJ",
        "latitude": 39.9342,
        "longitude": -75.0013,
        "website": "https://lumecannabis.com/stores/cherry-hill-nj",
        "jane_store_id": "5000",
        "weedmaps_id": "lume-cherry-hill",
        "leafly_slug": "lume-cherry-hill-nj",
        "med_only": False,
        "status": "active",
    },
    {
        "name": "Justice Cannabis Co. Ewing",
        "address": "1510 N. Olden Ave",
        "city": "Ewing",
        "county": "Mercer",
        "zip_code": "08638",
        "state": "NJ",
        "latitude": 40.2691,
        "longitude": -74.7973,
        "website": "https://www.justicecannabisco.com",
        "jane_store_id": "5500",
        "weedmaps_id": "justice-cannabis-ewing",
        "leafly_slug": "justice-cannabis-ewing-nj",
        "med_only": False,
        "status": "active",
    },
    {
        "name": "iAnthus NJ / Oasis Cannabis",
        "address": "230 N. Center St",
        "city": "Orange",
        "county": "Essex",
        "zip_code": "07050",
        "state": "NJ",
        "latitude": 40.7712,
        "longitude": -74.2338,
        "website": "https://www.oasiscannabis.com",
        "jane_store_id": "6000",
        "weedmaps_id": "oasis-cannabis-orange",
        "leafly_slug": "oasis-cannabis-orange-nj",
        "med_only": False,
        "status": "active",
    },
    {
        "name": "TerrAscend NJ / The Apothecarium Maplewood",
        "address": "2048 Millburn Ave",
        "city": "Maplewood",
        "county": "Essex",
        "zip_code": "07040",
        "state": "NJ",
        "latitude": 40.7307,
        "longitude": -74.2724,
        "website": "https://www.theapothecarium.com/new-jersey/maplewood",
        "jane_store_id": "6500",
        "weedmaps_id": "the-apothecarium-maplewood",
        "leafly_slug": "the-apothecarium-maplewood-nj",
        "med_only": False,
        "status": "active",
    },
    {
        "name": "Verano / Zen Leaf Hazlet",
        "address": "2400 NJ-35",
        "city": "Hazlet",
        "county": "Monmouth",
        "zip_code": "07730",
        "state": "NJ",
        "latitude": 40.4287,
        "longitude": -74.1957,
        "website": "https://zenleaf.com/hazlet-nj",
        "jane_store_id": "7000",
        "weedmaps_id": "zen-leaf-hazlet",
        "leafly_slug": "zen-leaf-hazlet-nj",
        "med_only": False,
        "status": "active",
    },
]


async def main():
    engine = create_async_engine(settings.database_url, echo=False)
    Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with Session() as db:
        seeded = 0
        for d_data in NJ_DISPENSARIES:
            existing = (await db.execute(
                select(Dispensary).where(Dispensary.name == d_data["name"])
            )).scalar_one_or_none()

            if existing:
                print(f"[seed] Already exists: {d_data['name']}")
                continue

            disp_id = str(uuid.uuid4())
            lat = d_data.pop("latitude", None)
            lng = d_data.pop("longitude", None)

            d = Dispensary(id=disp_id, **d_data)
            db.add(d)
            await db.flush()

            if lat and lng:
                await db.execute(
                    text(f"UPDATE dispensaries SET geom = ST_SetSRID(ST_MakePoint({lng}, {lat}), 4326) WHERE id = :id"),
                    {"id": disp_id},
                )

            platforms = []
            if d_data.get("jane_store_id"):
                platforms.append("jane")
            if d_data.get("dutchie_id"):
                platforms.append("dutchie")
            if d_data.get("weedmaps_id"):
                platforms.append("weedmaps")
            if d_data.get("leafly_slug"):
                platforms.append("leafly")

            for platform in platforms:
                src = ScrapeSource(
                    id=str(uuid.uuid4()),
                    dispensary_id=disp_id,
                    platform=platform,
                    is_active=True,
                )
                db.add(src)

            seeded += 1
            print(f"[seed] Added: {d_data['name']} ({', '.join(platforms)})")

        await db.commit()
        print(f"\n[seed] Done. Seeded {seeded} dispensaries.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
