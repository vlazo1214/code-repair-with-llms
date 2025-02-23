from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
from pathlib import Path
from fastapi import HTTPException
from typing import List, Optional
from pydantic import BaseModel
import os

class SessionManager:
    """
    Manages user sessions
    """

    def __init__(self, secret_key: str, algorithm: str, upload_dir: Path, token_expiration_minutes: int = 60, model: any = "open_ai"):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.upload_dir = upload_dir
        self.model = model
        self.token_expiration_minutes = token_expiration_minutes

        self.upload_dir.mkdir(parents=True, exist_ok=True)

    '''
    ##############################
    Remove open_ai within the model param
    ##############################
    '''
    def create_session(self, selected_steps: List[int], model: any = "open_ai") -> str:

        now = datetime.now(tz=timezone.utc)

        expiration = now + timedelta(minutes=self.token_expiration_minutes)

        payload = {
            "exp": expiration,
            "iat": now,
            "sub": str(os.urandom(16).hex()),
            "selected_steps": selected_steps,
            "model": model,
        }

        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

        session_path: Path = (self.upload_dir / payload["sub"])
        session_path.mkdir(parents=True, exist_ok=True)

        return token
    
    def validate_session(self, token: str) -> str:

        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            session_id = payload.get("sub")

            if not session_id:
                raise HTTPException(status_code=400, detail="Invalid token payload")

            self.get_session_path(session_id)

            return session_id
        
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        
    
    def get_session_path(self, session_id: Optional[str] = None, token: Optional[str] = None) -> Path:

        if token and not session_id:
            session_id = self.validate_session(token)
        
        if not session_id:
            raise HTTPException(status_code=400, detail="Session ID or token is required")

        session_path = self.upload_dir / session_id
        if not session_path.exists():
            raise HTTPException(status_code=404, detail="Session dir not found")

        print(f"Session Path is: {session_path}")
        return session_path
    
    
    def get_selected_steps(self, token: str) -> List[int]:

        if not token:
            raise HTTPException(status_code=400, detail="Token is required")
        
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            steps = payload.get("selected_steps")

            if not steps:
                raise HTTPException(status_code=400, detail="Invalid token payload")

            return steps
        
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        
    def get_model(self, token: str) -> any:
    
        if not token:
            raise HTTPException(status_code=400, detail="Token is required")
        
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            model = payload.get("model")

            if not model:
                raise HTTPException(status_code=400, detail="Invalid token payload")

            return model
        
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

    def delete_session(self, session_id: str) -> None:

        session_path = self.upload_dir / session_id
        if session_path.exists():
            for file in session_path.iterdir():
                file.unlink()
            session_path.rmdir()