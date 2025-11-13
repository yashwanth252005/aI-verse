"""
API Models
==========
Pydantic models for request/response validation.

These models define the structure of API requests and responses,
ensuring type safety and automatic validation.

Author: FocusGuard Team
Date: October 25, 2025
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, List
from datetime import datetime


# Base configuration for all models
class BaseAPIModel(BaseModel):
    """Base model with common configuration."""
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()},
        use_enum_values=True
    )


# ============================================================================
# Session Models
# ============================================================================

class SessionCreateRequest(BaseAPIModel):
    """Request model for creating a new session."""
    institution_id: str = Field(..., description="Institution identifier")
    exam_id: str = Field(..., description="Exam identifier")
    student_id: str = Field(..., description="Student identifier")
    metadata: Optional[Dict] = Field(
        default=None,
        description="Optional metadata (exam_name, duration_minutes, etc.)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "institution_id": "school_123",
                "exam_id": "final_2025",
                "student_id": "student_456",
                "metadata": {
                    "exam_name": "Computer Science Final Exam",
                    "duration_minutes": 120
                }
            }
        }


class SessionResponse(BaseAPIModel):
    """Response model for session operations."""
    session_id: str
    status: str
    created_at: datetime
    expires_at: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "active",
                "created_at": "2025-10-25T10:30:00",
                "expires_at": "2025-10-25T14:30:00"
            }
        }


class SessionDetailResponse(BaseAPIModel):
    """Detailed session information."""
    session_id: str
    status: str
    institution_id: str
    exam_id: str
    student_id: str
    created_at: datetime
    last_activity: datetime
    ended_at: Optional[datetime] = None
    frames_processed: int
    metadata: Dict


# ============================================================================
# Analysis Models
# ============================================================================

class FrameAnalysisResponse(BaseAPIModel):
    """Response model for frame analysis."""
    session_id: str
    timestamp: float
    analysis: Dict = Field(
        ...,
        description="Analysis results including focus_score, status, detections, etc."
    )
    processing_time_ms: float
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "timestamp": 1234567890.123,
                "analysis": {
                    "focus_score": 85,
                    "status": "good",
                    "face_detected": True,
                    "face_count": 1,
                    "device_detected": False,
                    "device_type": None,
                    "audio_anomaly": False,
                    "gaze_direction": "forward",
                    "alerts": []
                },
                "processing_time_ms": 45.2
            }
        }


# ============================================================================
# Report Models
# ============================================================================

class ReportGenerateResponse(BaseAPIModel):
    """Response for report generation request."""
    task_id: str
    status: str
    estimated_seconds: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "report-550e8400",
                "status": "processing",
                "estimated_seconds": 30
            }
        }


class ReportStatusResponse(BaseAPIModel):
    """Response for report status check."""
    task_id: str
    status: str  # pending, processing, completed, failed
    progress: int  # 0-100
    report_url: Optional[str] = None
    error_message: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "report-550e8400",
                "status": "completed",
                "progress": 100,
                "report_url": "/api/v1/session/550e8400/report/download?token=..."
            }
        }


# ============================================================================
# Health & Info Models
# ============================================================================

class HealthResponse(BaseAPIModel):
    """API health check response."""
    status: str
    version: str
    models_loaded: bool
    active_sessions: int
    timestamp: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "models_loaded": True,
                "active_sessions": 5,
                "timestamp": "2025-10-25T10:30:00"
            }
        }


class InfoResponse(BaseAPIModel):
    """API information response."""
    name: str
    version: str
    description: str
    features: List[str]
    privacy_policy_url: str
    documentation_url: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "FocusGuard API",
                "version": "1.0.0",
                "description": "AI-powered focus monitoring for online exams",
                "features": [
                    "face_detection",
                    "device_detection",
                    "gaze_tracking",
                    "audio_analysis",
                    "pdf_reports"
                ],
                "privacy_policy_url": "/privacy",
                "documentation_url": "/docs"
            }
        }


# ============================================================================
# Error Models
# ============================================================================

class ErrorResponse(BaseAPIModel):
    """Standard error response."""
    error: str
    message: str
    status_code: int
    timestamp: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "SessionNotFound",
                "message": "Session with ID 550e8400 not found",
                "status_code": 404,
                "timestamp": "2025-10-25T10:30:00"
            }
        }
