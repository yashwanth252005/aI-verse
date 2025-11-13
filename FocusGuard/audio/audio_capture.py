"""
Audio Capture Module
====================
Captures real-time audio from microphone for anomaly detection.

This module runs in a separate thread to continuously capture audio
without blocking the main video processing pipeline.

Author: FocusGuard Team
Date: October 24, 2025
"""

import sounddevice as sd
import numpy as np
from typing import Callable, Optional
import threading
import queue
import time


class AudioCapture:
    """
    Real-time audio capture from microphone using sounddevice.
    
    Captures audio continuously in a background thread and provides
    audio chunks to the anomaly detector for analysis.
    
    Attributes:
        sample_rate: Audio sampling rate in Hz (default: 16000)
        channels: Number of audio channels (1=mono, 2=stereo)
        chunk_duration: Duration of each audio chunk in seconds
        device_index: Microphone device index (None = default)
        
    Example:
        def process_audio(audio_chunk, timestamp):
            print(f"Got {len(audio_chunk)} samples at {timestamp}")
        
        capture = AudioCapture(callback=process_audio)
        capture.start()
        time.sleep(10)
        capture.stop()
    """
    
    def __init__(
        self,
        callback: Optional[Callable] = None,
        sample_rate: int = 16000,
        channels: int = 1,
        chunk_duration: float = 0.5,
        device_index: Optional[int] = None
    ):
        """
        Initialize audio capture.
        
        Args:
            callback: Function to call with each audio chunk (audio_data, timestamp)
            sample_rate: Sampling rate in Hz (16kHz good for speech)
            channels: Number of channels (1=mono recommended for speech)
            chunk_duration: Duration of each chunk in seconds
            device_index: Specific microphone device (None = default)
        """
        self.callback = callback
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_duration = chunk_duration
        self.device_index = device_index
        
        # Calculate chunk size in samples
        self.chunk_size = int(sample_rate * chunk_duration)
        
        # Thread control
        self.is_running = False
        self.capture_thread = None
        self.audio_queue = queue.Queue(maxsize=10)
        
        # Statistics
        self.chunks_captured = 0
        self.start_time = None
        
        print("✓ AudioCapture initialized")
        print(f"  → Sample rate: {sample_rate} Hz")
        print(f"  → Channels: {channels} (mono)")
        print(f"  → Chunk size: {self.chunk_size} samples ({chunk_duration}s)")
    
    def start(self):
        """
        Start capturing audio in background thread.
        
        Returns:
            bool: True if started successfully, False otherwise
        """
        if self.is_running:
            print("⚠️  Audio capture already running")
            return False
        
        try:
            # List available audio devices for debugging
            devices = sd.query_devices()
            print(f"📢 Found {len(devices)} audio devices")
            
            if self.device_index is None:
                default_device = sd.query_devices(kind='input')
                print(f"  → Using default input: {default_device['name']}")
            else:
                print(f"  → Using device {self.device_index}")
            
            self.is_running = True
            self.start_time = time.time()
            self.chunks_captured = 0
            
            # Start capture thread
            self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.capture_thread.start()
            
            print("✓ Audio capture started")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start audio capture: {e}")
            self.is_running = False
            return False
    
    def stop(self):
        """Stop capturing audio and clean up resources."""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # Wait for thread to finish
        if self.capture_thread:
            self.capture_thread.join(timeout=2.0)
        
        elapsed = time.time() - self.start_time if self.start_time else 0
        print(f"✓ Audio capture stopped")
        print(f"  → Captured {self.chunks_captured} chunks in {elapsed:.1f}s")
    
    def _capture_loop(self):
        """
        Internal method: Continuous audio capture loop (runs in thread).
        
        This uses sounddevice's callback mode for efficient streaming.
        """
        def audio_callback(indata, frames, time_info, status):
            """Called by sounddevice for each audio chunk."""
            if status:
                print(f"⚠️  Audio callback status: {status}")
            
            # Copy audio data (indata is reused by sounddevice)
            audio_chunk = indata.copy().flatten()
            timestamp = time.time()
            
            # Put in queue for processing
            try:
                self.audio_queue.put((audio_chunk, timestamp), block=False)
            except queue.Full:
                pass  # Drop frame if queue full
        
        try:
            # Open audio stream
            with sd.InputStream(
                callback=audio_callback,
                device=self.device_index,
                channels=self.channels,
                samplerate=self.sample_rate,
                blocksize=self.chunk_size
            ):
                print("🎤 Audio stream opened, capturing...")
                
                # Process queued audio chunks
                while self.is_running:
                    try:
                        # Get audio chunk from queue
                        audio_chunk, timestamp = self.audio_queue.get(timeout=0.1)
                        
                        # Call user callback
                        if self.callback:
                            self.callback(audio_chunk, timestamp)
                        
                        self.chunks_captured += 1
                        
                    except queue.Empty:
                        continue
                    except Exception as e:
                        print(f"⚠️  Error processing audio chunk: {e}")
        
        except Exception as e:
            print(f"❌ Audio stream error: {e}")
            self.is_running = False
    
    def get_stats(self) -> dict:
        """
        Get capture statistics.
        
        Returns:
            Dictionary with statistics:
            {
                'is_running': bool,
                'chunks_captured': int,
                'elapsed_time': float,
                'sample_rate': int,
                'chunk_duration': float
            }
        """
        elapsed = time.time() - self.start_time if self.start_time else 0
        
        return {
            'is_running': self.is_running,
            'chunks_captured': self.chunks_captured,
            'elapsed_time': elapsed,
            'sample_rate': self.sample_rate,
            'chunk_duration': self.chunk_duration
        }
    
    @staticmethod
    def list_devices():
        """
        List all available audio input devices.
        
        Returns:
            List of device dictionaries with name and index
        """
        try:
            devices = sd.query_devices()
            input_devices = []
            
            for idx, device in enumerate(devices):
                if device['max_input_channels'] > 0:
                    input_devices.append({
                        'index': idx,
                        'name': device['name'],
                        'channels': device['max_input_channels'],
                        'sample_rate': device['default_samplerate']
                    })
            
            return input_devices
        except Exception as e:
            print(f"❌ Error listing audio devices: {e}")
            return []


# =============================================================================
# EXAMPLE USAGE
# =============================================================================
if __name__ == "__main__":
    print("=== AudioCapture Test ===\n")
    
    # List available devices
    print("Available audio input devices:")
    devices = AudioCapture.list_devices()
    for device in devices:
        print(f"  [{device['index']}] {device['name']} ({device['channels']} channels)")
    print()
    
    # Simple callback to monitor audio level
    def monitor_audio(audio_chunk, timestamp):
        # Calculate RMS (root mean square) as volume indicator
        rms = np.sqrt(np.mean(audio_chunk**2))
        db = 20 * np.log10(rms + 1e-10)  # Convert to decibels
        
        # Simple ASCII volume meter
        bars = int((db + 60) / 3)  # Map -60dB to 0dB into 0-20 bars
        bars = max(0, min(20, bars))
        meter = "█" * bars + "░" * (20 - bars)
        
        print(f"\rVolume: [{meter}] {db:.1f} dB", end='', flush=True)
    
    # Start capture
    capture = AudioCapture(callback=monitor_audio, chunk_duration=0.1)
    
    if capture.start():
        print("Capturing audio for 10 seconds (speak into your microphone)...\n")
        time.sleep(10)
        capture.stop()
        
        # Show stats
        stats = capture.get_stats()
        print(f"\n\nStatistics:")
        print(f"  Chunks captured: {stats['chunks_captured']}")
        print(f"  Duration: {stats['elapsed_time']:.1f}s")
    else:
        print("Failed to start audio capture")
