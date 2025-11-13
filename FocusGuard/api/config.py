"""
API Configuration
=================
Configuration settings for FocusGuard REST API.

This module contains all configuration values for the institutional
integration API, including defaults for privacy, security, and performance.

Author: FocusGuard Team
Date: October 25, 2025
"""

import os
from typing import Optional

# ============================================================================
# API Server Configuration
# ============================================================================

# Server settings
API_HOST = os.getenv("API_HOST", "0.0.0.0")  # Bind to all interfaces
API_PORT = int(os.getenv("API_PORT", 8000))   # Standard FastAPI port
API_DEBUG = os.getenv("API_DEBUG", "True").lower() == "true"

# API versioning
API_VERSION = "1.0.0"
API_PREFIX = "/api/v1"
API_TITLE = "FocusGuard API"
API_DESCRIPTION = "AI-powered focus monitoring for online exams"

# CORS (Cross-Origin Resource Sharing)
# Allow institutions to call API from their domains
CORS_ALLOW_ORIGINS = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:8000",
    "http://localhost:8501",  # Streamlit
    "*"  # Allow all for demo (restrict in production!)
]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ["*"]
CORS_ALLOW_HEADERS = ["*"]

# ============================================================================
# Session Management
# ============================================================================

# Session timeouts
SESSION_TIMEOUT_HOURS = 4  # Auto-expire after 4 hours of inactivity
MAX_CONCURRENT_SESSIONS = 100  # Maximum sessions per API instance

# Frame analysis
FRAME_ANALYSIS_TIMEOUT_SEC = 5  # Kill analysis if takes longer
MAX_FRAME_SIZE_MB = 1  # Reject frames larger than 1MB

# ============================================================================
# Privacy & Security
# ============================================================================

# Data retention
DATA_RETENTION_DAYS = 7  # Auto-delete reports/logs after 7 days
ENABLE_FRAME_STORAGE = False  # Don't save frames by default (privacy!)
ANONYMIZE_STUDENT_IDS = True  # Hash student IDs in logs

# Security
REQUIRE_HTTPS = False  # Set True for production
MAX_UPLOAD_SIZE_MB = 10  # Maximum request body size

# ============================================================================
# AI Models Configuration
# ============================================================================

# Model paths
MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
YOLO_MODEL_PATH = os.path.join(MODEL_DIR, "yolov8s.pt")
HAAR_CASCADE_PATH = os.path.join(MODEL_DIR, "haarcascade_frontalface_default.xml")

# Model settings
CAMERA_INDEX = 0  # Default webcam
CONFIDENCE_THRESHOLD = 0.45  # YOLOv8 detection confidence
FACE_MIN_SIZE = (80, 80)  # Minimum face size in pixels

# Performance
TARGET_FPS = 30  # Target frames per second for processing
FRAME_SKIP = 1  # Process every Nth frame (1 = process all)

# ============================================================================
# Report Generation
# ============================================================================

# PDF reports
REPORT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports")
CHART_DPI = 100  # Resolution for embedded charts
MAX_REPORT_SIZE_MB = 5  # Maximum PDF size

# ============================================================================
# Logging
# ============================================================================

# Encrypted logs
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
ENABLE_AUDIT_LOG = True  # Log all API access
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR

# ============================================================================
# Helper Functions
# ============================================================================

def get_config_summary() -> dict:
    """Get summary of current configuration."""
    return {
        "api_version": API_VERSION,
        "api_host": API_HOST,
        "api_port": API_PORT,
        "session_timeout_hours": SESSION_TIMEOUT_HOURS,
        "max_concurrent_sessions": MAX_CONCURRENT_SESSIONS,
        "data_retention_days": DATA_RETENTION_DAYS,
        "privacy_mode": not ENABLE_FRAME_STORAGE,
        "models": {
            "yolo": os.path.basename(YOLO_MODEL_PATH),
            "haar": os.path.basename(HAAR_CASCADE_PATH)
        }
    }


# Print configuration on import (helpful for debugging)
if __name__ == "__main__":
    import json
    print("FocusGuard API Configuration:")
    print(json.dumps(get_config_summary(), indent=2))
