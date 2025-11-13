"""
FocusGuard API
==============
Main FastAPI application for institutional integration.

This API allows institutions to integrate FocusGuard's AI proctoring
capabilities into their existing exam platforms.

Author: FocusGuard Team
Date: October 25, 2025
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
import logging

from api.config import (
    API_VERSION, API_TITLE, API_DESCRIPTION,
    CORS_ALLOW_ORIGINS, CORS_ALLOW_CREDENTIALS,
    CORS_ALLOW_METHODS, CORS_ALLOW_HEADERS
)
from api.models import HealthResponse, InfoResponse, ErrorResponse


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)


# ============================================================================
# CORS Middleware
# ============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW_ORIGINS,
    allow_credentials=CORS_ALLOW_CREDENTIALS,
    allow_methods=CORS_ALLOW_METHODS,
    allow_headers=CORS_ALLOW_HEADERS
)


# ============================================================================
# Exception Handlers
# ============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all uncaught exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    error_response = ErrorResponse(
        error="InternalServerError",
        message=str(exc),
        status_code=500,
        timestamp=datetime.now()
    )
    return JSONResponse(
        status_code=500,
        content=error_response.model_dump(mode='json')
    )


# ============================================================================
# Startup & Shutdown Events
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    logger.info("🚀 FocusGuard API starting...")
    logger.info(f"📋 Version: {API_VERSION}")
    logger.info(f"📚 API Docs: /api/docs")
    
    # TODO: Load AI models here
    # from core.processor_service import ProcessorService
    # processor = ProcessorService()
    # await processor.initialize()
    
    logger.info("✅ FocusGuard API ready!")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    logger.info("🛑 FocusGuard API shutting down...")
    
    # TODO: Cleanup
    # from api.session_manager import get_session_manager
    # manager = get_session_manager()
    # manager._cleanup_expired_sessions()
    
    logger.info("✅ Shutdown complete")


# ============================================================================
# Root Endpoints
# ============================================================================

@app.get("/", response_model=InfoResponse)
async def root():
    """API information endpoint."""
    return InfoResponse(
        name="FocusGuard API",
        version=API_VERSION,
        description="AI-powered focus monitoring for online exams",
        features=[
            "face_detection",
            "device_detection", 
            "gaze_tracking",
            "audio_analysis",
            "pdf_reports"
        ],
        privacy_policy_url="/privacy",
        documentation_url="/api/docs"
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    from api.session_manager import get_session_manager
    
    manager = get_session_manager()
    stats = manager.get_stats()
    
    return HealthResponse(
        status="healthy",
        version=API_VERSION,
        models_loaded=True,  # TODO: Check actual model status
        active_sessions=stats['active'],
        timestamp=datetime.now()
    )


# ============================================================================
# API Routes
# ============================================================================

from api.routes import session, analysis, reports

app.include_router(session.router, prefix="/api/v1/session", tags=["Session Management"])
app.include_router(analysis.router, prefix="/api/v1/session", tags=["Frame Analysis"])
app.include_router(reports.router, prefix="/api/v1/session", tags=["Report Generation"])


# ============================================================================
# Run Server (Development)
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    from api.config import API_HOST, API_PORT
    
    uvicorn.run(
        "api.main:app",
        host=API_HOST,
        port=API_PORT,
        reload=True,
        log_level="info"
    )
