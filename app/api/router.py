from fastapi import APIRouter
from app.api.rest.initiate_pipeline import initiate_pipeline
from app.core.session_manager import SessionManager

'''
    Router for defined API endpoints
'''
def api_router(session_manager: SessionManager) -> APIRouter:
    api_router = APIRouter()
    api_router.include_router(initiate_pipeline(session_manager), prefix="/api", tags=["Files"])
    api_router.include_router(run_pipeline(session_manager), prefix="/api")
    return api_router
