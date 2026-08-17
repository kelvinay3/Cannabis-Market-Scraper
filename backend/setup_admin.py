"""
Run once on first deploy to create the super-admin org and user.
Usage: python setup_admin.py
"""
import asyncio
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.core.config import get_settings
from app.core.security import hash_password
from app.models.organization import Organization
from app.models.user import User

settings = get_settings()


async def main():
    engine = create_async_engine(settings.database_url, echo=False)
    Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with Session() as db:
        existing = (await db.execute(select(User).where(User.email == settings.admin_email))).scalar_one_or_none()
        if existing:
            print(f"[setup] Admin user already exists: {settings.admin_email}")
            await engine.dispose()
            return

        org_id = str(uuid.uuid4())
        org = Organization(
            id=org_id,
            name="NJ Cannabis Intel — Admin",
            plan="enterprise",
            is_active=True,
        )
        db.add(org)

        admin_user = User(
            id=str(uuid.uuid4()),
            org_id=org_id,
            email=settings.admin_email,
            password_hash=hash_password(settings.admin_password),
            name="Platform Admin",
            role="super_admin",
            is_active=True,
        )
        db.add(admin_user)
        await db.commit()

        print(f"[setup] Created super_admin: {settings.admin_email}")
        print(f"[setup] Org ID: {org_id}")
        print(f"[setup] User ID: {admin_user.id}")
        print()
        print("  Login at: http://localhost:3000/login")
        print(f"  Email:    {settings.admin_email}")
        print(f"  Password: {settings.admin_password}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
