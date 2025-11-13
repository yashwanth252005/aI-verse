"""
Session Management Routes
=========================
API endpoints for creating and managing monitoring sessions.

Author: FocusGuard Team
Date: October 25, 2025
"""

from fastapi import APIRouter, HTTPException, status
from datetime import datetime, timedelta
from typing import Optional

from api.models import (
    SessionCreateRequest,
    SessionResponse,
    SessionDetailResponse,
    ErrorResponse
)
from api.session_manager import get_session_manager
from api.config import SESSION_TIMEOUT_HOURS

router = APIRouter()


# ============================================================================
# Session CRUD Endpoints
# ============================================================================

@router.post("/start", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(request: SessionCreateRequest):
    """
    Create a new monitoring session.
    
    This endpoint initiates a new proctoring session for a student.
    The session will remain active until explicitly ended or expires after 4 hours.
    
    **Example Request:**
    ```json
    {
        "institution_id": "university_123",
        "exam_id": "midterm_cs101",
        "student_id": "student_456",
        "metadata": {
            "exam_name": "Computer Science Midterm",
            "duration_minutes": 90
        }
    }
    ```
    
    **Returns:** Session ID and expiration time
    """
    try:
        manager = get_session_manager()
        
        # Create session
        session_id = manager.create_session(
            institution_id=request.institution_id,
            exam_id=request.exam_id,
            student_id=request.student_id,
            metadata=request.metadata or {}
        )
        
        # Get session details
        session = manager.get_session(session_id)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create session"
            )
        
        # Calculate expiration
        expires_at = session.created_at + timedelta(hours=SESSION_TIMEOUT_HOURS)
        
        return SessionResponse(
            session_id=session_id,
            status=session.status,
            created_at=session.created_at,
            expires_at=expires_at
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session: {str(e)}"
        )


@router.get("/{session_id}", response_model=SessionDetailResponse)
async def get_session(session_id: str):
    """
    Get detailed information about a session.
    
    **Returns:** Full session details including statistics and status
    """
    try:
        manager = get_session_manager()
        session = manager.get_session(session_id)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session not found: {session_id}"
            )
        
        return SessionDetailResponse(
            session_id=session.session_id,
            status=session.status,
            institution_id=session.institution_id,
            exam_id=session.exam_id,
            student_id=session.student_id,
            created_at=session.created_at,
            last_activity=session.last_activity,
            ended_at=session.ended_at,
            frames_processed=session.frames_processed,
            metadata=session.metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get session: {str(e)}"
        )


@router.post("/{session_id}/end", response_model=SessionDetailResponse)
async def end_session(session_id: str):
    """
    End a monitoring session.
    
    This marks the session as complete and triggers PDF report generation.
    After ending, no more frames can be analyzed for this session.
    
    **Returns:** Final session details
    """
    try:
        manager = get_session_manager()
        
        # End the session
        manager.end_session(session_id)
        
        # Get updated session
        session = manager.get_session(session_id)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session not found: {session_id}"
            )
        
        return SessionDetailResponse(
            session_id=session.session_id,
            status=session.status,
            institution_id=session.institution_id,
            exam_id=session.exam_id,
            student_id=session.student_id,
            created_at=session.created_at,
            last_activity=session.last_activity,
            ended_at=session.ended_at,
            frames_processed=session.frames_processed,
            metadata=session.metadata
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to end session: {str(e)}"
        )


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(session_id: str):
    """
    Delete a session permanently.
    
    **Warning:** This permanently removes all session data.
    Use with caution - typically you should end sessions rather than delete them.
    """
    try:
        manager = get_session_manager()
        
        # Check if session exists
        session = manager.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session not found: {session_id}"
            )
        
        # Delete the session
        manager.delete_session(session_id)
        
        return None  # 204 No Content
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete session: {str(e)}"
        )
