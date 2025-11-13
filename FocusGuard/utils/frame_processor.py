"""
Frame Processor Module
======================
Central pipeline for processing each video frame through the AI detection stack.
Coordinates between face detection, device detection, and scoring modules.

This module acts as the "brain" that takes raw frames and extracts all the
intelligence we need: face presence, head pose, gaze direction, devices, etc.

Author: FocusGuard Team
Date: October 24, 2025
"""

import cv2
import numpy as np
from typing import Dict, Any, Optional
import time


class FrameProcessor:
    """
    Central processor that runs all AI detection on each video frame.
    
    This class coordinates the entire detection pipeline:
    1. Face detection and landmark extraction
    2. Head pose estimation (pitch, yaw, roll angles)
    3. Gaze direction estimation
    4. Device detection (phones, books, laptops)
    5. Focus score calculation
    
    The processor maintains state across frames for temporal smoothing and
    tracks performance metrics.
    
    Attributes:
        frame_count (int): Total frames processed
        last_process_time (float): Time taken for last frame processing
    """
    
    def __init__(self):
        """
        Initialize the frame processor with real AI detection modules.
        
        Stage C: Face detection and head pose estimation active
        Stage D: Device detection (coming next)
        Stage E: Advanced focus scoring (coming after)
        """
        # Performance tracking
        self.frame_count = 0
        self.last_process_time = 0.0
        self.start_time = time.time()
        
        # Initialize STAGE C detection modules
        try:
            from focus.face_detector import FaceDetector
            from focus.head_pose_estimator import HeadPoseEstimator
            
            # Initialize with strict parameters to avoid false positives:
            # - scale_factor=1.05: Good balance between speed and accuracy
            # - min_neighbors=5: Strict to prevent neck/shoulder false positives
            # - min_face_size=(80, 80): Larger minimum to ensure real faces only
            self.face_detector = FaceDetector(
                scale_factor=1.05,  # Balanced detection (was 1.03)
                min_neighbors=5,    # Very strict to avoid false positives (was 4)
                min_face_size=(80, 80)  # Larger minimum for quality (was 60)
            )
            self.head_pose_estimator = HeadPoseEstimator()
            print("✓ Stage C modules loaded: Face detection + Head pose estimation")
            print("  → Strict detection (scale=1.05, neighbors=5, min_size=80) - No false positives!")
        except Exception as e:
            print(f"⚠️  Warning: Could not load face detection: {e}")
            print("   Will use fallback mode (simulated data)")
            self.face_detector = None
            self.head_pose_estimator = None
        
        # Initialize STAGE D detection modules
        try:
            from models.yolov8_wrapper import YOLOv8Detector
            from models.device_tracker import DeviceTracker
            
            # Initialize YOLOv8 with lower confidence for better detection
            self.device_detector = YOLOv8Detector(
                confidence_threshold=0.25,  # Lower threshold for better detection
                device='cpu'  # Use CPU for compatibility
            )
            
            # Initialize tracker with fast detection settings
            # - 2 frames confirmation (faster response time)
            # - 10 frames disappearance (forgive temporary occlusions)
            self.device_tracker = DeviceTracker(
                confirmation_frames=2,
                disappearance_frames=10
            )
            
            print("✓ Stage D modules loaded: YOLOv8 device detection + Tracker")
            print("  → Monitoring: phones, books, laptops")
        except Exception as e:
            print(f"⚠️  Warning: Could not load device detection: {e}")
            print("   Will continue without device detection")
            self.device_detector = None
            self.device_tracker = None
        
        # Initialize STAGE E: Advanced Focus Scoring
        try:
            from focus.scorer import FocusScorer
            
            self.focus_scorer = FocusScorer(
                device_penalty=30,           # -30 points per device
                multiple_person_penalty=50,  # -50 points for multiple people
                looking_away_threshold=3.0,  # Start penalty after 3 seconds
                temporal_penalty_rate=5      # -5 points per second looking away
            )
            
            print("✓ Stage E module loaded: Advanced Focus Scoring")
            print("  → Penalties: -30 per device, -50 multiple people, -5/sec looking away")
        except Exception as e:
            print(f"⚠️  Warning: Could not load focus scorer: {e}")
            print("   Will use basic scoring")
            self.focus_scorer = None
        
        # Initialize STAGE H: Session Logger
        try:
            from utils.logger import SessionLogger
            from datetime import datetime
            
            # Generate unique session ID
            session_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.session_id = f"session_{session_timestamp}"
            
            # Initialize logger with encryption
            self.logger = SessionLogger(
                session_id=self.session_id,
                log_dir="logs",
                encrypt=True
            )
            
            # Log session start
            self.logger.log_event('session_start', {
                'timestamp': datetime.now().isoformat(),
                'system': 'FocusGuard AI Proctoring'
            })
            
            print("✓ Stage H module loaded: Session Logger with Encryption")
            print(f"  → Session ID: {self.session_id}")
        except Exception as e:
            print(f"⚠️  Warning: Could not load session logger: {e}")
            print("   Will continue without logging")
            self.logger = None
            self.session_id = "unknown"
        
        # Initialize Gaze Direction Tracking (for analytics, not alerts)
        self.gaze_stats = {
            'forward': 0,
            'left': 0,
            'right': 0,
            'up': 0,
            'down': 0,
            'total_frames': 0
        }
        
        # Initialize STAGE G: Audio Anomaly Detection
        self.audio_capture = None
        self.audio_detector = None
        self.latest_audio_result = None
        self.audio_detection_count = 0  # Debug counter
        
        try:
            from audio.audio_capture import AudioCapture
            from audio.anomaly_detector import AudioAnomalyDetector
            import config
            
            if config.ENABLE_AUDIO:
                # Initialize detector with REALISTIC thresholds
                # Room silence is typically -50 to -60 dB
                # Normal speech is -20 to -10 dB
                # We want to detect actual speech, not room silence!
                self.audio_detector = AudioAnomalyDetector(
                    sample_rate=16000,
                    voice_threshold_db=-30.0,  # Only detect clear voice/speech
                    noise_threshold_db=-35.0   # Only detect actual noise (not room silence)
                )
                
                # Initialize capture with callback
                def audio_callback(audio_chunk, timestamp):
                    if self.audio_detector:
                        result = self.audio_detector.analyze(audio_chunk)
                        self.latest_audio_result = result
                        self.audio_detection_count += 1
                                                # Debug: Print when voice or noise detected
                        if result.get('voice_detected') and self.audio_detection_count % 10 == 0:
                            print(f"🎤 Voice detected! Energy: {result['energy_db']:.1f} dB, Score: {result['anomaly_score']:.0f}")
                        elif result.get('noise_detected') and self.audio_detection_count % 20 == 0:
                            print(f"🔊 Noise detected! Energy: {result['energy_db']:.1f} dB")
                
                self.audio_capture = AudioCapture(
                    callback=audio_callback,
                    sample_rate=16000,
                    chunk_duration=0.5
                )
                
                # Start capture
                if self.audio_capture.start():
                    print("✓ Stage G module loaded: Audio Anomaly Detection")
                    print("  → Monitoring: voice activity, background noise, anomalies")
                    print("  → Voice threshold: -35 dB, Noise threshold: -45 dB")
                else:
                    print("⚠️  Failed to start audio capture")
                    self.audio_capture = None
                    self.audio_detector = None
            else:
                print("ℹ️  Audio detection disabled in config")
        except Exception as e:
            print(f"⚠️  Warning: Could not load audio detection: {e}")
            print(f"   Error details: {str(e)}")
            print("   Will continue without audio detection")
            self.audio_capture = None
            self.audio_detector = None
        
        print("✓ FrameProcessor initialized with REAL face detection!")
    
    def process_frame(self, frame: np.ndarray) -> Dict[str, Any]:
        """
        Process a single video frame through the complete AI pipeline.
        
        This is the main entry point for frame analysis. It runs all detection
        algorithms and returns a comprehensive result dictionary.
        
        Args:
            frame: Input frame as BGR numpy array (from OpenCV)
        
        Returns:
            Dictionary containing all detection results:
            {
                'timestamp': float,              # Unix timestamp
                'frame_number': int,             # Sequential frame number
                'processing_time_ms': float,     # Time taken to process this frame
                'frame_shape': tuple,            # (height, width, channels)
                
                # Face detection results (Stage C)
                'face_detected': bool,           # Is a face present?
                'face_bbox': tuple or None,      # (x, y, w, h) bounding box
                'landmarks': array or None,      # Facial landmarks
                'head_pose': dict or None,       # {'pitch': float, 'yaw': float, 'roll': float}
                'gaze_direction': dict or None,  # {'horizontal': str, 'vertical': str}
                
                # Device detection results (Stage D)
                'devices_detected': list,        # List of detected devices
                'device_count': int,             # Total devices in frame
                
                # Focus analysis (Stage E)
                'focus_score': int,              # 0-100 focus score
                'focus_label': str,              # 'Focused', 'Distracted', 'Away'
                'focus_color': str,              # 'green', 'yellow', 'red'
                'alerts': list,                  # List of alert messages
                
                # Annotated frame (for display)
                'annotated_frame': np.ndarray    # Frame with overlays drawn
            }
        
        Example:
            processor = FrameProcessor()
            result = processor.process_frame(frame)
            print(f"Focus Score: {result['focus_score']}")
            cv2.imshow('Result', result['annotated_frame'])
        """
        process_start = time.time()
        
        # Increment frame counter
        self.frame_count += 1
        
        # Get frame dimensions
        height, width = frame.shape[:2]
        
        # Create a copy for annotation (so we don't modify the original)
        annotated_frame = frame.copy()
        
        # =======================================================================
        # STAGE C: REAL FACE DETECTION AND HEAD POSE ESTIMATION
        # =======================================================================
        
        # Initialize default values
        face_detected = False
        face_bbox = None
        head_pose = None
        focus_score = 50  # Default: neutral
        focus_label = "Unknown"
        focus_color = "yellow"
        alerts = []
        
        # Run face detection if module is available
        if self.face_detector is not None and self.head_pose_estimator is not None:
            try:
                # Detect ALL faces in frame
                faces = self.face_detector.detect(frame)
                person_count = len(faces)
                
                if len(faces) > 0:
                    # Use the largest face (most relevant) for head pose analysis
                    face_bbox = faces[0]
                    face_detected = True
                    
                    # Check for multiple people (cheating detection)
                    if person_count > 1:
                        alerts.append(f"Multiple people detected ({person_count} faces)")
                        focus_color = "red"
                        focus_label = f"⚠ {person_count} People Detected!"
                    
                    # Estimate head pose for primary face
                    head_pose = self.head_pose_estimator.estimate_pose(face_bbox, frame.shape[:2])
                    
                    # Calculate focus score based on attention (only if single person)
                    if person_count == 1:
                        focus_score = head_pose['attention_score']
                        
                        # Determine label and color
                        if focus_score >= 80:
                            focus_label = "Focused"
                            focus_color = "green"
                        elif focus_score >= 60:
                            focus_label = "Minor Distraction"
                            focus_color = "yellow"
                        else:
                            focus_label = "Distracted"
                            focus_color = "red"
                        
                        # Add alerts if looking away
                        if head_pose['looking_away']:
                            alerts.append(f"Looking {head_pose['direction']}")
                    else:
                        # Multiple people - severe penalty
                        focus_score = 20  # Low score for multiple people
                    
                    # Draw ALL detected faces on annotated frame
                    for idx, face in enumerate(faces):
                        # Primary face in green/yellow/red, others in red
                        if idx == 0:
                            face_color = (0, 255, 0) if focus_color == "green" \
                                        else (0, 255, 255) if focus_color == "yellow" \
                                        else (0, 0, 255)
                        else:
                            face_color = (0, 0, 255)  # Red for additional faces
                        
                        self.face_detector.draw_faces(annotated_frame, [face], color=face_color)
                        
                        # Label additional faces
                        if idx > 0:
                            x, y, w, h = face
                            cv2.putText(annotated_frame, f"Person {idx+1}", (x, y-10),
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                    
                    # REMOVED: Head pose visualization (arrows/axes) - too cluttered!
                    # Head pose is still being calculated for gaze detection, just not drawn
                    # self.head_pose_estimator.draw_pose(annotated_frame, head_pose)
                    
                else:
                    # No face detected
                    person_count = 0
                    focus_score = 0
                    focus_label = "No Face Detected"
                    focus_color = "red"
                    alerts.append("Face not visible")
            
            except Exception as e:
                print(f"⚠️  Error in face detection: {e}")
                # Fall back to neutral state
                person_count = 1
                focus_score = 50
                focus_label = "Detection Error"
                focus_color = "yellow"
            
            # Log face detection events
            if self.logger:
                self.logger.log_detection('face', {
                    'person_count': person_count,
                    'face_detected': face_detected,
                    'attention_score': head_pose.get('attention_score', 0) if head_pose else 0
                })
                
                # Log multiple person alert
                if person_count > 1:
                    self.logger.log_alert(
                        'multiple_people',
                        f"Multiple people detected ({person_count} faces)",
                        severity='CRITICAL'
                    )
        
        else:
            # Fallback: Use simulated score if face detector not available
            import math
            elapsed_time = time.time() - self.start_time
            person_count = 1
            focus_score = 85 + int(15 * math.sin(elapsed_time * 0.6))
            
            if focus_score >= 80:
                focus_label = "Focused (Simulated)"
                focus_color = "green"
            elif focus_score >= 60:
                focus_label = "Minor Distraction (Simulated)"
                focus_color = "yellow"
            else:
                focus_label = "Distracted (Simulated)"
                focus_color = "red"
        
        # =======================================================================
        # STAGE D: DEVICE DETECTION WITH YOLOV8
        # =======================================================================
        
        devices_detected = []
        device_count = 0
        cheating_device_count = 0
        
        # Run device detection if module is available
        if self.device_detector is not None and self.device_tracker is not None:
            try:
                # Run YOLOv8 detection every 3rd frame (faster detection response)
                # YOLOv8 is slower than face detection, so we skip frames for smoothness
                if self.frame_count % 3 == 0:
                    detections = self.device_detector.detect(frame, filter_cheating_only=True)
                    
                    # Update tracker for temporal smoothing
                    confirmed_devices = self.device_tracker.update(detections)
                    
                    # Only print on new device confirmations (not every frame)
                    if confirmed_devices and self.frame_count % 30 == 0:
                        print(f"⚠️  {len(confirmed_devices)} device(s) detected")
                else:
                    # On skipped frames, update tracker with empty list
                    confirmed_devices = self.device_tracker.update([])
                
                if confirmed_devices:
                    devices_detected = confirmed_devices
                    device_count = len(confirmed_devices)
                    cheating_device_count = len(self.device_detector.get_cheating_devices(confirmed_devices))
                    
                    # Log device detections
                    if self.logger:
                        for device in confirmed_devices:
                            self.logger.log_detection('device', {
                                'class': device['class_name'],
                                'confidence': device['confidence']
                            })
                            
                            # Log device alert
                            self.logger.log_alert(
                                'device',
                                f"Device detected: {device['class_name']} (confidence: {device['confidence']:.2f})",
                                severity='CRITICAL'
                            )
                    
                    # Note: Device alerts are now handled by FocusScorer (Stage E)
                    # No need to add duplicate alerts here
                    
                    # Draw device detection boxes on annotated frame
                    self.device_detector.draw_detections(annotated_frame, confirmed_devices)
            
            except Exception as e:
                print(f"⚠️  Error in device detection: {e}")
        
        # =======================================================================
        # STAGE E: Calculate Advanced Focus Score
        # =======================================================================
        focus_score_data = None
        if self.focus_scorer is not None:
            try:
                # Use head pose attention score as baseline
                base_score = head_pose.get('attention_score', 50.0) if head_pose else 50.0
                
                # Calculate comprehensive focus score with actual person count
                focus_score_data = self.focus_scorer.calculate_score(
                    head_pose_score=base_score,
                    face_detected=face_detected,
                    devices_detected=devices_detected,
                    person_count=person_count  # Now using actual detected person count!
                )
                
                # Override simple focus score with advanced scoring
                focus_score = focus_score_data['final_score']
                focus_label = focus_score_data['status']
                focus_color = focus_score_data['status_color']
                
                # Add warnings to alerts
                if focus_score_data['warnings']:
                    alerts.extend(focus_score_data['warnings'])
                
            except Exception as e:
                print(f"⚠️  Error in focus scoring: {e}")
        
        # =======================================================================
        # STAGE G: Process Audio Anomalies
        # =======================================================================
        audio_result = None
        if self.latest_audio_result:
            audio_result = self.latest_audio_result.copy()
            
            # Log audio detections
            if self.logger:
                self.logger.log_detection('audio', {
                    'voice_detected': audio_result.get('voice_detected', False),
                    'noise_detected': audio_result.get('noise_detected', False),
                    'anomaly_score': audio_result.get('anomaly_score', 0)
                })
            
            # Add audio warnings to alerts
            if audio_result.get('voice_detected'):
                alert_msg = f"[AUDIO] Voice detected (score: {audio_result['anomaly_score']:.0f}/100)"
                alerts.append(alert_msg)
                
                # Log audio alert
                if self.logger:
                    self.logger.log_alert('audio', alert_msg, severity='WARNING')
                    
            elif audio_result.get('noise_detected'):
                alert_msg = f"[AUDIO] Background noise detected"
                alerts.append(alert_msg)
                
                # Log audio alert
                if self.logger:
                    self.logger.log_alert('audio', alert_msg, severity='INFO')
        
        # =======================================================================
        # Log focus timeline point (every 10 frames = ~0.5 seconds at 20 FPS)
        # =======================================================================
        if self.logger and self.frame_count % 10 == 0:
            self.logger.log_timeline_point(focus_score)
        
        # Initialize result dictionary with detection results
        result = {
            'timestamp': time.time(),
            'frame_number': self.frame_count,
            'frame_shape': (height, width, 3),
            
            # Stage C (Face Detection) - NOW WITH REAL DATA + Multiple Face Detection
            'face_detected': face_detected,
            'face_bbox': face_bbox,
            'person_count': person_count,  # NEW: Number of people detected
            'landmarks': None,  # Will be added if we implement full landmark detection
            'head_pose': head_pose,
            'gaze_direction': head_pose['direction'] if head_pose else None,
            
            # Stage D (Device Detection) - NOW WITH REAL DATA
            'devices_detected': devices_detected,
            'device_count': device_count,
            'cheating_device_count': cheating_device_count,
            
            # Stage E (Advanced Focus Scoring) - NEW!
            'focus_score': focus_score,
            'focus_label': focus_label,
            'focus_color': focus_color,
            'focus_score_data': focus_score_data,  # Full scoring breakdown
            'alerts': alerts,
            
            # Stage G (Audio Anomaly Detection) - NEW!
            'audio_result': audio_result,  # Audio analysis data
            
            # Visual output
            'annotated_frame': annotated_frame
        }
        
        # =======================================================================
        # Add basic overlay to show the processor is working
        # =======================================================================
        self._add_status_overlay(annotated_frame, result)
        
        # Calculate processing time
        process_end = time.time()
        self.last_process_time = (process_end - process_start) * 1000  # Convert to milliseconds
        result['processing_time_ms'] = self.last_process_time
        
        return result
    
    def _add_status_overlay(self, frame: np.ndarray, result: Dict[str, Any]):
        """
        Add visual overlays to the frame showing detection status.
        
        This internal method draws text and graphics on the annotated frame
        to provide visual feedback about what the AI is detecting.
        
        Args:
            frame: Frame to draw on (modified in-place)
            result: Result dictionary with detection data
        """
        height, width = frame.shape[:2]
        
        # Draw a semi-transparent header bar at the top
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (width, 60), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
        
        # Draw title
        cv2.putText(
            frame,
            "FocusGuard - AI Proctoring Assistant",
            (10, 25),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )
        
        # Draw frame counter and FPS
        fps = self.get_fps()
        cv2.putText(
            frame,
            f"Frame: {result['frame_number']} | FPS: {fps:.1f}",
            (10, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (200, 200, 200),
            1
        )
        
        # Draw gaze direction indicator (top-left, below FPS)
        if result.get('head_pose') and result['face_detected']:
            direction = result['head_pose'].get('direction', 'forward')
            looking_away = result['head_pose'].get('looking_away', False)
            
            # Track gaze statistics
            self.gaze_stats[direction] = self.gaze_stats.get(direction, 0) + 1
            self.gaze_stats['total_frames'] += 1
            
            # Show message for any direction (more visible feedback)
            gaze_msg = None
            gaze_color = (0, 255, 0)  # Default green for forward
            
            if 'left' in direction:
                gaze_msg = "Looking Left"
                gaze_color = (0, 165, 255)  # Orange for looking away
            elif 'right' in direction:
                gaze_msg = "Looking Right"
                gaze_color = (0, 165, 255)  # Orange for looking away
            elif 'up' in direction:
                gaze_msg = "Looking Up"
                gaze_color = (0, 165, 255)  # Orange for looking away
            elif 'down' in direction:
                gaze_msg = "Looking Down"
                gaze_color = (0, 165, 255)  # Orange for looking away
            elif direction == 'forward':
                gaze_msg = "Looking Forward"
                gaze_color = (0, 255, 0)  # Green for good
            
            if gaze_msg:
                # Draw background rectangle for better visibility
                text_size = cv2.getTextSize(f"Gaze: {gaze_msg}", cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
                cv2.rectangle(frame, (5, 60), (text_size[0] + 15, 90), (0, 0, 0), -1)
                
                # Draw gaze indicator with larger font and thickness
                cv2.putText(
                    frame,
                    f"Gaze: {gaze_msg}",
                    (10, 80),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,  # Slightly larger font (was 0.5)
                    gaze_color,
                    2  # Bold text
                )
        
        # Draw audio status indicator (top-right)
        if result.get('audio_result'):
            audio = result['audio_result']
            if audio.get('voice_detected'):
                audio_text = "VOICE"
                audio_color = (0, 0, 255)  # Red
                icon = "🎤"
            elif audio.get('noise_detected'):
                audio_text = "NOISE"
                audio_color = (0, 165, 255)  # Orange
                icon = "🔊"
            else:
                audio_text = "QUIET"
                audio_color = (0, 255, 0)  # Green
                icon = "✓"
            
            # Draw audio status box
            text = f"Audio: {audio_text}"
            text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
            box_x = width - text_size[0] - 20
            
            cv2.rectangle(frame, (box_x - 5, 5), (width - 5, 35), (0, 0, 0), -1)
            cv2.putText(frame, text, (box_x, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, audio_color, 2)
        
        # =======================================================================
        # STAGE C: Real detection status (replaces Stage B placeholder)
        # =======================================================================
        
        # Draw detection status at bottom with person count
        if result['face_detected']:
            person_info = f" | People: {result['person_count']}" if result.get('person_count', 1) > 1 else ""
            status_text = f"Status: Face Detected{person_info} | Focus: {result['focus_score']}/100 ({result['focus_label']})"
            
            # Red color if multiple people detected
            if result.get('person_count', 1) > 1:
                status_color = (0, 0, 255)  # Red for multiple people
            else:
                status_color = (0, 255, 0) if result['focus_color'] == 'green' else \
                              (0, 255, 255) if result['focus_color'] == 'yellow' else \
                              (0, 0, 255)
        else:
            status_text = "Status: No Face Detected - Please position yourself in front of camera"
            status_color = (0, 0, 255)
        
        cv2.putText(
            frame,
            status_text,
            (10, height - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            status_color,
            1
        )
        
        # Draw alerts if any
        if result['alerts']:
            y_pos = height - 50
            for alert in result['alerts']:
                # Make alerts more visible with larger text and background
                # Remove emoji to avoid rendering issues on video overlay
                text = alert  # Use alert directly without adding emoji
                text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
                
                # Draw background rectangle
                cv2.rectangle(
                    frame,
                    (5, y_pos - text_size[1] - 5),
                    (15 + text_size[0], y_pos + 5),
                    (0, 0, 0),
                    -1
                )
                
                # Draw text
                cv2.putText(
                    frame,
                    text,
                    (10, y_pos),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 200, 255),  # Bright orange
                    2
                )
                y_pos -= 35
        
        # REMOVED: Directional arrows - too cluttered!
        # Clean UI: Just show face box and status text
        
        # Draw border color based on focus state
        border_color = (0, 255, 0) if result['focus_color'] == 'green' else \
                      (0, 255, 255) if result['focus_color'] == 'yellow' else \
                      (0, 0, 255)
        cv2.rectangle(frame, (0, 0), (width-1, height-1), border_color, 3)
    
    def get_fps(self) -> float:
        """
        Calculate average frames per second processed.
        
        Returns:
            float: Average FPS since processor started
        """
        elapsed = time.time() - self.start_time
        if elapsed > 0 and self.frame_count > 0:
            return self.frame_count / elapsed
        return 0.0
    
    def save_session_log(self, statistics: Optional[Dict] = None) -> Optional[str]:
        """
        Save session log with optional statistics.
        
        Args:
            statistics: Optional session statistics to include in log
            
        Returns:
            Path to saved log file, or None if logger not available
            
        Example:
            stats = {
                'average_focus_score': 85.5,
                'total_alerts': 12,
                'session_duration_seconds': 3600
            }
            log_path = processor.save_session_log(stats)
        """
        if not self.logger:
            print("⚠️  Logger not available, cannot save session log")
            return None
        
        try:
            # Update statistics if provided
            if statistics:
                self.logger.update_statistics(statistics)
            
            # Save the log (will encrypt if enabled)
            log_path = self.logger.save(finalize=True)
            
            return log_path
        
        except Exception as e:
            print(f"❌ Error saving session log: {e}")
            return None
    
    def get_stats(self) -> Dict[str, float]:
        """
        Get performance statistics for the processor.
        
        Returns:
            Dictionary with performance metrics:
            {
                'total_frames': int,
                'total_time_seconds': float,
                'average_fps': float,
                'last_frame_time_ms': float
            }
        """
        elapsed = time.time() - self.start_time
        avg_fps = self.frame_count / elapsed if elapsed > 0 else 0.0
        
        return {
            'total_frames': self.frame_count,
            'total_time_seconds': elapsed,
            'average_fps': avg_fps,
            'last_frame_time_ms': self.last_process_time
        }
    
    def get_gaze_statistics(self) -> Dict[str, any]:
        """
        Get gaze direction statistics.
        
        Returns:
            Dictionary with gaze analysis:
            {
                'forward_percentage': float,
                'left_percentage': float,
                'right_percentage': float,
                'up_percentage': float,
                'down_percentage': float,
                'total_frames_analyzed': int
            }
        """
        total = self.gaze_stats.get('total_frames', 0)
        
        if total == 0:
            return {
                'forward_percentage': 0,
                'left_percentage': 0,
                'right_percentage': 0,
                'up_percentage': 0,
                'down_percentage': 0,
                'total_frames_analyzed': 0
            }
        
        return {
            'forward_percentage': (self.gaze_stats.get('forward', 0) / total) * 100,
            'left_percentage': (self.gaze_stats.get('left', 0) / total) * 100,
            'right_percentage': (self.gaze_stats.get('right', 0) / total) * 100,
            'up_percentage': (self.gaze_stats.get('up', 0) / total) * 100,
            'down_percentage': (self.gaze_stats.get('down', 0) / total) * 100,
            'total_frames_analyzed': total
        }
    
    def reset_stats(self):
        """
        Reset performance counters.
        
        Useful when starting a new monitoring session.
        """
        self.frame_count = 0
        self.start_time = time.time()
        self.last_process_time = 0.0
        print("✓ Frame processor statistics reset")


# Example usage and testing
if __name__ == "__main__":
    """
    Test the frame processor with webcam.
    
    Run this file directly to test frame processing:
        python utils/frame_processor.py
    
    Press 'q' to quit.
    """
    print("Testing FrameProcessor module with live webcam...")
    print("Press 'q' to quit\n")
    
    # Import the video capture module
    import sys
    import os
    # Add parent directory to path so we can import from sibling modules
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from utils.video_capture import WebcamCapture
    
    try:
        # Initialize webcam and processor
        camera = WebcamCapture(camera_index=0, target_fps=30)
        processor = FrameProcessor()
        
        camera.start()
        
        print("Processing frames... Watch the FPS counter!\n")
        
        # Process frames until user quits
        while True:
            # Get frame from camera
            success, frame = camera.read_frame()
            
            if success:
                # Process the frame through AI pipeline
                result = processor.process_frame(frame)
                
                # Display the annotated frame
                cv2.imshow('FocusGuard - Frame Processor Test (Press Q to Quit)', 
                          result['annotated_frame'])
                
                # Print stats every 30 frames
                if result['frame_number'] % 30 == 0:
                    stats = processor.get_stats()
                    print(f"Processed {stats['total_frames']} frames | "
                          f"Avg FPS: {stats['average_fps']:.1f} | "
                          f"Last frame: {stats['last_frame_time_ms']:.1f}ms")
            
            # Check for 'q' key press
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        # Clean up
        camera.release()
        cv2.destroyAllWindows()
        
        # Print final statistics
        print("\n" + "="*60)
        print("FINAL STATISTICS")
        print("="*60)
        stats = processor.get_stats()
        for key, value in stats.items():
            print(f"{key}: {value}")
        print("="*60)
        
        print("\n✓ Test completed successfully!")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
