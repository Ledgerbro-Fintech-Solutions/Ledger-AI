import uuid
import threading
import time
from typing import Dict, Optional, Any
from dataclasses import dataclass
from langchain_community.vectorstores import FAISS
from backend.app.core.logging import logger

@dataclass
class SessionData:
    session_id: str
    vector_store: FAISS
    agent: Any
    created_at: float
    last_accessed: float
    files_processed: int = 1

class SessionManager:
    """Thread-safe session manager for handling concurrent RAG sessions."""

    def __init__(self, session_timeout: int = 3600):
        self._sessions: Dict[str, SessionData] = {}
        self._lock = threading.RLock()
        self.session_timeout = session_timeout

    def create_session(self, vector_store: FAISS, agent: Any, files_processed: int = 1) -> str:
        session_id = str(uuid.uuid4())
        current_time = time.time()

        with self._lock:
            session_data = SessionData(
                session_id=session_id,
                vector_store=vector_store,
                agent=agent,
                created_at=current_time,
                last_accessed=current_time,
                files_processed=files_processed
            )
            self._sessions[session_id] = session_data
            self._cleanup_expired_sessions()

        logger.info(f"Created new chat session: {session_id} (active: {len(self._sessions)})")
        return session_id

    def get_session(self, session_id: str) -> Optional[SessionData]:
        with self._lock:
            session_data = self._sessions.get(session_id)
            if session_data is None:
                return None

            if time.time() - session_data.last_accessed > self.session_timeout:
                del self._sessions[session_id]
                logger.info(f"Session {session_id} expired and removed.")
                return None

            session_data.last_accessed = time.time()
            return session_data

    def delete_session(self, session_id: str) -> bool:
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                return True
            return False

    def _cleanup_expired_sessions(self):
        current_time = time.time()
        expired_sessions = [
            sid for sid, data in self._sessions.items()
            if current_time - data.last_accessed > self.session_timeout
        ]
        for sid in expired_sessions:
            del self._sessions[sid]

    def cleanup_all_sessions(self):
        with self._lock:
            count = len(self._sessions)
            self._sessions.clear()
            logger.info(f"Cleared all {count} active sessions.")

    def get_active_sessions_count(self) -> int:
        with self._lock:
            self._cleanup_expired_sessions()
            return len(self._sessions)

session_manager = SessionManager()
