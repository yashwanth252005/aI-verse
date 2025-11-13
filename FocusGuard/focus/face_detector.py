"""
Face Detection Module
=====================
Detects faces in video frames using OpenCV Haar Cascade classifier.

This module provides simple but effective face detection that works well
for proctoring scenarios where the user is typically facing the camera.

Author: FocusGuard Team
Date: October 24, 2025
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional
import os


class FaceDetector:
    """
    Face detector using OpenCV Haar Cascade.
    
    This detector is fast, lightweight, and works without requiring
    GPU or complex dependencies. It's perfect for real-time proctoring.
    
    Attributes:
        face_cascade: OpenCV CascadeClassifier for face detection
        scale_factor: Image pyramid scale factor (lower = more accurate but slower)
        min_neighbors: Minimum neighbors for detection (higher = fewer false positives)
        min_face_size: Minimum face size in pixels (width, height)
        
    Example:
        detector = FaceDetector()
        faces = detector.detect(frame)
        if faces:
            x, y, w, h = faces[0]
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
    """
    
    def __init__(
        self,
        cascade_path: Optional[str] = None,
        scale_factor: float = 1.1,
        min_neighbors: int = 5,
        min_face_size: Tuple[int, int] = (80, 80)
    ):
        """
        Initialize the face detector.
        
        Args:
            cascade_path: Path to Haar Cascade XML file. If None, uses default path.
            scale_factor: How much image size is reduced at each image scale (1.1 = 10% smaller).
                         Lower values (e.g., 1.05) are more accurate but slower.
            min_neighbors: How many neighbors each candidate rectangle should have to retain it.
                          Higher values result in fewer but more quality detections.
            min_face_size: Minimum face size (width, height) in pixels.
                          Faces smaller than this will be ignored.
        
        Raises:
            FileNotFoundError: If cascade file doesn't exist
            ValueError: If cascade file fails to load
        """
        # Set default path if not provided
        if cascade_path is None:
            # Get the project root directory (3 levels up from this file)
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
            cascade_path = os.path.join(project_root, 'models', 'haarcascade_frontalface_default.xml')
        
        # Check if file exists
        if not os.path.exists(cascade_path):
            raise FileNotFoundError(
                f"Haar Cascade file not found: {cascade_path}\n"
                f"Please run: cd models && wget https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/haarcascade_frontalface_default.xml"
            )
        
        # Load the cascade classifier
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        
        # Verify it loaded correctly
        if self.face_cascade.empty():
            raise ValueError(f"Failed to load Haar Cascade from: {cascade_path}")
        
        # Try to load profile face cascade as fallback for side views
        try:
            profile_path = cascade_path.replace('frontalface', 'profileface')
            if os.path.exists(profile_path):
                self.profile_cascade = cv2.CascadeClassifier(profile_path)
                if not self.profile_cascade.empty():
                    print(f"  → Profile face cascade loaded for side-view detection")
                else:
                    self.profile_cascade = None
            else:
                self.profile_cascade = None
        except:
            self.profile_cascade = None
        
        # Store detection parameters
        self.scale_factor = scale_factor
        self.min_neighbors = min_neighbors
        self.min_face_size = min_face_size
        
        # Statistics
        self.detection_count = 0
        self.no_detection_count = 0
        
        print(f"✓ FaceDetector initialized (Haar Cascade, min_size={min_face_size})")
    
    def detect(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detect faces in a frame.
        
        Args:
            frame: Input frame as BGR numpy array (from OpenCV)
        
        Returns:
            List of face bounding boxes as (x, y, width, height) tuples.
            Returns empty list if no faces detected.
            Faces are sorted by size (largest first).
        
        Example:
            faces = detector.detect(frame)
            print(f"Found {len(faces)} faces")
            if faces:
                x, y, w, h = faces[0]  # Get largest face
                face_roi = frame[y:y+h, x:x+w]
        """
        # Convert to grayscale (Haar Cascades work on grayscale images)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Apply histogram equalization to improve contrast
        # This helps detection work better in various lighting conditions
        gray = cv2.equalizeHist(gray)
        
        # Detect faces
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=self.scale_factor,
            minNeighbors=self.min_neighbors,
            minSize=self.min_face_size,
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        
        # DISABLED: Profile cascade causes false positives (neck, shoulders detected as faces)
        # Only use frontal face detection for better accuracy in proctoring scenarios
        # Profile detection can be re-enabled if needed, but frontal-only works best
        
        # Convert from numpy array to list of tuples
        face_list = [tuple(face) for face in faces]
        
        # CRITICAL: Filter out false positives (background patterns, edges, etc.)
        if len(face_list) > 1:
            frame_height, frame_width = gray.shape
            filtered_faces = []
            
            # Keep the largest face (main person)
            largest_face = face_list[0]
            largest_area = largest_face[2] * largest_face[3]
            filtered_faces.append(largest_face)
            
            # For additional faces, apply strict quality checks
            for face in face_list[1:]:
                x, y, w, h = face
                area = w * h
                
                # Check 1: Must be at least 40% of largest face size (not tiny background patterns)
                if area < largest_area * 0.4:
                    continue
                
                # Check 2: Aspect ratio must be face-like (0.75 to 1.25, roughly square)
                aspect_ratio = w / h if h > 0 else 0
                if aspect_ratio < 0.75 or aspect_ratio > 1.25:
                    continue
                
                # Check 3: Must be in center region (not far edges where background patterns are)
                center_x = x + w // 2
                center_y = y + h // 2
                # Skip if too close to left/right edges (outer 15% of frame)
                if center_x < frame_width * 0.15 or center_x > frame_width * 0.85:
                    continue
                
                # Check 4: Must not overlap too much with largest face (avoid duplicate detection)
                lx, ly, lw, lh = largest_face
                # Calculate intersection over union (IoU)
                x_overlap = max(0, min(x + w, lx + lw) - max(x, lx))
                y_overlap = max(0, min(y + h, ly + lh) - max(y, ly))
                intersection = x_overlap * y_overlap
                union = area + (lw * lh) - intersection
                iou = intersection / union if union > 0 else 0
                if iou > 0.3:  # More than 30% overlap = probably same face
                    continue
                
                # Passed all checks - this is a real additional face
                filtered_faces.append(face)
            
            face_list = filtered_faces
        
        # Sort by area (largest first) - most relevant face is usually largest
        face_list.sort(key=lambda f: f[2] * f[3], reverse=True)
        
        # Update statistics
        if len(face_list) > 0:
            self.detection_count += 1
        else:
            self.no_detection_count += 1
        
        return face_list
    
    def get_face_center(self, bbox: Tuple[int, int, int, int]) -> Tuple[int, int]:
        """
        Calculate the center point of a face bounding box.
        
        Args:
            bbox: Face bounding box as (x, y, width, height)
        
        Returns:
            Center point as (center_x, center_y)
        
        Example:
            x, y, w, h = faces[0]
            cx, cy = detector.get_face_center((x, y, w, h))
            cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)
        """
        x, y, w, h = bbox
        center_x = x + w // 2
        center_y = y + h // 2
        return (center_x, center_y)
    
    def draw_faces(
        self,
        frame: np.ndarray,
        faces: List[Tuple[int, int, int, int]],
        color: Tuple[int, int, int] = (0, 255, 0),
        thickness: int = 2,
        draw_center: bool = False  # Changed default to False for cleaner look
    ) -> np.ndarray:
        """
        Draw face bounding boxes on a frame (for visualization/debugging).
        
        Args:
            frame: Input frame to draw on (will be modified in-place)
            faces: List of face bounding boxes from detect()
            color: Box color as BGR tuple (default: green)
            thickness: Line thickness in pixels
            draw_center: If True, also draw center point of each face (default: False for clean UI)
        
        Returns:
            The modified frame (same object as input)
        
        Example:
            faces = detector.detect(frame)
            detector.draw_faces(frame, faces, color=(0, 255, 0))
            cv2.imshow('Faces', frame)
        """
        for face in faces:
            x, y, w, h = face
            
            # Draw clean rectangle around face only - no labels or center points by default
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, thickness)
            
            # Optional: Draw center point only if explicitly requested
            if draw_center:
                cx, cy = self.get_face_center(face)
                cv2.circle(frame, (cx, cy), 5, color, -1)
        
        return frame
    
    def get_stats(self) -> dict:
        """
        Get detection statistics.
        
        Returns:
            Dictionary with detection statistics:
            - total_frames: Total frames processed
            - detections: Frames with at least one face
            - no_detections: Frames with no faces
            - detection_rate: Percentage of frames with faces (0-100)
        
        Example:
            stats = detector.get_stats()
            print(f"Detection rate: {stats['detection_rate']:.1f}%")
        """
        total = self.detection_count + self.no_detection_count
        rate = (self.detection_count / total * 100) if total > 0 else 0.0
        
        return {
            'total_frames': total,
            'detections': self.detection_count,
            'no_detections': self.no_detection_count,
            'detection_rate': rate
        }


# =============================================================================
# Testing / Demo Code
# =============================================================================
if __name__ == "__main__":
    """
    Simple test script to verify face detection works.
    Run: python -m focus.face_detector
    """
    print("="*70)
    print("FaceDetector Test")
    print("="*70)
    print()
    
    # Initialize detector
    try:
        detector = FaceDetector()
        print("✓ Detector initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize detector: {e}")
        exit(1)
    
    # Try to open webcam
    print("\nOpening webcam...")
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("✗ Failed to open webcam")
        exit(1)
    
    print("✓ Webcam opened")
    print("\nPress 'q' to quit")
    print("="*70)
    
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("✗ Failed to read frame")
            break
        
        frame_count += 1
        
        # Detect faces
        faces = detector.detect(frame)
        
        # Draw faces
        detector.draw_faces(frame, faces)
        
        # Add info text
        info = f"Frame: {frame_count} | Faces: {len(faces)}"
        cv2.putText(frame, info, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Show frame
        cv2.imshow('Face Detection Test', frame)
        
        # Check for quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    
    # Print statistics
    print()
    print("="*70)
    stats = detector.get_stats()
    print(f"Processed {stats['total_frames']} frames")
    print(f"Detected faces in {stats['detections']} frames ({stats['detection_rate']:.1f}%)")
    print("="*70)
