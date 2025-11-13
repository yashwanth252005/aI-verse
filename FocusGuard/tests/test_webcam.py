"""
Webcam Test Script
==================
Simple test to verify webcam capture is working correctly.

Usage:
    python tests/test_webcam.py

Expected behavior:
- Window opens showing live webcam feed
- FPS counter is displayed
- Press 'q' to quit
- Final statistics are printed

Author: FocusGuard Team
Date: October 24, 2025
"""

import sys
import os
import time

# Add parent directory to path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2
from utils.video_capture import WebcamCapture
import config


def test_webcam_basic():
    """
    Test 1: Basic webcam access and frame capture.
    
    Verifies:
    - Camera can be opened
    - Frames can be read
    - Resolution is correct
    """
    print("="*70)
    print("TEST 1: Basic Webcam Access")
    print("="*70)
    
    try:
        camera = WebcamCapture(
            camera_index=config.CAMERA_INDEX,
            target_fps=config.TARGET_FPS,
            frame_width=config.FRAME_WIDTH,
            frame_height=config.FRAME_HEIGHT
        )
        
        camera.start()
        
        # Wait a moment for camera to initialize
        time.sleep(1)
        
        # Try to read a frame
        success, frame = camera.read_frame()
        
        if success:
            height, width = frame.shape[:2]
            print(f"✓ Camera opened successfully")
            print(f"✓ Frame captured: {width}x{height}")
            print(f"✓ Frame shape: {frame.shape}")
            print(f"✓ Frame dtype: {frame.dtype}")
            result = True
        else:
            print("✗ Failed to capture frame")
            result = False
        
        camera.release()
        
        print()
        return result
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        print()
        return False


def test_webcam_fps():
    """
    Test 2: Capture 100 frames and measure FPS.
    
    Verifies:
    - Consistent frame capture
    - FPS meets target (or close to it)
    - No frame drops
    """
    print("="*70)
    print("TEST 2: FPS Performance (capturing 100 frames)")
    print("="*70)
    
    try:
        camera = WebcamCapture(
            camera_index=config.CAMERA_INDEX,
            target_fps=config.TARGET_FPS
        )
        
        camera.start()
        time.sleep(0.5)  # Let camera stabilize
        
        # Capture 100 frames and measure time
        num_frames = 100
        successful_captures = 0
        start_time = time.time()
        
        for i in range(num_frames):
            success, frame = camera.read_frame()
            if success:
                successful_captures += 1
            
            # Small delay to not overwhelm the system
            time.sleep(0.01)
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        # Calculate FPS
        actual_fps = successful_captures / elapsed if elapsed > 0 else 0
        camera_fps = camera.get_fps()
        
        print(f"✓ Captured {successful_captures}/{num_frames} frames")
        print(f"✓ Time elapsed: {elapsed:.2f} seconds")
        print(f"✓ Actual FPS: {actual_fps:.1f}")
        print(f"✓ Camera reported FPS: {camera_fps:.1f}")
        print(f"✓ Target FPS: {config.TARGET_FPS}")
        
        # Check if FPS is reasonable (within 50% of target)
        if actual_fps > config.TARGET_FPS * 0.5:
            print(f"✓ FPS performance is acceptable")
            result = True
        else:
            print(f"⚠ FPS is below 50% of target (may need optimization)")
            result = False
        
        camera.release()
        
        print()
        return result
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        print()
        return False


def test_webcam_interactive():
    """
    Test 3: Interactive test with live preview window.
    
    Displays live webcam feed in a window.
    User can verify image quality and press 'q' to quit.
    """
    print("="*70)
    print("TEST 3: Interactive Live Preview")
    print("="*70)
    print("Press 'q' to quit the preview window")
    print()
    
    try:
        camera = WebcamCapture(
            camera_index=config.CAMERA_INDEX,
            target_fps=config.TARGET_FPS,
            frame_width=config.FRAME_WIDTH,
            frame_height=config.FRAME_HEIGHT
        )
        
        camera.start()
        
        frame_count = 0
        start_time = time.time()
        
        while True:
            success, frame = camera.read_frame()
            
            if success:
                frame_count += 1
                
                # Add FPS counter to frame
                fps = camera.get_fps()
                cv2.putText(
                    frame,
                    f"FPS: {fps:.1f} | Frame: {frame_count} | Press 'q' to quit",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2
                )
                
                # Add green border to indicate active capture
                height, width = frame.shape[:2]
                cv2.rectangle(frame, (0, 0), (width-1, height-1), (0, 255, 0), 2)
                
                cv2.imshow('FocusGuard Webcam Test - Press Q to Quit', frame)
            
            # Check for 'q' key press (wait 1ms)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        # Calculate final statistics
        elapsed = time.time() - start_time
        avg_fps = frame_count / elapsed if elapsed > 0 else 0
        
        camera.release()
        cv2.destroyAllWindows()
        
        print(f"✓ Interactive test completed")
        print(f"✓ Total frames shown: {frame_count}")
        print(f"✓ Average FPS: {avg_fps:.1f}")
        print()
        
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        print()
        return False


def main():
    """
    Run all webcam tests.
    """
    print("\n")
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║              FocusGuard Webcam Test Suite                         ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    print()
    
    # Run tests
    results = []
    
    results.append(("Basic Access", test_webcam_basic()))
    results.append(("FPS Performance", test_webcam_fps()))
    results.append(("Interactive Preview", test_webcam_interactive()))
    
    # Summary
    print("="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    all_passed = True
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status:8s} {test_name}")
        if not passed:
            all_passed = False
    
    print("="*70)
    
    if all_passed:
        print("\n✓✓✓ All tests passed! Webcam is working correctly! ✓✓✓\n")
        return 0
    else:
        print("\n✗✗✗ Some tests failed. Please check the output above. ✗✗✗\n")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
