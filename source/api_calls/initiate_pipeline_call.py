import requests
import os

API_URL = "http://localhost:8000/api/initiate_pipeline"

def initiate_pipeline_call(file_path, pipeline_steps):
    if isinstance(file_path, str):
        # Handle string path input
        file_name = os.path.basename(file_path)
        with open(file_path, 'rb') as file:
            files_to_send = [
                ("files", (file_name, file.read(), 'application/octet-stream'))
            ]
    else:
        # Handle file object input
        files_to_send = [
            ("files", (file_path.name, file_path.read(), file_path.type))
        ]
    
    response = requests.post(
        f"{API_URL}?pipeline_steps={pipeline_steps}", 
        files=files_to_send
    )
    
    if response.status_code == 200:
        return f"Success: {response.json()}"
    else:
        return f"Error: {response.json().get('detail', 'Unknown error')}"