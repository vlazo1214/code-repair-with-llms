from fastapi import APIRouter, HTTPException, Query, File,  Websocket
from typing import List
from app.core.session_manager import SessionManager
from app.api.websocket.websocket_connection_manager import WebSocketConnectionManager

def download_output(session_manager: SessionManager, websocket_connection_manager: WebSocketConnectionManager) -> APIRouter:

    api_router = APIRouter()

    @api_router.post("/download-output")
    async def download_output(
        session_token: str = Query(default="", description="JWT Token of User Running Pipeline")
    ) -> List[File]:
        '''
        API Endpoint that downloads any files within a sessions file pool

        Parameters:
        - session_token: JWT Token of User running pipeline

        Returns:
        - pipeline_output: Files that were produced from the pipeline
        '''

        pipeline_output = List

        # Validate session of user
        session_id = session_manager.validate_session(session_token=session_token)
        if not session_id:
            return pipeline_output
        
        # Retrieve the users websocket connection and get the files
        websocket = websocket_connection_manager.get_websocket(session_token=session_token)
        pipeline_output = websocket.get_files()

        # Either returns an empty List or List of files
        return pipeline_output
    
    return api_router
        
        