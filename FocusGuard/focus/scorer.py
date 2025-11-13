"""
Focus Scorer Module
===================
Calculates comprehensive focus score (0-100) combining multiple factors.

This module creates a unified attention score by combining:
1. Face attention baseline (head pose quality)
2. Device detection penalties (phones, books, etc.)
3. Temporal factors (time looking away, sustained attention)
4. Multiple person penalties

Author: FocusGuard Team
Date: October 24, 2025
"""

import time
from typing import Dict, List, Optional
from collections import deque
import numpy as np


class FocusScorer:
    """
    Calculates comprehensive focus score combining multiple attention factors.
    
    The scoring system works as follows:
    - Start with base score from head pose (0-100)
    - Apply device penalties (-30 points per cheating device)
    - Apply temporal penalties (looking away too long)
    - Apply multiple person penalty (-50 points)
    
    Score Interpretation:
    - 90-100: Excellent focus (Green)
    - 70-89: Good focus (Light Green)
    - 50-69: Fair focus (Yellow)
    - 30-49: Poor focus (Orange)
    - 0-29: Critical - Cheating likely (Red)
    
    Attributes:
        device_penalty: Points deducted per detected device
        multiple_person_penalty: Points deducted when >1 person detected
        looking_away_threshold: Seconds before temporal penalty kicks in
        history_window: Seconds of history to maintain for trends
        
    Example:
        scorer = FocusScorer()
        
        # Each frame
        score_data = scorer.calculate_score(
            head_pose_score=85,
            face_detected=True,
            devices_detected=[{'class_name': 'cell phone'}],
            person_count=1
        )
        print(f"Focus: {score_data['final_score']}/100")
    """
    
    def __init__(
        self,
        device_penalty: int = 30,
        multiple_person_penalty: int = 50,
        looking_away_threshold: float = 3.0,
        temporal_penalty_rate: int = 5,  # Points per second looking away
        history_window: float = 60.0
    ):
        """
        Initialize focus scorer.
        
        Args:
            device_penalty: Points to deduct per detected cheating device
            multiple_person_penalty: Points to deduct when multiple people detected
            looking_away_threshold: Seconds of looking away before temporal penalty
            temporal_penalty_rate: Points deducted per second looking away (after threshold)
            history_window: Seconds of score history to maintain
        """
        self.device_penalty = device_penalty
        self.multiple_person_penalty = multiple_person_penalty
        self.looking_away_threshold = looking_away_threshold
        self.temporal_penalty_rate = temporal_penalty_rate
        self.history_window = history_window
        
        # Score history for trend analysis
        self.score_history = deque(maxlen=1000)  # Last ~30 seconds at 30 FPS
        
        # Tracking state
        self.looking_away_start = None
        self.total_looking_away_time = 0.0
        self.device_detection_count = 0
        self.session_start = time.time()
        
        print("✓ FocusScorer initialized")
        print(f"  → Device penalty: -{device_penalty} points")
        print(f"  → Multiple person penalty: -{multiple_person_penalty} points")
        print(f"  → Temporal penalty: -{temporal_penalty_rate} pts/sec after {looking_away_threshold}s")
    
    def calculate_score(
        self,
        head_pose_score: float,
        face_detected: bool,
        devices_detected: List[Dict],
        person_count: int = 1
    ) -> Dict:
        """
        Calculate comprehensive focus score from multiple factors.
        
        Args:
            head_pose_score: Base attention score from head pose (0-100)
            face_detected: Whether face is currently detected
            devices_detected: List of detected cheating devices
            person_count: Number of people detected in frame
            
        Returns:
            Dictionary containing:
            - final_score: Overall focus score (0-100)
            - base_score: Original head pose score
            - device_penalty_applied: Points deducted for devices
            - temporal_penalty_applied: Points deducted for looking away
            - multiple_person_penalty_applied: Points deducted for multiple people
            - status: Text status (Excellent/Good/Fair/Poor/Critical)
            - status_color: Color for UI (green/yellow/orange/red)
            - warnings: List of active warning messages
            
        Example:
            score = scorer.calculate_score(
                head_pose_score=85,
                face_detected=True,
                devices_detected=[],
                person_count=1
            )
            print(f"Score: {score['final_score']} - {score['status']}")
        """
        current_time = time.time()
        
        # Start with base score from head pose
        score = head_pose_score
        
        # Track penalties
        device_penalty_applied = 0
        temporal_penalty_applied = 0
        multiple_person_penalty_applied = 0
        warnings = []
        
        # === 1. DEVICE DETECTION PENALTY ===
        if devices_detected and len(devices_detected) > 0:
            device_penalty_applied = len(devices_detected) * self.device_penalty
            score -= device_penalty_applied
            
            device_names = [d.get('class_name', 'device') for d in devices_detected]
            warnings.append(f"[ALERT] {len(devices_detected)} device(s) detected: {', '.join(device_names)}")
            self.device_detection_count += 1
        
        # === 2. MULTIPLE PERSON PENALTY ===
        if person_count > 1:
            multiple_person_penalty_applied = self.multiple_person_penalty
            score -= multiple_person_penalty_applied
            warnings.append(f"[ALERT] Multiple people detected ({person_count} people)")
        
        # === 3. TEMPORAL PENALTY (Looking away for extended time) ===
        if not face_detected:
            # Track start of looking away
            if self.looking_away_start is None:
                self.looking_away_start = current_time
            
            # Calculate how long user has been looking away
            looking_away_duration = current_time - self.looking_away_start
            
            # Apply penalty if exceeding threshold
            if looking_away_duration > self.looking_away_threshold:
                excess_time = looking_away_duration - self.looking_away_threshold
                temporal_penalty_applied = int(excess_time * self.temporal_penalty_rate)
                score -= temporal_penalty_applied
                
                warnings.append(f"[ALERT] Looking away for {looking_away_duration:.1f}s")
                self.total_looking_away_time += (current_time - self.looking_away_start)
        else:
            # Face detected - reset looking away timer
            if self.looking_away_start is not None:
                self.total_looking_away_time += (current_time - self.looking_away_start)
                self.looking_away_start = None
        
        # === CLAMP SCORE TO 0-100 ===
        score = max(0, min(100, score))
        
        # === DETERMINE STATUS AND COLOR ===
        if score >= 90:
            status = "Excellent Focus"
            status_color = "green"
        elif score >= 70:
            status = "Good Focus"
            status_color = "lightgreen"
        elif score >= 50:
            status = "Fair Focus"
            status_color = "yellow"
        elif score >= 30:
            status = "Poor Focus"
            status_color = "orange"
        else:
            status = "⚠️ CRITICAL - Possible Cheating"
            status_color = "red"
        
        # === STORE IN HISTORY ===
        score_entry = {
            'timestamp': current_time,
            'score': score,
            'base_score': head_pose_score,
            'device_penalty': device_penalty_applied,
            'temporal_penalty': temporal_penalty_applied,
            'multiple_person_penalty': multiple_person_penalty_applied
        }
        self.score_history.append(score_entry)
        
        # === BUILD RESULT ===
        result = {
            'final_score': score,
            'base_score': head_pose_score,
            'device_penalty_applied': device_penalty_applied,
            'temporal_penalty_applied': temporal_penalty_applied,
            'multiple_person_penalty_applied': multiple_person_penalty_applied,
            'status': status,
            'status_color': status_color,
            'warnings': warnings,
            'session_duration': current_time - self.session_start,
            'total_looking_away_time': self.total_looking_away_time,
            'device_detection_count': self.device_detection_count
        }
        
        return result
    
    def get_statistics(self) -> Dict:
        """
        Get session statistics and trends.
        
        Returns:
            Dictionary with:
            - average_score: Mean score over session
            - min_score: Lowest score recorded
            - max_score: Highest score recorded
            - score_trend: Recent trend (increasing/stable/decreasing)
            - total_penalties: Sum of all penalties applied
            - focus_time_percentage: % of time with good focus (>70)
            
        Example:
            stats = scorer.get_statistics()
            print(f"Average: {stats['average_score']:.1f}")
            print(f"Trend: {stats['score_trend']}")
        """
        if not self.score_history:
            return {
                'average_score': 0,
                'min_score': 0,
                'max_score': 0,
                'score_trend': 'No data',
                'total_penalties': 0,
                'focus_time_percentage': 0
            }
        
        scores = [entry['score'] for entry in self.score_history]
        
        # Basic statistics
        avg_score = np.mean(scores)
        min_score = np.min(scores)
        max_score = np.max(scores)
        
        # Calculate trend (last 10 seconds vs previous 10 seconds)
        half_point = len(scores) // 2
        if len(scores) > 20:
            recent_avg = np.mean(scores[-half_point:])
            previous_avg = np.mean(scores[:half_point])
            
            if recent_avg > previous_avg + 5:
                trend = "📈 Improving"
            elif recent_avg < previous_avg - 5:
                trend = "📉 Declining"
            else:
                trend = "➡️ Stable"
        else:
            trend = "⏳ Collecting data..."
        
        # Calculate total penalties
        total_device_penalties = sum(entry['device_penalty'] for entry in self.score_history)
        total_temporal_penalties = sum(entry['temporal_penalty'] for entry in self.score_history)
        total_person_penalties = sum(entry['multiple_person_penalty'] for entry in self.score_history)
        total_penalties = total_device_penalties + total_temporal_penalties + total_person_penalties
        
        # Calculate focus time percentage (score > 70)
        good_focus_frames = sum(1 for s in scores if s >= 70)
        focus_percentage = (good_focus_frames / len(scores)) * 100
        
        return {
            'average_score': avg_score,
            'min_score': min_score,
            'max_score': max_score,
            'score_trend': trend,
            'total_penalties': total_penalties,
            'focus_time_percentage': focus_percentage,
            'total_device_penalties': total_device_penalties,
            'total_temporal_penalties': total_temporal_penalties,
            'total_person_penalties': total_person_penalties
        }
    
    def reset(self):
        """Reset scorer state for new session."""
        self.score_history.clear()
        self.looking_away_start = None
        self.total_looking_away_time = 0.0
        self.device_detection_count = 0
        self.session_start = time.time()
        print("✓ FocusScorer reset for new session")
