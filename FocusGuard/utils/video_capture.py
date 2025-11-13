"""
Video Capture Module
====================
Handles webcam capture with threading for smooth, non-blocking frame reading.
This prevents the main application from freezing while waiting for camera frames.

Usage:
    camera = WebcamCapture(camera_index=0, target_fps=30)
    camera.start()
    success, frame = camera.read_frame()
    camera.release()

Author: FocusGuard Team
Date: October 24, 2025
"""

import cv2
import threading
import time
from typing import Tuple, Optional
import numpy as np


class WebcamCapture:
    """
    Thread-safe webcam capture class that continuously reads frames in the background.
    
    This class uses a separate thread to grab frames from the camera, which prevents
    the main application from blocking on slow camera operations. It maintains a buffer
    of the most recent frame for instant access.
    
    Attributes:
        camera_index (int): Index of the camera device (0 = default camera)
        target_fps (int): Target frames per second for capture
        frame_width (int): Width of captured frames in pixels
        frame_height (int): Height of captured frames in pixels
    """
    
    def __init__(
        self, 
        camera_index: int = 0,
        target_fps: int = 30,
        frame_width: int = 640,
        frame_height: int = 480
    ):
        """
        Initialize the webcam capture.
        
        Args:
            camera_index: Camera device index (0 for built-in, 1+ for external)
            target_fps: Desired frames per second
            frame_width: Frame width in pixels
            frame_height: Frame height in pixels
        """
        # Store camera parameters
        self.camera_index = camera_index
        self.target_fps = target_fps
        self.frame_width = frame_width
        self.frame_height = frame_height
        
        # Initialize the OpenCV video capture object
        self.cap = cv2.VideoCapture(camera_index)
        
        # Set camera properties for optimal performance
        # Note: Not all cameras support all properties, but we try anyway
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)
        self.cap.set(cv2.CAP_PROP_FPS, target_fps)
        
        # Thread-related variables
        self.thread = None  # Background thread for frame reading
        self.is_running = False  # Flag to control the thread loop
        self.frame = None  # Most recent frame (shared between threads)
        self.frame_lock = threading.Lock()  # Protects the frame variable from race conditions
        
        # Performance tracking
        self.frame_count = 0  # Total frames captured
        self.start_time = time.time()  # When capture started
        self.last_frame_time = time.time()  # Timestamp of last frame
        
        # Release protection flag
        self._released = False  # Prevents double-release from __del__
        
        # Check if camera opened successfully
        if not self.cap.isOpened():
            raise RuntimeError(
                f"Failed to open camera at index {camera_index}. "
                f"Please check if the camera is connected and not in use by another application."
            )
    
    def start(self):
        """
        Start the background thread that continuously captures frames.
        
        This method spawns a daemon thread that runs _capture_loop() in the background.
        The daemon flag ensures the thread terminates when the main program exits.
        """
        if self.is_running:
            print("Warning: Camera capture is already running!")
            return
        
        # Set the running flag to True before starting the thread
        self.is_running = True
        
        # Create and start the background thread
        # daemon=True means the thread will automatically stop when the main program exits
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()
        
        # Give the camera more time to initialize and capture first frame
        # This is especially important for Streamlit where reruns can happen quickly
        time.sleep(1.0)
        
        print(f"✓ Camera started successfully (Index: {self.camera_index}, "
              f"Resolution: {self.frame_width}x{self.frame_height}, "
              f"Target FPS: {self.target_fps})")
    
    def _capture_loop(self):
        """
        Internal method that runs in a background thread.
        
        This continuously reads frames from the camera and updates the shared frame buffer.
        It runs until is_running is set to False by the release() method.
        """
        # Calculate delay between frames to achieve target FPS
        # For 30 FPS, delay = 1/30 = 0.033 seconds
        frame_delay = 1.0 / self.target_fps
        
        while self.is_running:
            loop_start = time.time()
            
            # Check if camera is still valid before reading
            if not self.cap or not self.cap.isOpened():
                # Camera released or disconnected - stop gracefully
                print(f"Camera {self.camera_index} no longer available. Stopping capture loop.")
                self.is_running = False
                break
            
            # Read a frame from the camera
            # ret = True if frame was successfully read, False otherwise
            # frame = the captured image as a numpy array (BGR format)
            ret, frame = self.cap.read()
            
            if ret:
                # Successfully captured a frame
                # Use a lock to prevent race conditions when accessing self.frame
                with self.frame_lock:
                    self.frame = frame.copy()  # Make a copy to avoid overwriting
                    self.last_frame_time = time.time()
                    self.frame_count += 1
            else:
                # Failed to read frame - check if we're still supposed to be running
                if self.is_running:
                    print(f"Warning: Failed to read frame from camera {self.camera_index}")
                    time.sleep(0.1)  # Wait a bit before retrying
                continue
            
            # Calculate how long we need to sleep to maintain target FPS
            elapsed = time.time() - loop_start
            sleep_time = max(0, frame_delay - elapsed)
            
            if sleep_time > 0:
                time.sleep(sleep_time)
    
    def read_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Read the most recent frame from the camera.
        
        This method is thread-safe and non-blocking. It returns immediately with
        the latest available frame, even if it's slightly old.
        
        Returns:
            Tuple containing:
                - success (bool): True if a frame is available, False otherwise
                - frame (numpy.ndarray or None): The frame as BGR image, or None if no frame available
        
        Example:
            success, frame = camera.read_frame()
            if success:
                cv2.imshow('Camera', frame)
        """
        # Use lock to safely access the shared frame variable
        with self.frame_lock:
            if self.frame is not None:
                # Return a copy to prevent external modifications
                return True, self.frame.copy()
            else:
                return False, None
    
    def get_fps(self) -> float:
        """
        Calculate the actual frames per second being captured.
        
        Returns:
            float: Current FPS (frames per second)
        """
        elapsed = time.time() - self.start_time
        if elapsed > 0 and self.frame_count > 0:
            return self.frame_count / elapsed
        return 0.0
    
    def get_resolution(self) -> Tuple[int, int]:
        """
        Get the actual resolution of captured frames.
        
        Returns:
            Tuple of (width, height) in pixels
        """
        # Try to get from current frame first
        with self.frame_lock:
            if self.frame is not None:
                height, width = self.frame.shape[:2]
                return width, height
        
        # Fallback to camera properties
        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        return width, height
    
    def is_frame_recent(self, max_age_seconds: float = 1.0) -> bool:
        """
        Check if the current frame is recent (not stale).
        
        Useful for detecting if the camera has frozen or disconnected.
        
        Args:
            max_age_seconds: Maximum age in seconds for a frame to be considered "recent"
        
        Returns:
            bool: True if frame is recent, False if stale or no frame available
        """
        if self.frame is None:
            return False
        
        age = time.time() - self.last_frame_time
        return age <= max_age_seconds
    
    def release(self):
        """
        Stop capturing and release camera resources.
        
        This method stops the background thread and releases the camera device
        so other applications can use it.
        
        IMPORTANT: Always call this when you're done with the camera!
        """
        # Prevent double-release (common in Streamlit with __del__ and explicit calls)
        if self._released:
            return
        
        self._released = True
        
        # Signal the background thread to stop
        self.is_running = False
        
        # Wait for the thread to finish (with timeout)
        if self.thread is not None and self.thread.is_alive():
            self.thread.join(timeout=2.0)  # Wait up to 2 seconds
        
        # Release the camera device
        if self.cap is not None:
            self.cap.release()
        
        # Calculate final statistics (only if frames were actually captured)
        total_time = time.time() - self.start_time
        avg_fps = self.frame_count / total_time if total_time > 0 else 0
        
        # Only print stats if camera was actually used
        if self.frame_count > 0:
            print(f"✓ Camera released. Stats: {self.frame_count} frames in {total_time:.1f}s "
                  f"(Average FPS: {avg_fps:.1f})")
        else:
            print(f"✓ Camera released (no frames captured - likely cleaned up during initialization)")
    
    def __enter__(self):
        """
        Context manager entry - starts the camera.
        
        Allows using the camera with 'with' statement:
            with WebcamCapture() as camera:
                success, frame = camera.read_frame()
        """
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit - releases the camera.
        """
        self.release()
        return False  # Don't suppress exceptions
    
    def __del__(self):
        """
        Destructor - ensures camera is released when object is garbage collected.
        
        Note: In Streamlit, this may be called during reruns. The _released flag
        prevents multiple releases.
        """
        if not self._released:
            self.release()


# Example usage and testing
if __name__ == "__main__":
    """
    Test the webcam capture module.
    
    Run this file directly to test your camera:
        python utils/video_capture.py
    
    Press 'q' to quit.
    """
    print("Testing WebcamCapture module...")
    print("Press 'q' to quit\n")
    
    try:
        # Create camera capture object
        camera = WebcamCapture(camera_index=0, target_fps=30)
        camera.start()
        
        # Display frames until user presses 'q'
        while True:
            success, frame = camera.read_frame()
            
            if success:
                # Add FPS counter to the frame
                fps = camera.get_fps()
                width, height = camera.get_resolution()
                
                cv2.putText(
                    frame, 
                    f"FPS: {fps:.1f} | Resolution: {width}x{height}",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2
                )
                
                cv2.imshow('Webcam Test - Press Q to Quit', frame)
            
            # Check for 'q' key press (wait 1ms)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        # Clean up
        camera.release()
        cv2.destroyAllWindows()
        
        print("\n✓ Test completed successfully!")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
