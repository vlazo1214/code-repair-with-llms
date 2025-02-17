import requests
import os
import mimetypes

API_URL = "http://localhost:8000/api/initiate_pipeline"

def initiate_pipeline_call(files, pipeline_steps):
    """
    Initiate the pipeline with multiple files.
    
    Args:
        files: List of tuples containing file information (name, content, type)
        pipeline_steps: Integer representing selected pipeline steps
    """

    file_data = []
    
    for file in files:
        mime_type = mimetypes.guess_type(file.name)[0] or "application/octet-stream"
        
        # Ensure we send the actual file content
        with open(file.name, "rb") as f:
            file_data.append(("files", (file.name, f.read(), mime_type)))  

    try:
        response = requests.post(
            f"{API_URL}?pipeline_steps={pipeline_steps}", 
            files=file_data
        )
        
        response.raise_for_status()  # Raise exception for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        return f"Error: {str(e)}"