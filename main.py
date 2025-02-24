from fastapi import FastAPI, WebSocket
from app.api.websocket.websocket_handler import WebSocketHandler
from app.api.router import api_router
from app.core.session_manager import SessionManager
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

app = FastAPI(
    title="Code Repair With LLM's",
    description="Backend server with LLM's"
)

# Allow all origins for testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Handles user sessions and session directories
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
UPLOAD_DIR = Path("./uploads")

session_manager = SessionManager(
    secret_key=SECRET_KEY,
    algorithm=ALGORITHM,
    upload_dir=UPLOAD_DIR,
    token_expiration_minutes=60,
)

# Manage websocket connections
websocket_manager = WebSocketHandler((session_manager))

# For REST Api's 
app.include_router(api_router(session_manager, websocket_connection_manager=websocket_manager))

# Websocket listener for continued connection to backend
@app.websocket("/start-llm-session")
async def websocket_endpoint(websocket: WebSocket):
    await websocket_manager.handle_connection(websocket)

