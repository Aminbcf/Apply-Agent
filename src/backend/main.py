import logging

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database import init_db
from routers.cv import router as cv_router
from api.llm_router import router as llm_router
from api.job_router import router as job_router
from api.stream_router import router as stream_router
from api.settings_router import router as settings_router
from api.interview_router import router as interview_router
from routers.dashboard import router as dashboard_router
from routers.onboarding import router as onboarding_router
from routers.profile import router as profile_router
import model_registry

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    import models  # noqa: F401 - Ensure models are imported before init_db
    await init_db()

    # Eagerly load all ML models (LLM, embeddings, domain manager)
    logger.info("Loading ML models at startup …")
    await model_registry.initialize()
    logger.info("ML models ready.")

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
def health() -> dict[str, str | bool]:
    return {"status": "ok", "models_ready": model_registry.is_ready()}

app.include_router(cv_router)
app.include_router(llm_router)
app.include_router(job_router)
app.include_router(stream_router)
app.include_router(interview_router)
app.include_router(dashboard_router)
app.include_router(onboarding_router)
app.include_router(profile_router)
app.include_router(settings_router)

