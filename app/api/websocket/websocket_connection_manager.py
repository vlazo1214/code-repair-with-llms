from fastapi import WebSocket, WebSocketDisconnect

class WebSocketConnectionManager:
    '''
        Manages websockets that are connected
        to the backend server
    '''

    def __init__(self):
        self.active_connections: Dict[str, Websocket] = {}

    async def connect(self, websocket: WebSocket, session_token: str):
        self.active_connections[session_token] = websocket
        print(f"Connection established for session: {session_token}")

    def disconnect(self, websocket: WebSocket):
        session_token = next((sid for sid, ws in self.active_connections.items() if ws == websocket), None)
        if session_token:
            del self.active_connections[session_token]
            print(f"Connection removed for session: {session_token}")

    def get_websocket(self, session_token: str) -> WebSocket:
        return self.active_connections.get(session_token)

