"""
FocusGuard Configuration File
=============================
Central configuration for all modules.
Optimized for: RTX 2050, Intel i5 13th Gen, 16GB RAM, Windows 11

Author: FocusGuard Team
Date: October 24, 2025
"""

import os
from pathlib import Path

# =============================================================================
# PROJECT PATHS
# =============================================================================
# Base directory of the project (where this config.py file lives)
BASE_DIR = Path(__file__).parent.absolute()

# Directory paths for various components
LOG_DIR = BASE_DIR / 'logs'                    # Encrypted session logs
EXPORT_DIR = BASE_DIR / 'exports'              # PDF summary reports
MODEL_CACHE_DIR = BASE_DIR / 'models_cache'    # Downloaded ML model weights
SAMPLE_DATA_DIR = BASE_DIR / 'sample_data'     # Test images for validation

# Create directories if they don't exist
for directory in [LOG_DIR, EXPORT_DIR, MODEL_CACHE_DIR, SAMPLE_DATA_DIR]:
    directory.mkdir(exist_ok=True)

# =============================================================================
# CAMERA SETTINGS
# =============================================================================
CAMERA_INDEX = 0                # Default webcam (0 = built-in, 1 = external)
FRAME_WIDTH = 640               # Video resolution width in pixels
FRAME_HEIGHT = 480              # Video resolution height in pixels
TARGET_FPS = 30                 # Target frames per second (30 is smooth enough, reduces CPU load)

# =============================================================================
# MODEL SETTINGS
# =============================================================================
# YOLOv8 Configuration (Object Detection)
YOLO_MODEL_SIZE = 's'           # 's' = small model (better accuracy than 'n' nano, still fast on RTX 2050)
YOLO_DEVICE = 'cuda'            # Use GPU acceleration ('cuda' for NVIDIA, 'cpu' for fallback)
YOLO_CONFIDENCE_THRESHOLD = 0.55  # Minimum confidence to accept a detection (0-1)
YOLO_IOU_THRESHOLD = 0.45       # Non-max suppression threshold for overlapping boxes

# MediaPipe Face Mesh Configuration
MEDIAPIPE_MIN_DETECTION_CONFIDENCE = 0.5   # Min confidence to detect face initially
MEDIAPIPE_MIN_TRACKING_CONFIDENCE = 0.5    # Min confidence to track face across frames
MEDIAPIPE_MAX_NUM_FACES = 2                # Maximum faces to detect (alert if >1)

# Device classes to detect (from COCO dataset used by YOLO)
DEVICE_CLASSES = {
    67: 'cell phone',    # COCO class 67
    73: 'book',          # COCO class 73
    63: 'laptop',        # COCO class 63
    # Note: Tablets are often detected as cell phones or laptops
}

# =============================================================================
# FOCUS SCORING RULES
# =============================================================================
# Base score (perfect focus scenario)
BASE_SCORE = 100

# Penalty values for different infractions
PENALTY_NO_FACE = 40            # Person not visible in frame
PENALTY_HEAD_TURN_MAX = 25      # Maximum penalty for extreme head turn
PENALTY_HEAD_PITCH_MAX = 15     # Maximum penalty for looking up/down
PENALTY_GAZE_OFF_CENTER = 15    # Looking away from screen
PENALTY_PHONE_DETECTED = 30     # Mobile phone in frame
PENALTY_LAPTOP_DETECTED = 20    # Laptop detected (might be cheating)
PENALTY_BOOK_DETECTED = 10      # Book in frame (might be reference material)
PENALTY_MULTIPLE_FACES = 20     # More than one person detected

# Head pose thresholds (in degrees)
HEAD_YAW_THRESHOLD = 30         # Sideways turn beyond this triggers penalty
HEAD_PITCH_THRESHOLD = 20       # Up/down tilt beyond this triggers penalty

# Temporal smoothing for stable scores
SMOOTHING_ALPHA = 0.3           # Exponential moving average weight (lower = smoother but slower response)

# Score color coding for UI
SCORE_THRESHOLDS = {
    'focused': 80,      # Score >= 80: Green (Focused)
    'distracted': 60,   # Score >= 60: Yellow (Distracted)
    # Score < 60: Red (Away/Not Present)
}

# =============================================================================
# AUDIO DETECTION SETTINGS (Optional but enabled since microphone is present)
# =============================================================================
ENABLE_AUDIO = True             # Enable audio-based anomaly detection
AUDIO_SAMPLE_RATE = 16000       # Audio sampling rate in Hz
AUDIO_CHUNK_DURATION = 1.0      # Process audio in 1-second chunks
AUDIO_ENERGY_THRESHOLD = 0.02   # Minimum energy to detect voice activity
AUDIO_ANOMALY_THRESHOLD = 30    # dB change to trigger loud noise alert

# =============================================================================
# LOGGING AND PRIVACY
# =============================================================================
ENABLE_ENCRYPTION = True        # Encrypt all log files
AUTO_DELETE_LOGS_DAYS = 7       # Auto-delete logs older than this (0 = keep forever)
SAVE_RAW_FRAMES = False         # DON'T save raw images (privacy protection)
LOG_INTERVAL_SECONDS = 5        # Log events every N seconds

# Encryption key (IMPORTANT: Keep this secret! Change before deployment)
# In production, load this from environment variable or secure key vault
ENCRYPTION_KEY = b'FocusGuard2025SecureKey_ChangeMe_32B'  # Must be 32 bytes for Fernet

# =============================================================================
# UI SETTINGS
# =============================================================================
UI_UPDATE_INTERVAL_MS = 100     # Update dashboard every 100ms (10 Hz for smooth UI)
TIMELINE_HISTORY_POINTS = 1000  # Keep last 1000 score points in memory (~5 minutes at 30 fps)
EVENT_LOG_MAX_ENTRIES = 100     # Show last 100 events in the log table

# =============================================================================
# ALERT THRESHOLDS
# =============================================================================
# Trigger alerts when these conditions persist for N consecutive frames
ALERT_FRAMES_THRESHOLD = {
    'device_detected': 3,       # Phone/book visible for 3 frames = alert
    'looking_away': 30,         # Looking away for 30 frames (~1 second) = warning
    'multiple_faces': 5,        # Multiple people for 5 frames = alert
    'no_face': 15,              # No face for 15 frames (~0.5 second) = alert
}

# =============================================================================
# PERFORMANCE OPTIMIZATION
# =============================================================================
# Process every Nth frame for heavy operations (set to 1 to process all frames)
YOLO_PROCESS_EVERY_N_FRAMES = 2  # Run YOLO every 2nd frame (still gives 15 fps detection)
POSE_PROCESS_EVERY_N_FRAMES = 1  # Run pose estimation every frame (lightweight)

# =============================================================================
# DEBUG AND DEVELOPMENT
# =============================================================================
DEBUG_MODE = False              # Enable verbose logging and debug visualizations
SHOW_FPS_COUNTER = True         # Display FPS on video feed
SHOW_LANDMARK_DOTS = True       # Show facial landmark points on video

# =============================================================================
# DEMO AND PRESENTATION
# =============================================================================
DEMO_MODE = False               # When True, adds helpful overlays for presentation
DEMO_SHOW_CONFIDENCE = True     # Show detection confidence scores in demo
DEMO_RECORD_SESSION = False     # Auto-record session for demo video
