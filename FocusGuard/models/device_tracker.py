"""
Device Tracker Module
=====================
Tracks detected devices over time with temporal smoothing.

Prevents false alarms by requiring consistent detection across multiple frames
before confirming a device is present. Uses a sliding window approach.

Author: FocusGuard Team
Date: October 24, 2025
"""

import time
from typing import List, Dict, Optional, Tuple
from collections import deque
import numpy as np


class DeviceTracker:
    """
    Tracks devices across multiple frames with temporal smoothing.
    
    This prevents false positives by requiring a device to be detected
    consistently across multiple frames before reporting it as "present".
    
    Attributes:
        confirmation_frames: Number of frames needed to confirm detection
        disappearance_frames: Number of frames before device is considered gone
        iou_threshold: Minimum IoU to consider same device across frames
        
    Example:
        tracker = DeviceTracker(confirmation_frames=5)
        
        for frame in video:
            detections = detector.detect(frame)
            confirmed = tracker.update(detections)
            if confirmed:
                print(f"⚠️ Confirmed: {len(confirmed)} device(s) present")
    """
    
    def __init__(
        self,
        confirmation_frames: int = 5,
        disappearance_frames: int = 10,
        iou_threshold: float = 0.3
    ):
        """
        Initialize device tracker.
        
        Args:
            confirmation_frames: How many consecutive frames must detect a device
                                before it's confirmed (reduces false positives)
            disappearance_frames: How many frames without detection before device
                                 is considered gone (reduces false negatives)
            iou_threshold: Minimum IoU (Intersection over Union) to match same
                          device across frames (0-1, typically 0.3-0.5)
        """
        self.confirmation_frames = confirmation_frames
        self.disappearance_frames = disappearance_frames
        self.iou_threshold = iou_threshold
        
        # Tracking state
        self.tracked_devices = {}  # device_id -> device info
        self.next_device_id = 0
        self.frame_count = 0
        
        # History for temporal smoothing
        self.detection_history = deque(maxlen=max(confirmation_frames, disappearance_frames))
        
        print(f"✓ DeviceTracker initialized")
        print(f"  → Confirmation: {confirmation_frames} frames")
        print(f"  → Disappearance: {disappearance_frames} frames")
    
    def update(self, detections: List[Dict]) -> List[Dict]:
        """
        Update tracker with new detections and return confirmed devices.
        
        Args:
            detections: List of detections from YOLOv8Detector.detect()
            
        Returns:
            List of confirmed devices with tracking information:
            - All fields from original detection
            - device_id: Unique tracking ID
            - frames_detected: How many consecutive frames it's been seen
            - is_confirmed: True if confirmed (seen for confirmation_frames)
            - first_seen: Timestamp when first detected
            - last_seen: Timestamp of last detection
            
        Example:
            detections = detector.detect(frame)
            confirmed = tracker.update(detections)
            for device in confirmed:
                print(f"Device {device['device_id']}: {device['class_name']}")
        """
        self.frame_count += 1
        current_time = time.time()
        
        # Store current detections in history
        self.detection_history.append({
            'timestamp': current_time,
            'detections': detections,
            'frame': self.frame_count
        })
        
        # Match current detections to tracked devices
        matched_ids = set()
        
        for detection in detections:
            # Find best matching tracked device
            best_match_id = None
            best_iou = 0.0
            
            for device_id, device in self.tracked_devices.items():
                iou = self._calculate_iou(detection['bbox'], device['bbox'])
                if iou > self.iou_threshold and iou > best_iou:
                    best_iou = iou
                    best_match_id = device_id
            
            if best_match_id is not None:
                # Update existing device
                device = self.tracked_devices[best_match_id]
                device['bbox'] = detection['bbox']
                device['center'] = detection['center']
                device['confidence'] = detection['confidence']
                device['frames_detected'] += 1
                device['last_seen'] = current_time
                device['missed_frames'] = 0
                matched_ids.add(best_match_id)
                
            else:
                # New device - start tracking
                device_id = self.next_device_id
                self.next_device_id += 1
                
                self.tracked_devices[device_id] = {
                    **detection,  # Include all detection fields
                    'device_id': device_id,
                    'frames_detected': 1,
                    'is_confirmed': False,
                    'first_seen': current_time,
                    'last_seen': current_time,
                    'missed_frames': 0
                }
                matched_ids.add(device_id)
        
        # Update devices that weren't detected in this frame
        devices_to_remove = []
        for device_id, device in self.tracked_devices.items():
            if device_id not in matched_ids:
                device['missed_frames'] += 1
                
                # Remove if disappeared for too long
                if device['missed_frames'] >= self.disappearance_frames:
                    devices_to_remove.append(device_id)
        
        # Remove disappeared devices
        for device_id in devices_to_remove:
            del self.tracked_devices[device_id]
        
        # Update confirmation status
        for device in self.tracked_devices.values():
            if not device['is_confirmed']:
                if device['frames_detected'] >= self.confirmation_frames:
                    device['is_confirmed'] = True
        
        # Return only confirmed devices
        confirmed = [
            device for device in self.tracked_devices.values()
            if device['is_confirmed']
        ]
        
        return confirmed
    
    def _calculate_iou(
        self,
        bbox1: Tuple[int, int, int, int],
        bbox2: Tuple[int, int, int, int]
    ) -> float:
        """
        Calculate Intersection over Union (IoU) between two bounding boxes.
        
        Args:
            bbox1: First bounding box as (x1, y1, x2, y2)
            bbox2: Second bounding box as (x1, y1, x2, y2)
            
        Returns:
            IoU value (0-1), where 1 = perfect overlap
        """
        x1_1, y1_1, x2_1, y2_1 = bbox1
        x1_2, y1_2, x2_2, y2_2 = bbox2
        
        # Calculate intersection area
        x1_i = max(x1_1, x1_2)
        y1_i = max(y1_1, y1_2)
        x2_i = min(x2_1, x2_2)
        y2_i = min(y2_1, y2_2)
        
        if x2_i < x1_i or y2_i < y1_i:
            return 0.0  # No intersection
        
        intersection = (x2_i - x1_i) * (y2_i - y1_i)
        
        # Calculate union area
        area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
        area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
        union = area1 + area2 - intersection
        
        if union == 0:
            return 0.0
        
        return intersection / union
    
    def get_active_devices(self) -> List[Dict]:
        """
        Get all currently tracked devices (confirmed or not).
        
        Returns:
            List of all tracked devices
        """
        return list(self.tracked_devices.values())
    
    def get_confirmed_count(self) -> int:
        """
        Get count of confirmed devices.
        
        Returns:
            Number of confirmed devices currently tracked
        """
        return sum(1 for device in self.tracked_devices.values() if device['is_confirmed'])
    
    def get_cheating_devices(self) -> List[Dict]:
        """
        Get only confirmed cheating devices.
        
        Returns:
            List of confirmed devices that are cheating-related
        """
        return [
            device for device in self.tracked_devices.values()
            if device['is_confirmed'] and device['is_cheating_device']
        ]
    
    def reset(self):
        """
        Reset tracker state (clear all tracked devices).
        """
        self.tracked_devices = {}
        self.detection_history.clear()
        self.frame_count = 0
        self.next_device_id = 0
    
    def get_stats(self) -> Dict:
        """
        Get tracking statistics.
        
        Returns:
            Dictionary with tracking stats
        """
        total_devices = len(self.tracked_devices)
        confirmed_devices = self.get_confirmed_count()
        cheating_devices = len(self.get_cheating_devices())
        
        return {
            'frame_count': self.frame_count,
            'total_tracked': total_devices,
            'confirmed': confirmed_devices,
            'cheating_devices': cheating_devices,
            'tracking_ids_used': self.next_device_id
        }


# =============================================================================
# TEST SCRIPT
# =============================================================================
if __name__ == "__main__":
    """
    Test the device tracker with sample data.
    """
    print("=" * 70)
    print("DeviceTracker - Test Script")
    print("=" * 70)
    
    # Create tracker
    tracker = DeviceTracker(confirmation_frames=3, disappearance_frames=5)
    
    # Simulate detections over multiple frames
    print("\nSimulating detections:")
    
    # Frame 1-2: Phone appears
    for i in range(1, 3):
        detections = [{
            'class_id': 67,
            'class_name': 'cell phone',
            'confidence': 0.85,
            'bbox': (100, 100, 200, 250),
            'center': (150, 175),
            'is_cheating_device': True
        }]
        
        confirmed = tracker.update(detections)
        print(f"Frame {i}: {len(detections)} detected, {len(confirmed)} confirmed")
    
    # Frame 3: Phone still there (should be confirmed now)
    detections = [{
        'class_id': 67,
        'class_name': 'cell phone',
        'confidence': 0.87,
        'bbox': (105, 102, 205, 252),
        'center': (155, 177),
        'is_cheating_device': True
    }]
    
    confirmed = tracker.update(detections)
    print(f"Frame 3: {len(detections)} detected, {len(confirmed)} confirmed ⚠️")
    
    if confirmed:
        device = confirmed[0]
        print(f"  → Confirmed device: {device['class_name']} (ID: {device['device_id']})")
        print(f"     Seen for {device['frames_detected']} frames")
    
    # Frame 4-8: Phone disappears
    for i in range(4, 9):
        detections = []
        confirmed = tracker.update(detections)
        print(f"Frame {i}: {len(detections)} detected, {len(confirmed)} confirmed")
    
    # Frame 9: Phone reappears (but tracking should have been lost)
    detections = [{
        'class_id': 67,
        'class_name': 'cell phone',
        'confidence': 0.82,
        'bbox': (100, 100, 200, 250),
        'center': (150, 175),
        'is_cheating_device': True
    }]
    
    confirmed = tracker.update(detections)
    print(f"Frame 9: {len(detections)} detected, {len(confirmed)} confirmed")
    
    # Show stats
    print("\n" + "=" * 70)
    stats = tracker.get_stats()
    print("Tracking Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    print("=" * 70)
    
    print("\n✅ Test complete!")
