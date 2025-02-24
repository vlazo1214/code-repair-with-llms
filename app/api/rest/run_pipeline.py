from fastapi import APIRouter, HTTPException, Query
from typing import List
from app.core.session_manager import SessionManager

def run_pipeline(session_manager: SessionManager) -> APIRouter:

    api_router = APIRouter()

    @api_router.post("/run-pipeline")
    async def run_pipeline(
        session_token: str = Query(default="", description="JWT Token of User running pipeline")
    ) -> bool:
        '''
        API Endpoint handles the start and running of the LLM pipeline

        Parameters:
        - session_token: JWT Token of User running pipeline

        Returns:
        - Run_Status: Boolean if run startup was successful
        '''

        # Validate session token of user
        session_id = session_manager.validate_session(session_token)
        if not session_id:
            return False
        
        # Get File Path of Users files
        file_path = session_manager.get_session_path(session_id=session_id)
        if not file_path:
            return False
        
        model = session_manager.get_model(session_token)
        if not model:
            return False
        
        # Forward File path into Pipeline Class and run
        
        # pipeline = Pipeline(file_path, model, session_token)
        # pipeline_status = pipeline.start()


        # if successful return True else False
        return pipeline_status

    return api_router
