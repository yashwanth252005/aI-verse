"""
YOLOv8 Device Detection Wrapper
================================
Wrapper class for YOLOv8 object detection focused on proctoring scenarios.

Detects relevant objects for exam proctoring:
- Mobile phones (cell phone)
- Books
- Laptops
- Other electronic devices

Author: FocusGuard Team
Date: October 24, 2025
"""

import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
from ultralytics import YOLO
import os


class YOLOv8Detector:
    """
    YOLOv8-based object detector for proctoring scenarios.
    
    This detector identifies objects that might indicate cheating or
    distraction during an exam/study session:
    - cell phone (class 67 in COCO)
    - book (class 73 in COCO)
    - laptop (class 63 in COCO)
    - keyboard (class 66 in COCO)
    - mouse (class 64 in COCO)
    
    Attributes:
        model: YOLOv8 model instance
        target_classes: List of COCO class IDs we care about
        confidence_threshold: Minimum confidence for detection
        device: 'cpu' or 'cuda' for inference
        
    Example:
        detector = YOLOv8Detector()
        detections = detector.detect(frame)
        for det in detections:
            print(f"Found {det['class_name']} with confidence {det['confidence']:.2f}")
    """
    
    # COCO dataset class mapping (relevant classes for proctoring)
    COCO_CLASSES = {
        63: 'laptop',
        64: 'mouse',
        65: 'remote',
        66: 'keyboard',
        67: 'cell phone',
        73: 'book',
        76: 'scissors',
        77: 'teddy bear',
        84: 'book',  # Alternative book class
    }
    
    # Classes that indicate potential cheating
    CHEATING_DEVICES = {
        67: 'cell phone',  # Primary concern - texting/browsing
        73: 'book',         # Secondary concern - notes/answers
        63: 'laptop',       # Browsing/accessing materials
        66: 'keyboard',     # External keyboard for another device
        64: 'mouse',        # Controlling another device
        65: 'remote',       # TV remote or device control
    }
    
    # Per-class confidence thresholds to reduce false positives
    CLASS_CONFIDENCE_THRESHOLDS = {
        67: 0.30,  # cell phone - medium threshold (often confused with mouse)
        73: 0.30,  # book - medium threshold
        63: 0.45,  # laptop - higher threshold (often confused with books)
        66: 0.35,  # keyboard - medium threshold
        64: 0.35,  # mouse - medium-high threshold (often confused with phone)
        65: 0.30,  # remote - medium threshold
    }
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        confidence_threshold: float = 0.5,
        device: str = 'cpu'
    ):
        """
        Initialize YOLOv8 detector.
        
        Args:
            model_path: Path to YOLOv8 model weights. If None, uses 'yolov8s.pt'
            confidence_threshold: Minimum confidence (0-1) for detection
            device: 'cpu' or 'cuda' for inference
            
        Raises:
            FileNotFoundError: If model file doesn't exist
            RuntimeError: If model fails to load
        """
        self.confidence_threshold = confidence_threshold
        self.device = device
        
        # Set default model path if not provided
        if model_path is None:
            # Look in models directory first
            current_dir = os.path.dirname(os.path.abspath(__file__))
            model_path = os.path.join(current_dir, 'yolov8s.pt')
            
            # If not there, check project root
            if not os.path.exists(model_path):
                project_root = os.path.dirname(current_dir)
                model_path = os.path.join(project_root, 'yolov8s.pt')
        
        # Auto-download if model doesn't exist
        if not os.path.exists(model_path):
            print(f"⏳ YOLOv8 model not found at: {model_path}")
            print(f"   Auto-downloading yolov8s.pt (this may take a minute)...")
            try:
                # YOLO() will auto-download the model
                temp_model = YOLO('yolov8s.pt')
                # Model is now downloaded to Ultralytics cache
                # Use the downloaded model path
                model_path = 'yolov8s.pt'  # Use model name, Ultralytics finds it
                print(f"✓ YOLOv8 model downloaded successfully!")
            except Exception as e:
                raise RuntimeError(f"Failed to download YOLOv8 model: {e}")
        
        try:
            # Load YOLOv8 model
            print(f"⏳ Loading YOLOv8 model from: {model_path}")
            self.model = YOLO(model_path)
            self.model.to(device)
            print(f"✓ YOLOv8 loaded successfully (device={device})")
            
        except Exception as e:
            raise RuntimeError(f"Failed to load YOLOv8 model: {e}")
        
        # Filter to only care about specific classes
        self.target_classes = list(self.COCO_CLASSES.keys())
        
        # Statistics
        self.detection_count = 0
        self.frame_count = 0
        
        print(f"✓ YOLOv8Detector initialized")
        print(f"  → Monitoring CHEATING devices: {list(self.CHEATING_DEVICES.values())}")
        print(f"  → Confidence: phone=30%, book=30%, laptop=45%, keyboard=35%, mouse=35%, remote=30%")
    
    def detect(
        self,
        frame: np.ndarray,
        filter_cheating_only: bool = True
    ) -> List[Dict]:
        """
        Detect objects in a frame.
        
        Args:
            frame: Input frame as BGR numpy array
            filter_cheating_only: If True, only return cheating-related devices
            
        Returns:
            List of detection dictionaries, each containing:
            - class_id: COCO class ID
            - class_name: Human-readable class name
            - confidence: Detection confidence (0-1)
            - bbox: Bounding box as (x1, y1, x2, y2)
            - center: Center point as (cx, cy)
            - is_cheating_device: Boolean flag
            
        Example:
            detections = detector.detect(frame)
            for det in detections:
                x1, y1, x2, y2 = det['bbox']
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
        """
        self.frame_count += 1
        
        # Run YOLOv8 inference with optimized image size for speed
        # imgsz=320 is much faster than 416, still accurate enough for device detection
        results = self.model.predict(
            frame,
            conf=self.confidence_threshold,
            verbose=False,
            device=self.device,
            imgsz=320  # Smaller image = maximum speed
        )
        
        detections = []
        
        # Process results
        if len(results) > 0:
            result = results[0]  # First image
            
            # Extract boxes, classes, and confidences
            boxes = result.boxes.xyxy.cpu().numpy()  # (x1, y1, x2, y2)
            confidences = result.boxes.conf.cpu().numpy()
            class_ids = result.boxes.cls.cpu().numpy().astype(int)
            
            # Filter and format detections
            for box, conf, cls_id in zip(boxes, confidences, class_ids):
                # Only include target classes
                if cls_id not in self.target_classes:
                    continue
                
                # Use per-class confidence thresholds (stricter for laptops)
                min_confidence = self.CLASS_CONFIDENCE_THRESHOLDS.get(cls_id, self.confidence_threshold)
                if conf < min_confidence:
                    continue
                
                x1, y1, x2, y2 = map(int, box)
                
                # Calculate dimensions and aspect ratio
                width = x2 - x1
                height = y2 - y1
                aspect_ratio = width / height if height > 0 else 0
                area = width * height
                
                # Additional filtering for laptop vs book confusion
                # Laptops are typically wider (aspect_ratio > 1.3)
                # Books held vertically are taller (aspect_ratio < 1.0)
                if cls_id == 63:  # laptop
                    # If detected as laptop but aspect ratio suggests book, skip it
                    if aspect_ratio < 1.2:  # Too tall to be a laptop
                        continue
                    # Also require higher confidence for laptops in portrait orientation
                    if aspect_ratio < 1.5 and conf < 0.55:
                        continue
                
                # Additional filtering for cell phone vs mouse confusion
                # Cell phones are typically taller (portrait) or rectangular
                # Mice are small and more rounded/wider
                if cls_id == 67:  # cell phone
                    # Cell phones in portrait: tall and thin (aspect < 0.8)
                    # Cell phones in landscape: medium rectangle (0.8 < aspect < 2.0)
                    # If it's very wide/flat or very small, might be a mouse - require higher confidence
                    if aspect_ratio > 1.8 or area < 5000:  # Too wide or too small for phone
                        if conf < 0.40:  # Require higher confidence
                            continue
                
                if cls_id == 64:  # mouse
                    # Computer mice are typically small and wide/rounded
                    # If detected as mouse but too tall/large, might be phone - require higher confidence
                    if aspect_ratio < 0.7 or area > 15000:  # Too tall or too large for mouse
                        if conf < 0.40:  # Require higher confidence
                            continue
                
                # Calculate center point
                cx = (x1 + x2) // 2
                cy = (y1 + y2) // 2
                
                # Get class name
                class_name = self.COCO_CLASSES.get(cls_id, f'class_{cls_id}')
                
                # Check if it's a cheating device
                is_cheating = cls_id in self.CHEATING_DEVICES
                
                detection = {
                    'class_id': cls_id,
                    'class_name': class_name,
                    'confidence': float(conf),
                    'bbox': (x1, y1, x2, y2),
                    'center': (cx, cy),
                    'is_cheating_device': is_cheating
                }
                
                # Apply filter if requested
                if filter_cheating_only:
                    if is_cheating:
                        detections.append(detection)
                        self.detection_count += 1
                else:
                    detections.append(detection)
                    self.detection_count += 1
        
        return detections
    
    def draw_detections(
        self,
        frame: np.ndarray,
        detections: List[Dict],
        show_confidence: bool = True
    ) -> np.ndarray:
        """
        Draw detection bounding boxes on frame.
        
        Args:
            frame: Input frame to draw on (modified in-place)
            detections: List of detections from detect()
            show_confidence: If True, show confidence scores
            
        Returns:
            Modified frame (same object as input)
            
        Example:
            detections = detector.detect(frame)
            detector.draw_detections(frame, detections)
            cv2.imshow('Detections', frame)
        """
        for det in detections:
            x1, y1, x2, y2 = det['bbox']
            class_name = det['class_name']
            confidence = det['confidence']
            is_cheating = det['is_cheating_device']
            
            # Color: RED for cheating devices, YELLOW for others
            color = (0, 0, 255) if is_cheating else (0, 255, 255)
            
            # Draw bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            
            # Prepare label
            if show_confidence:
                label = f"{class_name}: {confidence:.2f}"
            else:
                label = class_name
            
            # Draw label background
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
            cv2.rectangle(
                frame,
                (x1, y1 - label_size[1] - 10),
                (x1 + label_size[0], y1),
                color,
                -1
            )
            
            # Draw label text
            cv2.putText(
                frame,
                label,
                (x1, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                2
            )
        
        return frame
    
    def get_cheating_devices(self, detections: List[Dict]) -> List[Dict]:
        """
        Filter detections to only include cheating-related devices.
        
        Args:
            detections: List of all detections
            
        Returns:
            List of only cheating device detections
            
        Example:
            all_detections = detector.detect(frame, filter_cheating_only=False)
            cheating = detector.get_cheating_devices(all_detections)
            if cheating:
                print(f"⚠️ Found {len(cheating)} cheating device(s)!")
        """
        return [det for det in detections if det['is_cheating_device']]
    
    def get_stats(self) -> Dict:
        """
        Get detection statistics.
        
        Returns:
            Dictionary with statistics
            
        Example:
            stats = detector.get_stats()
            print(f"Detection rate: {stats['detection_rate']:.1%}")
        """
        detection_rate = self.detection_count / self.frame_count if self.frame_count > 0 else 0
        
        return {
            'total_frames': self.frame_count,
            'total_detections': self.detection_count,
            'detection_rate': detection_rate,
            'target_classes': list(self.COCO_CLASSES.values()),
            'confidence_threshold': self.confidence_threshold
        }


# =============================================================================
# TEST SCRIPT
# =============================================================================
if __name__ == "__main__":
    """
    Test the YOLOv8 detector with webcam.
    Press 'q' to quit.
    """
    print("=" * 70)
    print("YOLOv8 Device Detector - Test Script")
    print("=" * 70)
    
    try:
        # Initialize detector
        detector = YOLOv8Detector(confidence_threshold=0.4)
        
        # Open webcam
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("❌ Error: Could not open webcam")
            exit(1)
        
        print("\n✓ Webcam opened")
        print("📱 Try showing your phone, a book, or laptop to the camera")
        print("Press 'q' to quit\n")
        
        frame_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                print("❌ Failed to read frame")
                break
            
            frame_count += 1
            
            # Detect objects (process every 5th frame for speed)
            if frame_count % 5 == 0:
                detections = detector.detect(frame, filter_cheating_only=False)
                
                # Draw detections
                detector.draw_detections(frame, detections)
                
                # Check for cheating devices
                cheating_devices = detector.get_cheating_devices(detections)
                if cheating_devices:
                    print(f"⚠️  Frame {frame_count}: Found {len(cheating_devices)} cheating device(s)")
                    for det in cheating_devices:
                        print(f"   - {det['class_name']} ({det['confidence']:.2%} confidence)")
            
            # Add instruction text
            cv2.putText(
                frame,
                "YOLOv8 Device Detection Test - Press 'q' to quit",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )
            
            # Show frame
            cv2.imshow('YOLOv8 Device Detection', frame)
            
            # Check for quit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        # Cleanup
        cap.release()
        cv2.destroyAllWindows()
        
        # Show stats
        stats = detector.get_stats()
        print("\n" + "=" * 70)
        print("Detection Statistics:")
        print(f"  Total frames: {stats['total_frames']}")
        print(f"  Total detections: {stats['total_detections']}")
        print(f"  Detection rate: {stats['detection_rate']:.1%}")
        print("=" * 70)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
