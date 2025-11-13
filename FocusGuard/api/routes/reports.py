"""
Report Generation Routes
========================
API endpoints for generating and downloading PDF reports.

Author: FocusGuard Team
Date: October 25, 2025
"""

from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from fastapi.responses import FileResponse
from datetime import datetime
import os

from api.models import ReportGenerateResponse, ReportStatusResponse
from api.session_manager import get_session_manager
from api.config import REPORT_DIR
from utils.report_generator import ReportGenerator

router = APIRouter()


# ============================================================================
# Report Generation (Background Task)
# ============================================================================

async def generate_pdf_report(session_id: str):
    """
    Background task to generate PDF report.
    
    TODO: This needs to use the actual ReportGenerator.
    For now, this is a placeholder.
    
    Args:
        session_id: Session identifier
    """
    try:
        manager = get_session_manager()
        session = manager.get_session(session_id)
        
        if not session:
            print(f"❌ Cannot generate report: Session {session_id} not found")
            return
        
        print(f"📊 Generating PDF report for session {session_id[:8]}...")
        
        # Use actual ReportGenerator to create PDF
        generator = ReportGenerator(
            session_id=session_id,
            output_dir=REPORT_DIR
        )
        report_filename = f"report_{session_id}.pdf"
        report_path = os.path.join(REPORT_DIR, report_filename)
        
        # Ensure reports directory exists
        os.makedirs(REPORT_DIR, exist_ok=True)
        
        # Generate the actual PDF report
        generator.generate_report(
            session_data=session,
            output_path=report_path
        )
        
        # Update session with report path
        session.report_path = report_path
        
        print(f"✅ Report generated: {report_path}")
        
    except Exception as e:
        print(f"❌ Report generation failed: {e}")
        import traceback
        traceback.print_exc()


# ============================================================================
# Report Endpoints
# ============================================================================

@router.post("/{session_id}/generate", response_model=ReportGenerateResponse)
async def request_report_generation(
    session_id: str,
    background_tasks: BackgroundTasks
):
    """
    Request PDF report generation (async).
    
    This endpoint triggers background report generation and returns immediately.
    Use the returned task_id to check generation status.
    
    **Workflow:**
    1. POST /session/{id}/generate → Get task_id
    2. GET /session/{id}/report/status → Check if ready
    3. GET /session/{id}/report/download → Download PDF
    
    **Returns:** Task ID for status checking
    """
    try:
        manager = get_session_manager()
        session = manager.get_session(session_id)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session not found: {session_id}"
            )
        
        if session.status == "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot generate report for active session. End session first."
            )
        
        # Check if report already exists
        if session.report_path and os.path.exists(session.report_path):
            return ReportGenerateResponse(
                task_id=f"report-{session_id}",
                status="completed",
                estimated_seconds=0
            )
        
        # Start background generation
        background_tasks.add_task(generate_pdf_report, session_id)
        
        return ReportGenerateResponse(
            task_id=f"report-{session_id}",
            status="processing",
            estimated_seconds=30
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start report generation: {str(e)}"
        )


@router.get("/{session_id}/report/status", response_model=ReportStatusResponse)
async def check_report_status(session_id: str):
    """
    Check PDF report generation status.
    
    **Returns:**
    - pending: Not started
    - processing: Currently generating
    - completed: Ready to download
    - failed: Generation error
    """
    try:
        manager = get_session_manager()
        session = manager.get_session(session_id)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session not found: {session_id}"
            )
        
        # Check if report exists
        if session.report_path and os.path.exists(session.report_path):
            return ReportStatusResponse(
                task_id=f"report-{session_id}",
                status="completed",
                progress=100,
                report_url=f"/api/v1/session/{session_id}/report/download"
            )
        else:
            return ReportStatusResponse(
                task_id=f"report-{session_id}",
                status="pending",
                progress=0,
                report_url=None
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check report status: {str(e)}"
        )


@router.get("/{session_id}/report/download")
async def download_report(session_id: str):
    """
    Download PDF report.
    
    **Returns:** PDF file for download
    """
    try:
        manager = get_session_manager()
        session = manager.get_session(session_id)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session not found: {session_id}"
            )
        
        # Check if report exists
        if not session.report_path or not os.path.exists(session.report_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not generated yet. Use /generate endpoint first."
            )
        
        # Generate filename
        filename = f"FocusGuard_Report_{session.student_id}_{session.exam_id}.pdf"
        
        return FileResponse(
            path=session.report_path,
            media_type="application/pdf",
            filename=filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download report: {str(e)}"
        )
