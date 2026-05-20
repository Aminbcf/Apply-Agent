from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database import init_db
from routers.cv import router as cv_router
from routers.dashboard import router as dashboard_router
from routers.onboarding import router as onboarding_router
from routers.profile import router as profile_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    import models  # noqa: F401 - Ensure models are imported before init_db
    await init_db()
    yield

app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

app.include_router(cv_router)
app.include_router(dashboard_router)
app.include_router(onboarding_router)
app.include_router(profile_router)
