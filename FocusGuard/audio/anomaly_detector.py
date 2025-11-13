"""
Audio Anomaly Detector Module
==============================
Detects audio anomalies like voices, background noise, and unusual sounds.

Uses FFT analysis and energy detection to identify suspicious audio patterns
that might indicate cheating (conversations, phone calls, etc.).

Author: FocusGuard Team
Date: October 24, 2025
"""

import numpy as np
from scipy import signal
from typing import Dict, List, Optional
from collections import deque
import time


class AudioAnomalyDetector:
    """
    Detects audio anomalies using frequency analysis.
    
    This detector analyzes audio chunks to identify:
    - Voice activity (speech detection)
    - Background conversations
    - Sudden loud noises
    - Sustained audio (keyboard typing, paper rustling)
    
    Uses FFT (Fast Fourier Transform) to analyze frequency spectrum
    and energy thresholds to detect activity.
    
    Attributes:
        sample_rate: Audio sampling rate in Hz
        voice_freq_range: Frequency range for voice (Hz)
        noise_threshold_db: dB threshold for noise detection
        voice_threshold_db: dB threshold for voice detection
        
    Example:
        detector = AudioAnomalyDetector(sample_rate=16000)
        
        # Analyze audio chunk
        result = detector.analyze(audio_chunk)
        if result['voice_detected']:
            print("Voice activity detected!")
    """
    
    def __init__(
        self,
        sample_rate: int = 16000,
        voice_freq_range: tuple = (85, 3400),  # Human speech range
        noise_threshold_db: float = -40.0,
        voice_threshold_db: float = -30.0,
        history_seconds: float = 5.0
    ):
        """
        Initialize audio anomaly detector.
        
        Args:
            sample_rate: Audio sampling rate in Hz
            voice_freq_range: (min_freq, max_freq) for voice detection
            noise_threshold_db: Threshold for general noise (lower = more sensitive)
            voice_threshold_db: Threshold for voice detection
            history_seconds: Seconds of history to maintain
        """
        self.sample_rate = sample_rate
        self.voice_freq_range = voice_freq_range
        self.noise_threshold_db = noise_threshold_db
        self.voice_threshold_db = voice_threshold_db
        
        # History tracking
        max_history_samples = int(history_seconds * 10)  # ~10 chunks per second
        self.energy_history = deque(maxlen=max_history_samples)
        self.voice_activity_history = deque(maxlen=max_history_samples)
        
        # Statistics
        self.chunks_analyzed = 0
        self.voice_detections = 0
        self.noise_detections = 0
        self.last_voice_time = None
        
        print("✓ AudioAnomalyDetector initialized")
        print(f"  → Voice frequency range: {voice_freq_range[0]}-{voice_freq_range[1]} Hz")
        print(f"  → Noise threshold: {noise_threshold_db} dB")
        print(f"  → Voice threshold: {voice_threshold_db} dB")
    
    def analyze(self, audio_chunk: np.ndarray) -> Dict:
        """
        Analyze audio chunk for anomalies.
        
        Args:
            audio_chunk: 1D numpy array of audio samples
        
        Returns:
            Dictionary containing:
            {
                'timestamp': float,
                'energy_db': float,              # Overall energy in dB
                'voice_detected': bool,           # Voice activity detected
                'noise_detected': bool,           # General noise detected
                'voice_energy_db': float,         # Energy in voice frequencies
                'background_energy_db': float,    # Energy in non-voice frequencies
                'spectral_peak_freq': float,      # Dominant frequency
                'anomaly_score': float,           # 0-100 anomaly score
                'warnings': list                  # List of warning messages
            }
        
        Example:
            result = detector.analyze(audio_chunk)
            if result['voice_detected']:
                print(f"Voice detected! Energy: {result['voice_energy_db']} dB")
        """
        timestamp = time.time()
        warnings = []
        
        # Calculate overall energy (RMS in dB)
        rms = np.sqrt(np.mean(audio_chunk**2))
        energy_db = 20 * np.log10(rms + 1e-10)  # Add small value to avoid log(0)
        
        # Perform FFT to analyze frequency spectrum
        fft = np.fft.rfft(audio_chunk)
        fft_magnitude = np.abs(fft)
        fft_db = 20 * np.log10(fft_magnitude + 1e-10)
        
        # Frequency bins
        freqs = np.fft.rfftfreq(len(audio_chunk), 1/self.sample_rate)
        
        # Analyze voice frequency range (85-3400 Hz for human speech)
        voice_mask = (freqs >= self.voice_freq_range[0]) & (freqs <= self.voice_freq_range[1])
        voice_energy = np.mean(fft_db[voice_mask]) if np.any(voice_mask) else -100
        
        # Analyze background (non-voice frequencies)
        background_mask = ~voice_mask
        background_energy = np.mean(fft_db[background_mask]) if np.any(background_mask) else -100
        
        # Find spectral peak (dominant frequency)
        peak_idx = np.argmax(fft_magnitude)
        spectral_peak_freq = freqs[peak_idx]
        
        # === DETECTION LOGIC ===
        
        # 1. Voice detection (energy in voice range + overall energy)
        voice_detected = (voice_energy > self.voice_threshold_db and 
                         energy_db > self.noise_threshold_db)
        
        if voice_detected:
            self.voice_detections += 1
            self.last_voice_time = timestamp
            warnings.append("Voice activity detected")
        
        # 2. General noise detection
        noise_detected = energy_db > self.noise_threshold_db
        
        if noise_detected and not voice_detected:
            self.noise_detections += 1
            warnings.append("Background noise detected")
        
        # 3. Calculate anomaly score (0-100)
        # Higher score = more suspicious audio
        anomaly_score = 0
        
        if voice_detected:
            # Voice is highly suspicious during an exam
            anomaly_score = min(100, 60 + (voice_energy - self.voice_threshold_db) * 2)
            warnings.append(f"Anomaly score: {anomaly_score:.0f}/100")
        elif noise_detected:
            # General noise less suspicious but still flagged
            anomaly_score = min(100, 30 + (energy_db - self.noise_threshold_db) * 1.5)
        
        # Store in history
        self.energy_history.append(energy_db)
        self.voice_activity_history.append(voice_detected)
        self.chunks_analyzed += 1
        
        # Build result
        result = {
            'timestamp': timestamp,
            'energy_db': float(energy_db),
            'voice_detected': voice_detected,
            'noise_detected': noise_detected,
            'voice_energy_db': float(voice_energy),
            'background_energy_db': float(background_energy),
            'spectral_peak_freq': float(spectral_peak_freq),
            'anomaly_score': float(anomaly_score),
            'warnings': warnings
        }
        
        return result
    
    def get_statistics(self) -> Dict:
        """
        Get detection statistics.
        
        Returns:
            Dictionary with:
            - chunks_analyzed: Total chunks analyzed
            - voice_detections: Number of voice detections
            - noise_detections: Number of noise detections
            - voice_detection_rate: Percentage of chunks with voice
            - average_energy_db: Average audio energy
            - seconds_since_last_voice: Time since last voice detection
        """
        voice_rate = (self.voice_detections / self.chunks_analyzed * 100) if self.chunks_analyzed > 0 else 0
        avg_energy = np.mean(self.energy_history) if self.energy_history else -100
        
        seconds_since_voice = None
        if self.last_voice_time:
            seconds_since_voice = time.time() - self.last_voice_time
        
        return {
            'chunks_analyzed': self.chunks_analyzed,
            'voice_detections': self.voice_detections,
            'noise_detections': self.noise_detections,
            'voice_detection_rate': voice_rate,
            'average_energy_db': float(avg_energy),
            'seconds_since_last_voice': seconds_since_voice
        }
    
    def is_sustained_voice(self, duration_seconds: float = 2.0) -> bool:
        """
        Check if voice has been detected consistently for a duration.
        
        Args:
            duration_seconds: Minimum duration to check
        
        Returns:
            True if voice detected consistently for the duration
        """
        if not self.voice_activity_history:
            return False
        
        # Calculate how many chunks correspond to the duration
        chunks_needed = int(duration_seconds * 10)  # ~10 chunks per second
        chunks_needed = min(chunks_needed, len(self.voice_activity_history))
        
        if chunks_needed < 2:
            return False
        
        # Check recent history
        recent_voice = list(self.voice_activity_history)[-chunks_needed:]
        voice_percentage = sum(recent_voice) / len(recent_voice)
        
        # Voice detected in at least 70% of recent chunks
        return voice_percentage >= 0.7
    
    def reset(self):
        """Reset detector statistics and history."""
        self.energy_history.clear()
        self.voice_activity_history.clear()
        self.chunks_analyzed = 0
        self.voice_detections = 0
        self.noise_detections = 0
        self.last_voice_time = None
        print("✓ AudioAnomalyDetector reset")


# =============================================================================
# EXAMPLE USAGE
# =============================================================================
if __name__ == "__main__":
    print("=== AudioAnomalyDetector Test ===\n")
    
    # Create detector
    detector = AudioAnomalyDetector(sample_rate=16000)
    
    # Generate test signals
    print("\n1. Testing with silence:")
    silence = np.zeros(8000)  # 0.5 seconds of silence
    result = detector.analyze(silence)
    print(f"   Voice detected: {result['voice_detected']}")
    print(f"   Energy: {result['energy_db']:.1f} dB")
    
    print("\n2. Testing with pure tone (440 Hz - musical A):")
    t = np.linspace(0, 0.5, 8000)
    tone = 0.3 * np.sin(2 * np.pi * 440 * t)
    result = detector.analyze(tone)
    print(f"   Voice detected: {result['voice_detected']}")
    print(f"   Peak frequency: {result['spectral_peak_freq']:.1f} Hz")
    print(f"   Energy: {result['energy_db']:.1f} dB")
    
    print("\n3. Testing with voice-range frequencies (mix of 200-1000 Hz):")
    voice_sim = 0.5 * (
        np.sin(2 * np.pi * 200 * t) +
        np.sin(2 * np.pi * 500 * t) +
        np.sin(2 * np.pi * 1000 * t)
    )
    result = detector.analyze(voice_sim)
    print(f"   Voice detected: {result['voice_detected']}")
    print(f"   Voice energy: {result['voice_energy_db']:.1f} dB")
    print(f"   Anomaly score: {result['anomaly_score']:.0f}/100")
    
    print("\n4. Testing sustained voice detection:")
    for i in range(25):  # Simulate 2.5 seconds of voice
        result = detector.analyze(voice_sim)
    
    is_sustained = detector.is_sustained_voice(duration_seconds=2.0)
    print(f"   Sustained voice (2s): {is_sustained}")
    
    # Show statistics
    stats = detector.get_statistics()
    print(f"\nStatistics:")
    print(f"  Chunks analyzed: {stats['chunks_analyzed']}")
    print(f"  Voice detections: {stats['voice_detections']}")
    print(f"  Voice detection rate: {stats['voice_detection_rate']:.1f}%")
