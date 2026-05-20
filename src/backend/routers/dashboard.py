from fastapi import APIRouter

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/stats")
async def get_dashboard_stats():
    return {
        "active_applications": 0,
        "generated_documents": 0,
        "interview_sessions": 0
    }
