"""
Frame Analysis Routes
=====================
API endpoints for analyzing webcam frames and detecting focus issues.

Author: FocusGuard Team
Date: October 25, 2025
"""

from fastapi import APIRouter, HTTPException, status, File, UploadFile, Form
from typing import Optional
import time
import io
import numpy as np
from PIL import Image

from api.models import FrameAnalysisResponse
from api.session_manager import get_session_manager
from api.config import MAX_FRAME_SIZE_MB, FRAME_ANALYSIS_TIMEOUT_SEC

router = APIRouter()


# ============================================================================
# Frame Processing
# ============================================================================

def process_frame_bytes(frame_bytes: bytes) -> dict:
    """
    Process frame bytes and return analysis results.
    
    TODO: This needs to be extracted from the Streamlit FrameProcessor.
    For now, returning mock data.
    
    Args:
        frame_bytes: Raw image bytes
        
    Returns:
        Analysis results dictionary
    """
    # TODO: Import and use actual FrameProcessor
    # from core.processor_service import ProcessorService
    # processor = ProcessorService()
    # result = processor.process_frame(frame_bytes)
    
    # Mock analysis for now
    return {
        "focus_score": 85,
        "status": "good",
        "face_detected": True,
        "face_count": 1,
        "device_detected": False,
        "device_type": None,
        "audio_anomaly": False,
        "gaze_direction": "forward",
        "alerts": []
    }


# ============================================================================
# Analysis Endpoints
# ============================================================================

@router.post("/{session_id}/analyze", response_model=FrameAnalysisResponse)
async def analyze_frame(
    session_id: str,
    frame: UploadFile = File(..., description="Webcam frame image (JPEG/PNG)"),
    timestamp: Optional[float] = Form(None, description="Frame timestamp (Unix time)")
):
    """
    Analyze a webcam frame for focus monitoring.
    
    This endpoint processes a single frame from the student's webcam and returns:
    - Focus score (0-100)
    - Face detection status
    - Device detection results
    - Gaze direction
    - Any alerts or violations
    
    **Usage:**
    ```javascript
    // JavaScript example
    const formData = new FormData();
    formData.append('frame', blob, 'frame.jpg');
    formData.append('timestamp', Date.now() / 1000);
    
    const response = await fetch('/api/v1/session/{id}/analyze', {
        method: 'POST',
        body: formData
    });
    ```
    
    **Returns:** Real-time analysis results
    """
    start_time = time.time()
    
    try:
        # Validate session
        manager = get_session_manager()
        session = manager.get_session(session_id)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session not found: {session_id}"
            )
        
        if session.status != "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Session is not active (status: {session.status})"
            )
        
        # Read frame data
        frame_bytes = await frame.read()
        
        # Check frame size
        frame_size_mb = len(frame_bytes) / (1024 * 1024)
        if frame_size_mb > MAX_FRAME_SIZE_MB:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Frame too large: {frame_size_mb:.2f}MB (max: {MAX_FRAME_SIZE_MB}MB)"
            )
        
        # Validate image format
        try:
            img = Image.open(io.BytesIO(frame_bytes))
            img.verify()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid image format: {str(e)}"
            )
        
        # Process frame
        analysis = process_frame_bytes(frame_bytes)
        
        # Use provided timestamp or current time
        frame_timestamp = timestamp if timestamp else time.time()
        
        # Add result to session
        manager.add_frame_result(
            session_id=session_id,
            focus_score=analysis.get("focus_score", 0),
            timestamp=frame_timestamp,
            events=analysis.get("alerts", [])
        )
        
        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000  # Convert to ms
        
        return FrameAnalysisResponse(
            session_id=session_id,
            timestamp=frame_timestamp,
            analysis=analysis,
            processing_time_ms=round(processing_time, 2)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Frame analysis failed: {str(e)}"
        )


@router.get("/{session_id}/stats")
async def get_session_stats(session_id: str):
    """
    Get real-time statistics for a session.
    
    **Returns:**
    - Current focus score
    - Number of frames processed
    - Alert counts
    - Session duration
    """
    try:
        manager = get_session_manager()
        session = manager.get_session(session_id)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session not found: {session_id}"
            )
        
        # Calculate stats
        avg_score = (
            sum(session.score_history) / len(session.score_history)
            if session.score_history else 0
        )
        
        duration = (
            (session.ended_at or session.last_activity) - session.created_at
        ).total_seconds()
        
        return {
            "session_id": session_id,
            "status": session.status,
            "frames_processed": session.frames_processed,
            "average_focus_score": round(avg_score, 1),
            "current_focus_score": session.score_history[-1] if session.score_history else 0,
            "duration_seconds": round(duration, 1),
            "alerts": {
                "device_detected": session.device_detections,
                "voice_detected": session.voice_detections,
                "person_detected": session.multiple_person_events
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stats: {str(e)}"
        )
