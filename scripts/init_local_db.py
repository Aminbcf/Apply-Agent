"""
Initialize the local SQLite database and optionally seed a sample profile and job.
Run: python scripts/init_local_db.py
"""
import asyncio
from pathlib import Path
import uuid
import sys

# Ensure backend code is on PYTHONPATH
ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / 'src' / 'backend'
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from database import Base, engine, async_session_factory
from models.user_profile import UserProfile
from models.job_application import JobApplication
from config import settings

async def init():
    print(f"Database file: {settings.database_path}")
    settings.database_path.parent.mkdir(parents=True, exist_ok=True)
    async with engine.begin() as conn:
        print("Creating database tables...")
        await conn.run_sync(Base.metadata.create_all)

    # Seed a sample profile and job only if none exist
    from sqlalchemy import select, func, inspect, text
    # Determine existing columns using a PRAGMA query (SQLite-friendly and async-safe)
    col_names = []

    async with async_session_factory() as session:
        # Query PRAGMA table_info to collect current columns
        try:
            pragma = await session.execute(text("PRAGMA table_info('job_applications')"))
            rows = pragma.fetchall()
            col_names = [row[1] for row in rows] if rows else []
        except Exception:
            col_names = []

        # Add the new column if the schema is older
        if 'user_profile_id' not in col_names:
            print('Adding user_profile_id column to job_applications table...')
            await session.execute(text('ALTER TABLE job_applications ADD COLUMN user_profile_id VARCHAR'))

        result = await session.execute(select(func.count()).select_from(UserProfile))
        count = int(result.scalar_one())
        if count == 0:
            print("Seeding sample user profile and job...")
            profile = UserProfile(
                full_name="Jane Doe",
                email="jane.doe@example.com",
                phone="+1-555-0100",
                location="San Francisco, CA",
                raw_cv_text=None,
            )
            session.add(profile)

            job = JobApplication(
                id=uuid.uuid4(),
                company_name="ExampleCorp",
                job_title="Software Engineer",
                job_description="Build backend services.",
                processing=False,
                workflow_status="pending",
            )
            session.add(job)
            await session.commit()
            print("Seeded sample data.")
        else:
            print("User profiles already exist; skipping seeding.")

if __name__ == '__main__':
    asyncio.run(init())
    print("Done.")
