import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from database import Base, get_db
from main import app
from models.job_application import JobApplication
from models.user_profile import UserProfile

# Mark all tests in this file as async using anyio
pytestmark = pytest.mark.anyio

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
test_session_factory = async_sessionmaker(
    test_engine, expire_on_commit=False, class_=AsyncSession
)


@pytest.fixture(autouse=True)
async def setup_test_db():
    """Create a clean in-memory database schema before each test."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def override_get_db():
    """Dependency override that yields a test database session."""
    async with test_session_factory() as session:
        yield session


# Override the database dependency in the FastAPI application
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
async def client():
    """AsyncClient fixture for making asynchronous requests to the FastAPI application."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="https://test") as ac:
        yield ac


async def test_onboarding_default_status(client):
    """Test the default onboarding status when no profile exists."""
    response = await client.get("/onboarding/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "pending"
    assert data["steps_completed"] == 0


async def test_profile_default_get(client):
    """Test getting profile when none exists returns a blank schema."""
    response = await client.get("/profile/")
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] is None
    assert data["email"] is None
    assert data["experience"] == []
    assert data["skills"] == {}


async def test_profile_save_and_retrieve(client):
    """Test saving a profile and then retrieving it."""
    profile_payload = {
        "full_name": "Test User",
        "email": "test@example.com",
        "phone": "1234567890",
        "location": "San Francisco, CA",
        "experience": [{"role": "Software Engineer", "years": 2}],
        "skills": {"languages": ["Python", "JavaScript"]},
        "career_goals": "Build great tools",
    }

    # Save profile
    response = await client.post("/profile/", json=profile_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Test User"
    assert data["email"] == "test@example.com"
    assert data["experience"] == [{"role": "Software Engineer", "years": 2}]
    assert data["skills"] == {"languages": ["Python", "JavaScript"]}

    # Retrieve profile
    response = await client.get("/profile/")
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Test User"
    assert data["email"] == "test@example.com"

    # Check onboarding status updates
    response = await client.get("/onboarding/status")
    assert response.status_code == 200
    data = response.json()
    # Name/email filled (step 1), experience/skills filled (step 2), career_goals filled (step 3)
    assert data["status"] == "completed"
    assert data["steps_completed"] == 3


async def test_dashboard_stats(client):
    """Test that dashboard stats dynamically count job applications."""
    # Default stats
    response = await client.get("/dashboard/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["active_applications"] == 0

    # Add a job application directly via DB session to verify count
    async with test_session_factory() as session:
        app1 = JobApplication(
            company_name="Google",
            job_title="Software Engineer",
            job_description="Coding stuff",
            status="active",
        )
        app2 = JobApplication(
            company_name="Meta",
            job_title="Product Manager",
            job_description="Planning stuff",
            status="archived",
        )
        session.add(app1)
        session.add(app2)
        await session.commit()

    # Query stats again
    response = await client.get("/dashboard/stats")
    assert response.status_code == 200
    data = response.json()
    # active_applications should count non-archived ones
    assert data["active_applications"] == 1


async def test_onboarding_cv_upload_txt_updates_profile(client):
    cv_text = (
        "Summary\n"
        "Experienced engineer.\n\n"
        "Experience\n"
        "Software Engineer\n"
        "Acme Corp\n"
        "City, State\n"
        "Did stuff\n\n"
        "Skills\n"
        "Python, TypeScript, FastAPI\n"
    )

    files = {
        "file": ("cv.txt", cv_text.encode("utf-8"), "text/plain"),
    }
    response = await client.post("/onboarding/cv", files=files)
    assert response.status_code == 200
    data = response.json()

    assert data["experience"] != []
    assert "general" in data["skills"]
    assert "Python" in data["skills"]["general"]

    status = await client.get("/onboarding/status")
    assert status.status_code == 200
    status_data = status.json()
    assert status_data["steps_completed"] >= 1
