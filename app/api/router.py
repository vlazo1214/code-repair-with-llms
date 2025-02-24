from fastapi import APIRouter
from app.api.rest.initiate_pipeline import initiate_pipeline
from app.api.rest.run_pipeline import run_pipeline
from app.api.rest.download_output import download_output
from app.core.session_manager import SessionManager
from app.api.websocket.websocket_connection_manager import WebSocketConnectionManager

'''
    Router for defined API endpoints
'''
def api_router(session_manager: SessionManager, websocket_connection_manager: WebSocketConnectionManager) -> APIRouter:
    api_router = APIRouter()

    api_router.include_router(initiate_pipeline(session_manager), prefix="/api", tags=["Files"])
    api_router.include_router(run_pipeline(session_manager), prefix="/api")
    api_router.include_router(download_output(session_manager, websocket_connection_manager), prefix="/api")
    
    return api_router
