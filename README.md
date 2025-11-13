# 🎯 FocusGuard - AI Proctoring Assistant

> **Privacy-First AI-Powered Focus Monitoring for Remote Exams and Productivity Tracking**

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CUDA 12.2](https://img.shields.io/badge/CUDA-12.2-green.svg)](https://developer.nvidia.com/cuda-toolkit)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [System Requirements](#system-requirements)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Usage Guide](#usage-guide)
- [Architecture](#architecture)
- [Privacy & Security](#privacy--security)
- [Troubleshooting](#troubleshooting)
- [Demo Script](#demo-script)
- [Contributing](#contributing)
- [License](#license)

---

## 🌟 Overview

**FocusGuard** is an intelligent proctoring assistant that uses computer vision and AI to monitor focus levels in real-time. Unlike invasive cloud-based solutions, FocusGuard processes everything **locally on your device**, ensuring complete privacy.

### The Problem
- 73% of students admit to cheating in online exams
- Traditional proctoring software uploads video to cloud servers (privacy concerns)
- Current solutions lack real-time feedback and transparency

### Our Solution
✅ **100% Local Processing** - No cloud uploads, no privacy risks  
✅ **Real-Time AI Detection** - Instant feedback on focus state  
✅ **Multi-Modal Analysis** - Face tracking + device detection + audio monitoring  
✅ **Encrypted Logging** - All session data is securely encrypted  
✅ **GPU Accelerated** - Optimized for NVIDIA RTX GPUs  

---

## ✨ Features

### Core Detection Capabilities

| Feature | Technology | Description |
|---------|-----------|-------------|
| 👤 **Face Detection** | MediaPipe Face Mesh | Detects 468 facial landmarks in 3D |
| 👁️ **Gaze Tracking** | Iris Landmark Analysis | Monitors where user is looking |
| 📐 **Head Pose Estimation** | PnP Algorithm | Tracks head rotation angles |
| 📱 **Device Detection** | YOLOv8s | Identifies phones, books, laptops |
| 🎤 **Audio Monitoring** | Librosa VAD | Detects voice and anomalies |
| 📊 **Focus Scoring** | Custom Heuristics | Real-time 0-100 focus score |

### Dashboard Features
- 🎥 Live webcam feed with AI overlays
- 📈 Real-time focus score with color coding (Green/Yellow/Red)
- 📉 Interactive timeline graph (Plotly)
- 📋 Event log with timestamps and alerts
- 📥 Export PDF summary reports
- 🔒 Encrypted session logs

---

## 💻 System Requirements

### Minimum Requirements
- **OS:** Windows 10/11, Linux (Ubuntu 20.04+), macOS 11+
- **CPU:** Intel Core i5 or equivalent
- **RAM:** 8 GB
- **Storage:** 2 GB free space
- **Webcam:** Any USB or built-in camera (720p recommended)

### Recommended (Your System!)
- **OS:** Windows 11
- **CPU:** Intel Core i5 13th Gen
- **RAM:** 16 GB
- **GPU:** NVIDIA RTX 2050 (4GB VRAM) with CUDA 12.2
- **Storage:** SSD with 5 GB free space
- **Webcam:** 1080p webcam
- **Microphone:** Built-in or USB mic

---

## 🚀 Installation

### Step 1: Clone or Download Repository
```bash
cd "c:\all\aI verse\FocusGuard"
```

### Step 2: Install Python 3.13
If not already installed:
- Download from [python.org](https://www.python.org/downloads/)
- During installation, check "Add Python to PATH"

### Step 3: Install Dependencies
```powershell
# Install all required libraries (takes 3-5 minutes)
pip install -r requirements.txt
```

### Step 4: Install PyTorch with CUDA Support
```powershell
# For NVIDIA GPUs with CUDA 12.2 (your system)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

### Step 5: Verify Installation
```powershell
python setup_check.py
```

**Expected output:**
```
✓ PASS    Python Version
✓ PASS    Libraries
✓ PASS    Webcam
✓ PASS    GPU/CUDA
✓ PASS    Microphone
✓ PASS    YOLO Model

✓✓✓ All critical checks passed! You're ready to run FocusGuard! ✓✓✓
```

---

## ⚡ Quick Start

### Run the Application
```powershell
streamlit run app.py
```

The dashboard will open in your default browser at `http://localhost:8501`

### First-Time Setup
1. **Allow camera access** when prompted by browser
2. **Allow microphone access** (optional, for audio detection)
3. **Review privacy notice** and click "I Understand"
4. **Adjust settings** in sidebar if needed (camera index, scoring thresholds)
5. **Start monitoring!** Your focus score will appear in real-time

---

## ⚙️ Configuration

Edit `config.py` to customize behavior:

### Camera Settings
```python
CAMERA_INDEX = 0        # Change to 1 for external webcam
FRAME_WIDTH = 640       # Increase to 1280 for higher quality
TARGET_FPS = 30         # Lower to 15 if system lags
```

### Model Settings
```python
YOLO_MODEL_SIZE = 's'   # 'n' (fast), 's' (balanced), 'm' (accurate)
YOLO_DEVICE = 'cuda'    # 'cpu' if no GPU
```

### Scoring Rules
```python
PENALTY_PHONE_DETECTED = 30   # How much score drops when phone seen
HEAD_YAW_THRESHOLD = 30       # Degrees before "looking away" penalty
```

### Privacy Controls
```python
ENABLE_ENCRYPTION = True      # Encrypt all logs
SAVE_RAW_FRAMES = False       # Never save images (privacy)
AUTO_DELETE_LOGS_DAYS = 7     # Auto-clean old logs
```

---

## 📖 Usage Guide

### For Students (Exam Mode)
1. Launch FocusGuard before starting your exam
2. Position your face in the center of the frame
3. Keep your focus score **above 80** (green zone)
4. Avoid using phone or looking away for extended periods
5. After exam, export PDF summary as proof of focus

### For Educators (Monitoring Mode)
1. Share setup instructions with students
2. Request students to export PDF summary after exam
3. Review focus percentage and alert counts
4. Use timeline graph to identify suspicious patterns

### For Personal Productivity
1. Run FocusGuard during work/study sessions
2. Use focus score as feedback to stay on task
3. Review session summaries to track improvement
4. Identify distractions (phone usage, looking away)

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      STREAMLIT DASHBOARD (app.py)               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Live Video   │  │ Focus Score  │  │  Timeline    │          │
│  │    Feed      │  │   Gauge      │  │   Graph      │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │ Display Results
                              │
┌─────────────────────────────────────────────────────────────────┐
│                    PROCESSING PIPELINE                          │
│                                                                 │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐ │
│  │   Webcam     │ ───► │ MediaPipe    │ ───► │ Head Pose &  │ │
│  │   Capture    │      │ Face Mesh    │      │ Gaze Est.    │ │
│  └──────────────┘      └──────────────┘      └──────────────┘ │
│                                                      │          │
│  ┌──────────────┐      ┌──────────────┐             │          │
│  │   Audio      │ ───► │   Librosa    │             │          │
│  │   Capture    │      │   VAD/FFT    │             │          │
│  └──────────────┘      └──────────────┘             │          │
│                                                      ▼          │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐ │
│  │    Frame     │ ───► │   YOLOv8s    │ ───► │    Focus     │ │
│  │ (every 2nd)  │      │ Device Det.  │      │   Scorer     │ │
│  └──────────────┘      └──────────────┘      └──────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │ Log Events
                              │
┌─────────────────────────────────────────────────────────────────┐
│                   STORAGE & REPORTING                           │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐ │
│  │  Encrypted   │      │   Session    │      │  PDF Report  │ │
│  │    Logs      │      │   Summary    │      │  Generator   │ │
│  └──────────────┘      └──────────────┘      └──────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Key Modules

| Module | File | Purpose |
|--------|------|---------|
| Face Detection | `focus/face_detector.py` | MediaPipe wrapper for 468-point face mesh |
| Head Pose | `focus/head_pose_estimator.py` | Calculates pitch/yaw/roll angles |
| Gaze Tracking | `focus/gaze_estimator.py` | Determines where user is looking |
| Device Detection | `models/yolov8_wrapper.py` | YOLO-based object detection |
| Focus Scoring | `focus/scorer.py` | Combines all inputs into 0-100 score |
| Audio Analysis | `audio/anomaly_detector.py` | Voice activity and noise detection |
| Dashboard | `app.py` + `ui/` | Streamlit web interface |
| Logging | `utils/logger.py` | Encrypted event logging |

---

## 🔒 Privacy & Security

### Data Protection Principles

#### ✅ What We Collect
- Facial landmark coordinates (NOT raw images)
- Head pose angles (pitch, yaw, roll)
- Gaze direction (left/center/right)
- Device detection bounding boxes
- Audio energy levels (NOT recordings)
- Focus scores and event timestamps

#### ❌ What We DON'T Collect
- Raw webcam images (unless debug mode explicitly enabled)
- Biometric identifiers
- Audio recordings
- Any data uploaded to cloud

### Encryption
All logs are encrypted using **Fernet (AES-128)** symmetric encryption:
```python
# Logs stored as encrypted JSON
{
    "timestamp": "2025-10-24T10:23:45",
    "event": "device_detected",
    "data": {"class": "cell phone", "confidence": 0.92},
    "score": 58
}
```

### Data Retention
- **Default:** Logs kept for current session only
- **Auto-delete:** Logs older than 7 days removed automatically
- **User control:** Clear all logs anytime via settings

### Compliance
- **GDPR-compliant:** Data minimization, local processing
- **COPPA-safe:** No personal data collection
- **FERPA-compatible:** Educational records stay local

---

## 🐛 Troubleshooting

### Camera Not Working
```
✗ Camera not accessible!
```
**Solutions:**
1. Close other apps using camera (Zoom, Teams, etc.)
2. Try different camera index: Set `CAMERA_INDEX = 1` in config.py
3. Grant camera permissions to terminal/browser

### Low FPS / Laggy Performance
```
FPS: 10-15 (should be 25-30)
```
**Solutions:**
1. Lower resolution: `FRAME_WIDTH = 320`, `FRAME_HEIGHT = 240`
2. Reduce target FPS: `TARGET_FPS = 15`
3. Process fewer frames: `YOLO_PROCESS_EVERY_N_FRAMES = 3`
4. Use smaller YOLO model: `YOLO_MODEL_SIZE = 'n'`

### GPU Not Detected
```
⚠ No GPU detected - will use CPU
```
**Solutions:**
1. Install PyTorch with CUDA: 
   ```
   pip install torch --index-url https://download.pytorch.org/whl/cu121
   ```
2. Verify CUDA: Run `nvidia-smi` in terminal
3. If no GPU, set `YOLO_DEVICE = 'cpu'` in config.py (slower but works)

### Import Errors
```
ModuleNotFoundError: No module named 'cv2'
```
**Solution:**
```powershell
pip install -r requirements.txt --force-reinstall
```

### Streamlit Won't Start
```
streamlit: command not found
```
**Solution:**
```powershell
python -m streamlit run app.py
```

---

## 🎬 Demo Script

### 2-Minute Live Demo (For Hackathon Judges)

#### Pre-Demo Checklist (1 minute before)
- [ ] Run `streamlit run app.py`
- [ ] Verify camera working, good lighting
- [ ] Have phone/book ready nearby
- [ ] Browser at `localhost:8501`

#### Demo Sequence

**[0:00-0:15] Introduction**
> "FocusGuard is an AI-powered proctoring assistant that monitors focus in real-time using computer vision. Everything runs locally—no cloud uploads, complete privacy."

- Point to live video feed
- Show current focus score (100, green)

**[0:15-0:45] Focused State**
> "When I'm looking at the screen and focused, my score is 100 and green. The system tracks 468 facial landmarks and my gaze direction in real-time."

- Sit straight, look at screen
- Point to facial landmark dots and gaze arrow overlay

**[0:45-1:10] Distraction Detection**
> "Now watch what happens when I look away..."

- Turn head to the left for 3 seconds
- Score drops to ~75-80 (yellow)
- Return to center
- Show event log entry: "Looking away - Warning"

**[1:10-1:30] Device Detection**
> "If I bring out my phone during an exam..."

- Hold phone clearly in frame
- Score drops to ~50 (red alert)
- Point to bounding box and "cell phone 92%" label
- Show event log: "Unauthorized device detected - Alert"

**[1:30-1:50] Timeline & Summary**
> "The timeline graph shows my focus fluctuations over time. At the end of a session, I can export a PDF summary."

- Put phone down, return to focused
- Point to timeline showing score recovery
- Click "Export Summary PDF"
- Show: "Focused 68% of time, 1 device alert, 2 warnings"

**[1:50-2:00] Privacy & Impact**
> "All processing is 100% local on this laptop using my RTX 2050 GPU. Logs are encrypted. This ensures student privacy while maintaining exam integrity. Perfect for remote education, corporate certifications, and personal productivity tracking."

---

## 🤝 Contributing

We welcome contributions! Here's how:

1. **Fork the repository**
2. **Create a feature branch:** `git checkout -b feature/amazing-feature`
3. **Make your changes** with clear comments
4. **Test thoroughly:** Run `pytest tests/`
5. **Submit a pull request**

### Code Style
- Follow PEP 8 guidelines
- Add docstrings to all functions
- Comment complex logic clearly
- Keep functions under 50 lines when possible

---

## 📄 License

This project is licensed under the **MIT License** - see LICENSE file for details.

```
MIT License

Copyright (c) 2025 FocusGuard Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

[Full MIT License text...]
```

---

## 🙏 Acknowledgments

- **MediaPipe** team at Google for face mesh technology
- **Ultralytics** for YOLOv8 object detection
- **Streamlit** for making dashboards easy
- **The open-source community** for all the amazing libraries

---

## 📞 Contact & Support

- **Issues:** [GitHub Issues](https://github.com/focusguard/focusguard/issues)
- **Email:** support@focusguard.ai
- **Documentation:** [Full Docs](https://focusguard.ai/docs)

---

**Built with ❤️ for fair remote education and privacy-conscious proctoring**

*FocusGuard - Focus on what matters. We'll handle the rest.*
