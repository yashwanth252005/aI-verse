"""
Head Pose Estimation Module
============================
Estimates head orientation from face detection results.

Since we're using Haar Cascade (which only gives face bounding box),
we estimate pose based on face position, size, and movement relative
to the frame center.

Author: FocusGuard Team
Date: October 24, 2025
"""

import cv2
import numpy as np
from typing import Tuple, Optional, Dict
import math


class HeadPoseEstimator:
    """
    Estimates head pose from face bounding box.
    
    Without facial landmarks, we use heuristics based on:
    - Face position relative to frame center (yaw/horizontal rotation)
    - Face vertical position (pitch/vertical tilt)
    - Face size changes (distance from camera)
    
    Attributes:
        frame_width: Expected frame width in pixels
        frame_height: Expected frame height in pixels
        center_x: Frame center X coordinate
        center_y: Frame center Y coordinate
        
    Example:
        estimator = HeadPoseEstimator(640, 480)
        pose = estimator.estimate_pose(face_bbox, frame_shape)
        if pose['looking_away']:
            print(f"User looking {pose['direction']}")
    """
    
    def __init__(self, frame_width: int = 640, frame_height: int = 480):
        """
        Initialize the head pose estimator.
        
        Args:
            frame_width: Expected frame width in pixels
            frame_height: Expected frame height in pixels
        """
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.center_x = frame_width // 2
        self.center_y = frame_height // 2
        
        # Thresholds for determining if user is looking away
        # More sensitive thresholds for earlier gaze detection
        self.horizontal_threshold = 0.15  # 15% from center = looking left/right (was 30%)
        self.vertical_threshold = 0.15    # 15% from center = looking up/down (was 25%)
        
        # Statistics
        self.estimate_count = 0
        
        print(f"✓ HeadPoseEstimator initialized (frame={frame_width}x{frame_height})")
        print(f"  → Sensitive thresholds: H={self.horizontal_threshold*100}%, V={self.vertical_threshold*100}%")
    
    def estimate_pose(
        self,
        face_bbox: Tuple[int, int, int, int],
        frame_shape: Optional[Tuple[int, int]] = None
    ) -> Dict:
        """
        Estimate head pose from face bounding box.
        
        Args:
            face_bbox: Face bounding box as (x, y, width, height)
            frame_shape: Optional frame shape as (height, width) for dynamic sizing
        
        Returns:
            Dictionary containing:
            - yaw: Horizontal rotation (-1.0 to 1.0, negative=left, positive=right)
            - pitch: Vertical tilt (-1.0 to 1.0, negative=down, positive=up)
            - roll: Side tilt (always 0 for Haar Cascade)
            - face_size: Normalized face size (0.0 to 1.0)
            - distance: Estimated distance category ('close', 'normal', 'far')
            - looking_away: Boolean indicating if user is not looking at camera
            - direction: String describing where user is looking
            - attention_score: 0-100 score (100=looking directly, 0=looking completely away)
        
        Example:
            faces = detector.detect(frame)
            if faces:
                pose = estimator.estimate_pose(faces[0])
                print(f"Attention: {pose['attention_score']}/100")
        """
        self.estimate_count += 1
        
        # Get face center and size
        x, y, w, h = face_bbox
        face_center_x = x + w // 2
        face_center_y = y + h // 2
        
        # Update frame dimensions if provided
        if frame_shape is not None:
            frame_h, frame_w = frame_shape
            self.frame_width = frame_w
            self.frame_height = frame_h
            self.center_x = frame_w // 2
            self.center_y = frame_h // 2
        
        # Calculate offset from center (normalized to -1.0 to 1.0)
        offset_x = (face_center_x - self.center_x) / (self.frame_width / 2)
        offset_y = (face_center_y - self.center_y) / (self.frame_height / 2)
        
        # Yaw (horizontal rotation): INVERTED for camera mirror effect
        # When user looks RIGHT, they appear on LEFT side of frame (negative offset_x)
        # So we invert: negative offset = looking right, positive offset = looking left
        yaw = -offset_x  # INVERTED: Now matches user's actual head direction
        
        # Pitch (vertical tilt): negative=down, positive=up
        pitch = -offset_y  # Invert because positive Y is down in images
        
        # Roll (side tilt): Not detectable with bounding box only
        roll = 0.0
        
        # Normalize face size (relative to frame)
        face_area = w * h
        frame_area = self.frame_width * self.frame_height
        face_size = face_area / frame_area
        
        # Estimate distance category based on face size
        if face_size > 0.15:  # Face takes up >15% of frame
            distance = 'close'
        elif face_size > 0.05:  # Face takes up 5-15% of frame
            distance = 'normal'
        else:  # Face takes up <5% of frame
            distance = 'far'
        
        # Determine if looking away based on offset thresholds
        # INVERTED LOGIC: Face on left = looking right, face on right = looking left
        looking_right = offset_x < -self.horizontal_threshold  # Face moved left = looking right
        looking_left = offset_x > self.horizontal_threshold    # Face moved right = looking left
        looking_up = pitch > self.vertical_threshold
        looking_down = pitch < -self.vertical_threshold
        
        looking_away = looking_left or looking_right or looking_up or looking_down
        
        # Determine direction string
        direction_parts = []
        if looking_up:
            direction_parts.append("up")
        elif looking_down:
            direction_parts.append("down")
        
        if looking_left:
            direction_parts.append("left")
        elif looking_right:
            direction_parts.append("right")
        
        if direction_parts:
            direction = " ".join(direction_parts)
        else:
            direction = "forward"  # Looking at camera
        
        # Calculate attention score (100 = directly at camera, 0 = far away)
        # Based on how far from center the face is
        offset_magnitude = math.sqrt(offset_x**2 + offset_y**2)
        
        # Clamp to 0-1 range (offset of 0.5 or more = 0 attention)
        attention_normalized = max(0.0, 1.0 - (offset_magnitude / 0.5))
        attention_score = int(attention_normalized * 100)
        
        # Adjust for face size (if too far away, reduce attention)
        if distance == 'far':
            attention_score = int(attention_score * 0.7)  # 30% penalty
        elif distance == 'close':
            attention_score = min(100, int(attention_score * 1.1))  # 10% bonus
        
        return {
            'yaw': yaw,
            'pitch': pitch,
            'roll': roll,
            'face_size': face_size,
            'distance': distance,
            'looking_away': looking_away,
            'direction': direction,
            'attention_score': attention_score,
            'face_center': (face_center_x, face_center_y),
            'frame_center': (self.center_x, self.center_y)
        }
    
    def draw_pose(
        self,
        frame: np.ndarray,
        pose: Dict,
        color: Tuple[int, int, int] = (255, 0, 255)
    ) -> np.ndarray:
        """
        Draw pose visualization on frame (for debugging).
        
        Args:
            frame: Input frame to draw on
            pose: Pose dictionary from estimate_pose()
            color: Drawing color as BGR tuple
        
        Returns:
            Modified frame
        
        Example:
            pose = estimator.estimate_pose(face_bbox)
            estimator.draw_pose(frame, pose)
        """
        face_cx, face_cy = pose['face_center']
        frame_cx, frame_cy = pose['frame_center']
        
        # Draw frame center (small white circle)
        cv2.circle(frame, (frame_cx, frame_cy), 5, (255, 255, 255), -1)
        
        # Draw line from frame center to face center
        cv2.line(frame, (frame_cx, frame_cy), (face_cx, face_cy), color, 2)
        
        # Draw face center (larger colored circle)
        cv2.circle(frame, (face_cx, face_cy), 8, color, -1)
        
        # Add text with pose information
        y_offset = 60
        texts = [
            f"Direction: {pose['direction']}",
            f"Attention: {pose['attention_score']}/100",
            f"Distance: {pose['distance']}"
        ]
        
        for text in texts:
            cv2.putText(
                frame,
                text,
                (10, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                color,
                2
            )
            y_offset += 25
        
        return frame
    
    def get_stats(self) -> dict:
        """
        Get estimation statistics.
        
        Returns:
            Dictionary with statistics
        """
        return {
            'total_estimates': self.estimate_count
        }


# =============================================================================
# Testing / Demo Code
# =============================================================================
if __name__ == "__main__":
    """
    Test the head pose estimator with face detector.
    Run: python -m focus.head_pose_estimator
    """
    import cv2
    from focus.face_detector import FaceDetector
    
    print("="*70)
    print("HeadPoseEstimator Test")
    print("="*70)
    print()
    
    # Initialize
    detector = FaceDetector()
    estimator = HeadPoseEstimator(640, 480)
    
    print("\nOpening webcam...")
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    if not cap.isOpened():
        print("✗ Failed to open webcam")
        exit(1)
    
    print("✓ Webcam opened")
    print("\nMove your head left/right/up/down to test pose estimation")
    print("Press 'q' to quit")
    print("="*70)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Detect faces
        faces = detector.detect(frame)
        
        if faces:
            # Get largest face
            face = faces[0]
            
            # Estimate pose
            pose = estimator.estimate_pose(face, frame.shape[:2])
            
            # Draw face box
            detector.draw_faces(frame, [face])
            
            # Draw pose visualization
            estimator.draw_pose(frame, pose)
            
            # Add warning if looking away
            if pose['looking_away']:
                cv2.putText(
                    frame,
                    f"LOOKING {pose['direction'].upper()}!",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 0, 255),
                    2
                )
        else:
            cv2.putText(
                frame,
                "NO FACE DETECTED",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 0, 255),
                2
            )
        
        cv2.imshow('Head Pose Estimation Test', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    
    print()
    print("="*70)
    print("Test complete!")
    print("="*70)
