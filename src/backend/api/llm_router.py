from fastapi import APIRouter, Body
from AI.llm.rag_service import RAGService

router = APIRouter()

# Simple endpoint that uses RAGService
@router.post("/generate/{scenario}")
async def generate_response(scenario: str, user_query: str = Body(..., embed=True), session_id: str = Body(...)):
    service = RAGService()
    response = service.generate(session_id=session_id, scenario=scenario, user_query=user_query)
    return {"response": response}
