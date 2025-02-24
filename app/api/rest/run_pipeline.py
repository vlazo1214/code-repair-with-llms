from fastapi import APIRouter, HTTPException, Query
from typing import List
from app.core.session_manager import SessionManager
from app.pipeline import Pipeline

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
        
        # Initialize and run the pipeline
        try:
            pipeline = Pipeline()
            pipeline.set_model(model_selection=model)
            pipeline.set_rag()

            with open(file_path, 'r') as file:
                code_content = file.read()

            # Embed code
            code_files = [{"filename": file_path, "content": code_content}]
            pipeline.rag.embed_code(code_files)

            # Run the steps
            localization = pipeline.fault_localization(code_content)
            patterns = pipeline.pattern_matching(localization)
            patch_dir = pipeline.patch_generation(code_content, patterns)
            status, issues, corrections, explanation = pipeline.patch_validation(localization)

            # Return True if the pipeline executed successfully
            return True  

        except Exception as e:
            print(f"Pipeline execution error: {e}")
            return False

    return api_router
