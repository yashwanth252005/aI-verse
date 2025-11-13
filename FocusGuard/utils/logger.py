"""
Session Logger Module
=====================
Logs proctoring session events with optional encryption.

Uses Fernet symmetric encryption to protect sensitive session data.
All events, alerts, and detection results are logged with timestamps.

Author: FocusGuard Team
Date: October 24, 2025
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from cryptography.fernet import Fernet
import base64
import hashlib


class SessionLogger:
    """
    Logs proctoring session events with optional encryption.
    
    Creates timestamped log files with all session data including:
    - Face detection events
    - Device detections
    - Audio anomalies
    - Focus score timeline
    - Alerts and warnings
    
    Attributes:
        session_id: Unique session identifier
        log_file_path: Path to the log file
        encrypt: Whether to encrypt log data
        cipher: Fernet cipher for encryption
        
    Example:
        logger = SessionLogger(
            session_id="session_20251024_143020",
            encrypt=True
        )
        
        logger.log_event("session_start", {"user": "student_123"})
        logger.log_detection("device", {"type": "cell_phone", "confidence": 0.85})
        logger.save()
    """
    
    def __init__(
        self,
        session_id: str,
        log_dir: str = "logs",
        encrypt: bool = True,
        encryption_key: Optional[bytes] = None
    ):
        """
        Initialize session logger.
        
        Args:
            session_id: Unique identifier for this session
            log_dir: Directory to store log files
            encrypt: Whether to encrypt log data
            encryption_key: Optional encryption key (generates if None)
        """
        self.session_id = session_id
        self.log_dir = log_dir
        self.encrypt = encrypt
        
        # Create log directory if it doesn't exist
        os.makedirs(log_dir, exist_ok=True)
        
        # Set up log file path
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file_path = os.path.join(
            log_dir,
            f"session_{timestamp}_{session_id}.json"
        )
        
        # Set up encryption
        if encrypt:
            if encryption_key is None:
                # Generate encryption key from session_id
                key_material = hashlib.sha256(session_id.encode()).digest()
                self.encryption_key = base64.urlsafe_b64encode(key_material)
            else:
                self.encryption_key = encryption_key
            
            self.cipher = Fernet(self.encryption_key)
            print(f"✓ SessionLogger initialized with encryption")
        else:
            self.cipher = None
            print(f"✓ SessionLogger initialized without encryption")
        
        # Initialize log data structure
        self.log_data = {
            'session_id': session_id,
            'start_time': datetime.now().isoformat(),
            'end_time': None,
            'events': [],
            'detections': {
                'faces': [],
                'devices': [],
                'audio': []
            },
            'timeline': {
                'timestamps': [],
                'focus_scores': []
            },
            'statistics': {},
            'alerts': []
        }
        
        print(f"  → Log file: {self.log_file_path}")
    
    def log_event(self, event_type: str, data: Dict):
        """
        Log a general event.
        
        Args:
            event_type: Type of event (e.g., 'session_start', 'user_action')
            data: Event data dictionary
            
        Example:
            logger.log_event('session_start', {
                'user_id': '12345',
                'exam_id': 'final_2025'
            })
        """
        event = {
            'timestamp': datetime.now().isoformat(),
            'type': event_type,
            'data': data
        }
        self.log_data['events'].append(event)
    
    def log_detection(self, detection_type: str, data: Dict):
        """
        Log a detection event (face, device, or audio).
        
        Args:
            detection_type: Type of detection ('face', 'device', 'audio')
            data: Detection data dictionary
            
        Example:
            logger.log_detection('device', {
                'class': 'cell_phone',
                'confidence': 0.85,
                'bbox': [100, 200, 150, 250]
            })
        """
        detection = {
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        
        if detection_type in self.log_data['detections']:
            self.log_data['detections'][detection_type].append(detection)
    
    def log_timeline_point(self, focus_score: float, timestamp: Optional[str] = None):
        """
        Log a point in the focus score timeline.
        
        Args:
            focus_score: Focus score (0-100)
            timestamp: Optional timestamp (uses current time if None)
        """
        if timestamp is None:
            timestamp = datetime.now().isoformat()
        
        self.log_data['timeline']['timestamps'].append(timestamp)
        self.log_data['timeline']['focus_scores'].append(focus_score)
    
    def log_alert(self, alert_type: str, message: str, severity: str = 'WARNING'):
        """
        Log an alert or warning.
        
        Args:
            alert_type: Type of alert ('device', 'face', 'audio', etc.)
            message: Alert message
            severity: Severity level ('INFO', 'WARNING', 'CRITICAL')
        """
        alert = {
            'timestamp': datetime.now().isoformat(),
            'type': alert_type,
            'message': message,
            'severity': severity
        }
        self.log_data['alerts'].append(alert)
    
    def update_statistics(self, stats: Dict):
        """
        Update session statistics.
        
        Args:
            stats: Statistics dictionary
            
        Example:
            logger.update_statistics({
                'average_focus': 85.5,
                'total_alerts': 12,
                'device_detections': 3
            })
        """
        self.log_data['statistics'].update(stats)
    
    def finalize(self):
        """Mark session as complete with end time."""
        self.log_data['end_time'] = datetime.now().isoformat()
    
    def save(self, finalize: bool = True) -> str:
        """
        Save log data to file.
        
        Args:
            finalize: Whether to mark session as complete
            
        Returns:
            Path to saved log file
        """
        if finalize:
            self.finalize()
        
        # Convert to JSON
        json_data = json.dumps(self.log_data, indent=2)
        
        # Encrypt if enabled
        if self.encrypt:
            encrypted_data = self.cipher.encrypt(json_data.encode())
            
            # Save encrypted data
            with open(self.log_file_path, 'wb') as f:
                f.write(encrypted_data)
            
            print(f"✓ Session log saved (encrypted): {self.log_file_path}")
        else:
            # Save plain JSON
            with open(self.log_file_path, 'w') as f:
                f.write(json_data)
            
            print(f"✓ Session log saved: {self.log_file_path}")
        
        return self.log_file_path
    
    def load_log(self, log_file_path: str) -> Dict:
        """
        Load and decrypt a log file.
        
        Args:
            log_file_path: Path to log file
            
        Returns:
            Decrypted log data dictionary
        """
        with open(log_file_path, 'rb') as f:
            data = f.read()
        
        if self.encrypt:
            try:
                decrypted_data = self.cipher.decrypt(data)
                return json.loads(decrypted_data.decode())
            except Exception as e:
                raise ValueError(f"Failed to decrypt log file: {e}")
        else:
            return json.loads(data.decode())
    
    @staticmethod
    def generate_key() -> bytes:
        """
        Generate a new encryption key.
        
        Returns:
            Fernet-compatible encryption key
        """
        return Fernet.generate_key()
    
    def export_key(self, key_file_path: str):
        """
        Export encryption key to file.
        
        Args:
            key_file_path: Path to save key file
        """
        if not self.encrypt:
            print("⚠️  Encryption not enabled")
            return
        
        with open(key_file_path, 'wb') as f:
            f.write(self.encryption_key)
        
        print(f"✓ Encryption key exported: {key_file_path}")


# =============================================================================
# EXAMPLE USAGE
# =============================================================================
if __name__ == "__main__":
    print("=== SessionLogger Test ===\n")
    
    # Create logger
    logger = SessionLogger(
        session_id="test_session_001",
        encrypt=True
    )
    
    # Log session start
    logger.log_event('session_start', {
        'user_id': 'student_12345',
        'exam_name': 'Final Exam - AI Proctoring'
    })
    
    # Simulate some detections
    logger.log_detection('device', {
        'class': 'cell_phone',
        'confidence': 0.87
    })
    
    logger.log_detection('face', {
        'person_count': 1,
        'attention_score': 92
    })
    
    logger.log_detection('audio', {
        'voice_detected': True,
        'anomaly_score': 75
    })
    
    # Log timeline
    for i in range(5):
        logger.log_timeline_point(85 + i * 2)
    
    # Log alerts
    logger.log_alert('device', 'Cell phone detected', severity='CRITICAL')
    logger.log_alert('audio', 'Voice activity detected', severity='WARNING')
    
    # Update statistics
    logger.update_statistics({
        'average_focus_score': 87.5,
        'total_alerts': 2,
        'session_duration_seconds': 300
    })
    
    # Save log
    log_path = logger.save()
    
    print(f"\n✓ Test complete!")
    print(f"  Session ID: {logger.session_id}")
    print(f"  Events logged: {len(logger.log_data['events'])}")
    print(f"  Alerts: {len(logger.log_data['alerts'])}")
    print(f"  Timeline points: {len(logger.log_data['timeline']['timestamps'])}")
    
    # Test loading
    print(f"\n📖 Loading log file...")
    loaded_data = logger.load_log(log_path)
    print(f"  ✓ Successfully loaded {len(loaded_data['events'])} events")
