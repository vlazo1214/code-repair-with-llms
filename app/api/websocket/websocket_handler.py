from fastapi import WebSocket, WebSocketDisconnect
from app.api.websocket.websocket_connection_manager import WebSocketConnectionManager
from app.core.session_manager import SessionManager

import aiofiles
import os
import bson
import json

class WebSocketHandler:
    '''
        Handles individual websockets
    '''


    def __init__(self, session_manager: SessionManager):
        self.connection_manager = WebSocketConnectionManager()
        self.session_manager = session_manager
        self.pending_files = {}
        self.CONNECTED = True

    async def handle_connection(self, websocket: WebSocket):
        '''
        
        '''

        await websocket.accept()
        session_token = websocket.query_params.get("session_token")
        self.connection_manager.connect(websocket, session_token)

        try:
            # While connected to 
            while self.CONNECTED:

                # Checks for valid session
                session_token = websocket.query_params.get("session_token")
                await self.check_session_id(websocket, session_token)

                # Receive WebSocket data
                data = await websocket.receive()
                print(f"Received data: {data}")

                response = {"type": "message", "content": f"Server received: {data}"}
                await websocket.send_text(f"From the Server {data.get('text')}")

        except WebSocketDisconnect:
            self.connection_manager.disconnect(websocket)
            print("Client disconnected")

    async def check_session_id(self, websocket: WebSocket, session_token: str) -> bool:

            print(f"DEBUG: Received session_token: {session_token}")
            if not session_token:
                self.connection_manager.disconnect(websocket)
                await websocket.close(code=4001, reason="Session ID is missing")
                return
            
            if not self.session_manager.validate_session(session_token):
                self.connection_manager.disconnect(websocket)
                await websocket.close(code=4002, reason="Invalid or expired session ID")
                return
            
    async def send_file(self, websocket: WebSocket, file_path: str):
        '''
            Sends a file via websocket
        '''

        if not os.path.exists(file_path):
            await self.send_bson(websocket, {"type": "error", "content": "File not found"})
            return
        
        try:
            filename = os.path.basename(file_path)
            await websocket.send_text(f"START_FILE_TRANSFER: {filename}")

            async with aiofiles.open(file_path, "rb") as file:
                file_data = await file.read()

            bson_data = bson.BSON.encode({
                "type": "file",
                "filename": filename,
                "data": file_data
            })

            await websocket.send_bytes(bson_data)

        except Exception as e:
            await self.send_bson(websocket, {"type": "error", "content": str(e)})

    
    def notify_new_file(self, session_token: str, file_path: str):
        """
            Called by the LLM when new files of code snippets are available and ready
        """
        self.pending_files = file_path

    async def send_bson(self, websocket: WebSocket, message: dict):
        """
            Serializes and sends a BSON Message
        """
        bson_data = bson.BSON.encode(message)
        await websocket.send_bytes(bson_data)