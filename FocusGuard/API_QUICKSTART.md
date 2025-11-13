# FocusGuard API - Quick Start Guide

## 🚀 API Overview

**Base URL:** `http://127.0.0.1:8000`  
**Documentation:** `http://127.0.0.1:8000/api/docs`  
**Version:** 1.0.0

FocusGuard provides a REST API for institutional integration of AI-powered exam monitoring.

---

## 📋 Complete API Endpoints

### 1. Session Management

#### Create Session
```http
POST /api/v1/session/start
Content-Type: application/json

{
  "institution_id": "university_123",
  "exam_id": "midterm_2025",
  "student_id": "student_456",
  "metadata": {
    "exam_name": "Computer Science Midterm",
    "duration_minutes": 90
  }
}
```

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "active",
  "created_at": "2025-10-25T10:30:00",
  "expires_at": "2025-10-25T14:30:00"
}
```

#### Get Session Details
```http
GET /api/v1/session/{session_id}
```

#### End Session
```http
POST /api/v1/session/{session_id}/end
```

#### Delete Session
```http
DELETE /api/v1/session/{session_id}
```

---

### 2. Frame Analysis

#### Analyze Webcam Frame
```http
POST /api/v1/session/{session_id}/analyze
Content-Type: multipart/form-data

frame: [image file]
timestamp: 1234567890.123
```

**Response:**
```json
{
  "session_id": "550e8400...",
  "timestamp": 1234567890.123,
  "analysis": {
    "focus_score": 85,
    "status": "good",
    "face_detected": true,
    "face_count": 1,
    "device_detected": false,
    "device_type": null,
    "audio_anomaly": false,
    "gaze_direction": "forward",
    "alerts": []
  },
  "processing_time_ms": 45.2
}
```

#### Get Real-time Statistics
```http
GET /api/v1/session/{session_id}/stats
```

**Response:**
```json
{
  "session_id": "550e8400...",
  "status": "active",
  "frames_processed": 1250,
  "average_focus_score": 87.5,
  "current_focus_score": 89,
  "duration_seconds": 3600,
  "alerts": {
    "device_detected": 2,
    "voice_detected": 5,
    "person_detected": 1
  }
}
```

---

### 3. Report Generation

#### Request Report Generation
```http
POST /api/v1/session/{session_id}/generate
```

**Response:**
```json
{
  "task_id": "report-550e8400",
  "status": "processing",
  "estimated_seconds": 30
}
```

#### Check Report Status
```http
GET /api/v1/session/{session_id}/report/status
```

**Response:**
```json
{
  "task_id": "report-550e8400",
  "status": "completed",
  "progress": 100,
  "report_url": "/api/v1/session/{id}/report/download"
}
```

#### Download PDF Report
```http
GET /api/v1/session/{session_id}/report/download
```

Returns PDF file for download.

---

### 4. Health & Info

#### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "models_loaded": true,
  "active_sessions": 5,
  "timestamp": "2025-10-25T10:30:00"
}
```

#### API Information
```http
GET /
```

---

## 🔧 Integration Examples

### JavaScript (Browser)

```javascript
// 1. Create session
async function startMonitoring() {
  const response = await fetch('http://localhost:8000/api/v1/session/start', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      institution_id: 'university_123',
      exam_id: 'midterm_2025',
      student_id: 'student_456',
      metadata: {
        exam_name: 'Computer Science Midterm',
        duration_minutes: 90
      }
    })
  });
  
  const session = await response.json();
  return session.session_id;
}

// 2. Capture and analyze frame
async function analyzeFrame(sessionId, imageBlob) {
  const formData = new FormData();
  formData.append('frame', imageBlob, 'frame.jpg');
  formData.append('timestamp', Date.now() / 1000);
  
  const response = await fetch(
    `http://localhost:8000/api/v1/session/${sessionId}/analyze`,
    {
      method: 'POST',
      body: formData
    }
  );
  
  const result = await response.json();
  return result.analysis;
}

// 3. Get real-time stats
async function getStats(sessionId) {
  const response = await fetch(
    `http://localhost:8000/api/v1/session/${sessionId}/stats`
  );
  return await response.json();
}

// 4. End session and download report
async function endSession(sessionId) {
  await fetch(`http://localhost:8000/api/v1/session/${sessionId}/end`, {
    method: 'POST'
  });
  
  // Generate report
  await fetch(`http://localhost:8000/api/v1/session/${sessionId}/generate`, {
    method: 'POST'
  });
  
  // Download when ready
  window.location.href = 
    `http://localhost:8000/api/v1/session/${sessionId}/report/download`;
}
```

### Python

```python
import requests

# Create session
response = requests.post('http://localhost:8000/api/v1/session/start', json={
    'institution_id': 'university_123',
    'exam_id': 'midterm_2025',
    'student_id': 'student_456'
})
session_id = response.json()['session_id']

# Analyze frame
with open('frame.jpg', 'rb') as f:
    files = {'frame': f}
    data = {'timestamp': time.time()}
    response = requests.post(
        f'http://localhost:8000/api/v1/session/{session_id}/analyze',
        files=files,
        data=data
    )
    result = response.json()

# Get stats
stats = requests.get(
    f'http://localhost:8000/api/v1/session/{session_id}/stats'
).json()

# End session
requests.post(f'http://localhost:8000/api/v1/session/{session_id}/end')
```

### PowerShell

```powershell
# Create session
$body = @{
    institution_id = "university_123"
    exam_id = "midterm_2025"
    student_id = "student_456"
} | ConvertTo-Json

$session = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/session/start" `
    -Method Post -Body $body -ContentType "application/json"

$sessionId = $session.session_id

# Get stats
$stats = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/session/$sessionId/stats"

# End session
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/session/$sessionId/end" -Method Post
```

---

## 🔐 Security & Privacy

- **No Frame Storage:** Frames are processed and discarded (configurable)
- **7-Day Data Retention:** Sessions auto-deleted after 7 days
- **4-Hour Session Timeout:** Inactive sessions expire automatically
- **CORS Enabled:** Configure allowed origins in production
- **Encrypted Logs:** Session logs use Fernet encryption

---

## ⚙️ Configuration

Edit `api/config.py`:

```python
# Server
API_HOST = "0.0.0.0"
API_PORT = 8000

# Session
SESSION_TIMEOUT_HOURS = 4
MAX_CONCURRENT_SESSIONS = 100

# Privacy
ENABLE_FRAME_STORAGE = False
DATA_RETENTION_DAYS = 7

# Performance
FRAME_ANALYSIS_TIMEOUT_SEC = 5
MAX_FRAME_SIZE_MB = 1
```

---

## 🚦 Running the API

```bash
# Development (with auto-reload)
cd FocusGuard
.venv\Scripts\Activate.ps1
python -m uvicorn api.main:app --reload --host 127.0.0.1 --port 8000

# Production
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## 📊 Current Status

✅ **Stage 1 Complete: API Foundation**
- Configuration system
- Session management (CRUD)
- Frame analysis endpoints
- Report generation endpoints
- Health monitoring
- Interactive API docs

**Next:** JavaScript widget for easy integration
