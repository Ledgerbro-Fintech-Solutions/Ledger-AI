import uuid
import threading
import time
from typing import Dict, Optional, Any
from dataclasses import dataclass
from langchain_community.vectorstores import FAISS


@dataclass
class SessionData:
    """Data structure for storing session information"""
    session_id: str
    vector_store: FAISS
    agent: Any
    created_at: float
    last_accessed: float


class SessionManager:
    """Thread-safe session manager for handling concurrent requests"""
    
    def __init__(self, session_timeout: int = 3600):  # 1 hour default timeout
        self._sessions: Dict[str, SessionData] = {}
        self._lock = threading.RLock()
        self.session_timeout = session_timeout
    
    def create_session(self, vector_store: FAISS, agent: Any) -> str:
        """
        Create a new session with vector store and agent
        Returns:
            Session ID string
        """
        session_id = str(uuid.uuid4())
        current_time = time.time()
        
        with self._lock:
            session_data = SessionData(
                session_id=session_id,
                vector_store=vector_store,
                agent=agent,
                created_at=current_time,
                last_accessed=current_time
            )
            self._sessions[session_id] = session_data
            
            # Clean up expired sessions
            self._cleanup_expired_sessions()
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[SessionData]:
        """
        Get session data by session ID
        Returns:
            SessionData if found and not expired, None otherwise
        """
        with self._lock:
            session_data = self._sessions.get(session_id)
            
            if session_data is None:
                return None
            
            # Check if session has expired
            if time.time() - session_data.last_accessed > self.session_timeout:
                del self._sessions[session_id]
                return None
            
            # Update last accessed time
            session_data.last_accessed = time.time()
            return session_data
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session
        Returns:
            True if session was deleted, False if not found
        """
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                return True
            return False
    
    def _cleanup_expired_sessions(self):
        """Clean up expired sessions (called with lock held)"""
        current_time = time.time()
        expired_sessions = [
            session_id for session_id, session_data in self._sessions.items()
            if current_time - session_data.last_accessed > self.session_timeout
        ]
        
        for session_id in expired_sessions:
            del self._sessions[session_id]
    
    def get_active_sessions_count(self) -> int:
        """Get the number of active sessions"""
        with self._lock:
            self._cleanup_expired_sessions()
            return len(self._sessions)
    
    def cleanup_all_sessions(self):
        """Clear all sessions (useful for testing or shutdown)"""
        with self._lock:
            self._sessions.clear()


# Global session manager instance
session_manager = SessionManager()
