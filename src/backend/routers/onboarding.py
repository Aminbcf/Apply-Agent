from fastapi import APIRouter

router = APIRouter(prefix="/onboarding", tags=["onboarding"])

@router.get("/status")
async def get_onboarding_status():
    return {"status": "pending", "steps_completed": 0}
