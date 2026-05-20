from fastapi import APIRouter

router = APIRouter(prefix="/profile", tags=["profile"])

@router.get("/")
async def get_profile():
    return {"status": "not_found"}
