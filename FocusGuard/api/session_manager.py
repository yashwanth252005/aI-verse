"""
Session Manager
===============
Manages active monitoring sessions for institutional integration.

This module handles session lifecycle:
- Create new sessions
- Store session state (frame history, scores, events)
- Track session metadata
- Auto-expire old sessions
- Thread-safe access

Author: FocusGuard Team
Date: October 25, 2025
"""

import uuid
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import threading
from dataclasses import dataclass, field


@dataclass
class SessionData:
    """Data structure for a monitoring session."""
    
    # Session identification
    session_id: str
    institution_id: str
    exam_id: str
    student_id: str
    
    # Timestamps
    created_at: datetime
    last_activity: datetime
    ended_at: Optional[datetime] = None
    
    # Metadata
    metadata: Dict = field(default_factory=dict)
    
    # Monitoring data
    frames_processed: int = 0
    score_history: List[float] = field(default_factory=list)
    time_history: List[float] = field(default_factory=list)
    event_log: List[Dict] = field(default_factory=list)
    
    # Statistics
    device_detections: int = 0
    voice_detections: int = 0
    multiple_person_events: int = 0
    
    # Status
    status: str = "active"  # active, ended, expired
    
    # PDF report
    report_path: Optional[str] = None
    report_ready: bool = False


class SessionManager:
    """
    Thread-safe session manager for FocusGuard API.
    
    Stores all active sessions in memory (no database needed for hackathon!).
    For production, this could be Redis or PostgreSQL.
    
    Example:
        manager = SessionManager()
        session_id = manager.create_session("school_123", "exam_456", "student_789")
        session = manager.get_session(session_id)
        manager.add_frame_result(session_id, result)
        manager.end_session(session_id)
    """
    
    def __init__(self, max_sessions: int = 100, timeout_hours: int = 4):
        """
        Initialize session manager.
        
        Args:
            max_sessions: Maximum concurrent sessions
            timeout_hours: Hours before inactive session expires
        """
        self.sessions: Dict[str, SessionData] = {}
        self.lock = threading.Lock()
        self.max_sessions = max_sessions
        self.timeout_hours = timeout_hours
        
        print(f"✓ SessionManager initialized (max={max_sessions}, timeout={timeout_hours}h)")
    
    def create_session(
        self,
        institution_id: str,
        exam_id: str,
        student_id: str,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Create a new monitoring session.
        
        Args:
            institution_id: Institution identifier
            exam_id: Exam identifier
            student_id: Student identifier
            metadata: Optional metadata (exam_name, duration, etc.)
        
        Returns:
            session_id: Unique session identifier (UUID)
        
        Raises:
            RuntimeError: If max concurrent sessions reached
        """
        with self.lock:
            # Check session limit
            if len(self.sessions) >= self.max_sessions:
                # Try to clean up expired sessions first
                self._cleanup_expired_sessions()
                
                if len(self.sessions) >= self.max_sessions:
                    raise RuntimeError(
                        f"Maximum concurrent sessions ({self.max_sessions}) reached. "
                        f"Please try again later or end unused sessions."
                    )
            
            # Generate unique session ID
            session_id = str(uuid.uuid4())
            
            # Create session data
            now = datetime.now()
            session = SessionData(
                session_id=session_id,
                institution_id=institution_id,
                exam_id=exam_id,
                student_id=student_id,
                created_at=now,
                last_activity=now,
                metadata=metadata or {}
            )
            
            # Store session
            self.sessions[session_id] = session
            
            print(f"✓ Session created: {session_id[:8]}... ({len(self.sessions)} active)")
            
            return session_id
    
    def get_session(self, session_id: str) -> Optional[SessionData]:
        """
        Get session data by ID.
        
        Args:
            session_id: Session identifier
        
        Returns:
            SessionData or None if not found
        """
        with self.lock:
            session = self.sessions.get(session_id)
            
            if session:
                # Update last activity
                session.last_activity = datetime.now()
            
            return session
    
    def add_frame_result(self, session_id: str, result: Dict):
        """
        Add frame analysis result to session.
        
        Args:
            session_id: Session identifier
            result: Frame analysis result from FrameProcessor
        """
        session = self.get_session(session_id)
        
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        
        with self.lock:
            # Update counters
            session.frames_processed += 1
            
            # Add to history
            session.score_history.append(result.get('focus_score', 0))
            
            # Calculate elapsed time
            elapsed = (datetime.now() - session.created_at).total_seconds()
            session.time_history.append(elapsed)
            
            # Add alerts to event log (with deduplication handled by caller)
            if 'alerts' in result:
                for alert in result['alerts']:
                    session.event_log.append({
                        'time': datetime.now().strftime('%H:%M:%S'),
                        'type': 'ALERT',
                        'message': alert
                    })
    
    def end_session(self, session_id: str):
        """
        Mark session as ended.
        
        Args:
            session_id: Session identifier
        """
        session = self.get_session(session_id)
        
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        
        with self.lock:
            session.ended_at = datetime.now()
            session.status = "ended"
            
            print(f"✓ Session ended: {session_id[:8]}... "
                  f"({session.frames_processed} frames processed)")
    
    def delete_session(self, session_id: str):
        """
        Delete session (permanent removal).
        
        Args:
            session_id: Session identifier
        """
        with self.lock:
            if session_id in self.sessions:
                del self.sessions[session_id]
                print(f"✓ Session deleted: {session_id[:8]}...")
    
    def get_active_sessions(self) -> List[str]:
        """Get list of active session IDs."""
        with self.lock:
            return [
                sid for sid, session in self.sessions.items()
                if session.status == "active"
            ]
    
    def get_stats(self) -> Dict:
        """Get manager statistics."""
        with self.lock:
            active = sum(1 for s in self.sessions.values() if s.status == "active")
            ended = sum(1 for s in self.sessions.values() if s.status == "ended")
            
            return {
                "total": len(self.sessions),
                "active": active,
                "ended": ended,
                "max": self.max_sessions
            }
    
    def _cleanup_expired_sessions(self):
        """Remove expired sessions (called automatically)."""
        now = datetime.now()
        timeout_delta = timedelta(hours=self.timeout_hours)
        
        expired = []
        
        for session_id, session in list(self.sessions.items()):
            # Check if session expired
            time_since_activity = now - session.last_activity
            
            if time_since_activity > timeout_delta:
                expired.append(session_id)
        
        # Remove expired sessions
        for session_id in expired:
            session = self.sessions[session_id]
            session.status = "expired"
            del self.sessions[session_id]
        
        if expired:
            print(f"✓ Cleaned up {len(expired)} expired sessions")


# Global session manager instance
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """Get global session manager instance (singleton pattern)."""
    global _session_manager
    
    if _session_manager is None:
        _session_manager = SessionManager()
    
    return _session_manager


# ============================================================================
# Testing
# ============================================================================
if __name__ == "__main__":
    # Quick test
    manager = SessionManager(max_sessions=5, timeout_hours=1)
    
    # Create test session
    session_id = manager.create_session(
        institution_id="test_school",
        exam_id="test_exam",
        student_id="test_student",
        metadata={"exam_name": "Final Exam"}
    )
    
    print(f"Created session: {session_id}")
    
    # Get session
    session = manager.get_session(session_id)
    print(f"Session data: {session.institution_id}, {session.exam_id}")
    
    # Add some results
    for i in range(10):
        manager.add_frame_result(session_id, {'focus_score': 85 + i, 'alerts': []})
    
    print(f"Frames processed: {session.frames_processed}")
    print(f"Score history length: {len(session.score_history)}")
    
    # Stats
    print(f"Stats: {manager.get_stats()}")
    
    # End session
    manager.end_session(session_id)
    print(f"Session status: {session.status}")
