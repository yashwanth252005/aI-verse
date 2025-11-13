"""
FocusGuard - Main Streamlit Application
========================================
AI-Powered Proctoring Assistant Dashboard

This is the main entry point for the FocusGuard application.
It provides a real-time web dashboard showing:
- Live webcam feed with AI overlays
- Real-time focus score
- Timeline graph of focus over time
- Event log with alerts
- Export functionality for reports

Usage:
    streamlit run app.py

Then open your browser to http://localhost:8501

Author: FocusGuard Team
Date: October 24, 2025
"""

import streamlit as st
import cv2
import numpy as np
from datetime import datetime
import time
from typing import Dict, Any

# Import our custom modules
from utils.video_capture import WebcamCapture
from utils.frame_processor import FrameProcessor
import config

# =============================================================================
# PAGE CONFIGURATION
# =============================================================================
# Must be the first Streamlit command - sets up the page layout and appearance
st.set_page_config(
    page_title="FocusGuard - AI Proctoring Assistant",
    page_icon="🎯",
    layout="wide",  # Use full width of browser
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/focusguard/focusguard',
        'Report a bug': 'https://github.com/focusguard/focusguard/issues',
        'About': 'FocusGuard - Privacy-first AI proctoring assistant'
    }
)


# =============================================================================
# SESSION STATE INITIALIZATION
# =============================================================================
# Streamlit reruns the entire script on each interaction, so we use session_state
# to persist variables across reruns (like a global scope)

def initialize_session_state():
    """
    Initialize all session state variables on first run.
    
    Session state persists across Streamlit reruns, allowing us to:
    - Keep the camera and processor alive between frames
    - Track monitoring session status
    - Store history for timeline graphs
    """
    # Camera and processing objects
    if 'camera' not in st.session_state:
        st.session_state.camera = None
    
    if 'processor' not in st.session_state:
        st.session_state.processor = None
    
    # Monitoring session state
    if 'monitoring_active' not in st.session_state:
        st.session_state.monitoring_active = False
    
    if 'session_start_time' not in st.session_state:
        st.session_state.session_start_time = None
    
    # History for timeline graph (stores last N score values)
    if 'score_history' not in st.session_state:
        st.session_state.score_history = []
    
    if 'time_history' not in st.session_state:
        st.session_state.time_history = []
    
    # Event log (stores alert messages)
    if 'event_log' not in st.session_state:
        st.session_state.event_log = []
    
    # Statistics
    if 'total_frames_processed' not in st.session_state:
        st.session_state.total_frames_processed = 0
    
    # Session logging and reports (Stage H)
    if 'session_log_path' not in st.session_state:
        st.session_state.session_log_path = None
    
    if 'pdf_report_path' not in st.session_state:
        st.session_state.pdf_report_path = None


# =============================================================================
# CAMERA CONTROL FUNCTIONS
# =============================================================================

def start_monitoring():
    """
    Start the monitoring session by initializing camera and processor.
    
    This function is called when the user clicks the "Start Monitoring" button.
    """
    try:
        # Initialize webcam capture
        st.session_state.camera = WebcamCapture(
            camera_index=config.CAMERA_INDEX,
            target_fps=config.TARGET_FPS,
            frame_width=config.FRAME_WIDTH,
            frame_height=config.FRAME_HEIGHT
        )
        st.session_state.camera.start()
        
        # Give camera time to warm up and capture first frame
        # This is CRITICAL for Streamlit - camera needs time to initialize
        time.sleep(1.0)
        
        # Verify camera is working before proceeding
        test_success, test_frame = st.session_state.camera.read_frame()
        if not test_success:
            raise RuntimeError("Camera started but cannot read frames. Please check camera connection.")
        
        # Initialize frame processor
        st.session_state.processor = FrameProcessor()
        
        # Update session state
        st.session_state.monitoring_active = True
        st.session_state.session_start_time = datetime.now()
        
        # Clear history for new session
        st.session_state.score_history = []
        st.session_state.time_history = []
        st.session_state.event_log = []
        st.session_state.total_frames_processed = 0
        
        # Add initial event to log
        st.session_state.event_log.append({
            'time': datetime.now().strftime('%H:%M:%S'),
            'type': 'INFO',
            'message': 'Monitoring session started'
        })
        
        st.success("✓ Monitoring started successfully! Camera is ready.")
        
    except Exception as e:
        st.error(f"✗ Failed to start monitoring: {e}")
        st.session_state.monitoring_active = False
        # Clean up if initialization failed
        if st.session_state.camera:
            st.session_state.camera.release()
            st.session_state.camera = None


def stop_monitoring():
    """
    Stop the monitoring session and release camera resources.
    
    This function is called when the user clicks the "Stop Monitoring" button.
    """
    try:
        # Calculate final statistics
        if st.session_state.score_history:
            # Calculate actual session duration from start to end time
            if st.session_state.session_start_time:
                session_duration_seconds = (datetime.now() - st.session_state.session_start_time).total_seconds()
            else:
                # Fallback: Use time_history if available
                session_duration_seconds = max(st.session_state.time_history) if st.session_state.time_history else 0
            
            # Count ONLY the 3 critical detection types (matching PDF event log filter)
            device_alerts = [e for e in st.session_state.event_log if any(keyword in e['message'].lower() for keyword in ['device', 'phone', 'book', 'laptop', 'keyboard', 'mouse', 'remote'])]
            voice_alerts = [e for e in st.session_state.event_log if any(keyword in e['message'].lower() for keyword in ['voice', 'audio', 'noise'])]
            person_alerts = [e for e in st.session_state.event_log if 'multiple people' in e['message'].lower() or ('people detected' in e['message'].lower() and 'faces' in e['message'].lower())]
            
            # Total alerts = sum of the 3 categories only (no other alert types counted)
            all_alerts = device_alerts + voice_alerts + person_alerts
            
            # Get gaze statistics
            gaze_stats = {}
            if st.session_state.processor and hasattr(st.session_state.processor, 'get_gaze_statistics'):
                gaze_stats = st.session_state.processor.get_gaze_statistics()
            
            final_stats = {
                'average_focus_score': sum(st.session_state.score_history) / len(st.session_state.score_history),
                'min_focus_score': min(st.session_state.score_history),
                'max_focus_score': max(st.session_state.score_history),
                'session_duration_seconds': session_duration_seconds,  # FIXED: Use actual elapsed time
                'total_alerts': len(all_alerts),
                'device_detections': len(device_alerts),
                'voice_detections': len(voice_alerts),
                'multiple_person_events': len(person_alerts),
                'focus_time_percentage': (len([s for s in st.session_state.score_history if s >= 70]) / len(st.session_state.score_history) * 100) if st.session_state.score_history else 0,
                # Add gaze statistics
                'gaze_forward_percentage': gaze_stats.get('forward_percentage', 0),
                'gaze_left_percentage': gaze_stats.get('left_percentage', 0),
                'gaze_right_percentage': gaze_stats.get('right_percentage', 0),
                'gaze_up_percentage': gaze_stats.get('up_percentage', 0),
                'gaze_down_percentage': gaze_stats.get('down_percentage', 0)
            }
        else:
            final_stats = {}
        
        # Save session log with statistics
        if st.session_state.processor and hasattr(st.session_state.processor, 'save_session_log'):
            log_path = st.session_state.processor.save_session_log(final_stats)
            if log_path:
                st.session_state.session_log_path = log_path
                print(f"✓ Session log saved: {log_path}")
        
        # Stop audio capture if running
        if st.session_state.processor and st.session_state.processor.audio_capture:
            st.session_state.processor.audio_capture.stop()
        
        # Release camera
        if st.session_state.camera is not None:
            st.session_state.camera.release()
            st.session_state.camera = None
        
        # Update session state
        st.session_state.monitoring_active = False
        
        # Add final event to log
        st.session_state.event_log.append({
            'time': datetime.now().strftime('%H:%M:%S'),
            'type': 'INFO',
            'message': 'Monitoring session stopped'
        })
        
        st.success("✓ Monitoring stopped successfully! Session log saved.")
        
    except Exception as e:
        st.error(f"✗ Failed to stop monitoring: {e}")


def generate_pdf_report():
    """
    Generate a PDF report of the monitoring session.
    
    Creates a professional PDF with:
    - Session statistics
    - Focus timeline chart
    - Event log
    """
    try:
        from utils.report_generator import ReportGenerator
        import plotly.graph_objects as go
        import os
        
        # Get session ID from processor
        session_id = st.session_state.processor.session_id if st.session_state.processor else "unknown"
        
        # Create report generator
        generator = ReportGenerator(
            session_id=session_id,
            output_dir="reports"
        )
        
        # Add session info
        generator.add_session_info({
            'user_id': 'Student',
            'exam_name': 'FocusGuard Monitoring Session',
            'start_time': st.session_state.event_log[0]['time'] if st.session_state.event_log else 'N/A',
            'end_time': st.session_state.event_log[-1]['time'] if st.session_state.event_log else 'N/A'
        })
        
        # Add statistics
        if st.session_state.score_history:
            # Calculate actual session duration
            if st.session_state.session_start_time:
                session_duration_seconds = (datetime.now() - st.session_state.session_start_time).total_seconds()
            else:
                session_duration_seconds = max(st.session_state.time_history) if st.session_state.time_history else 0
            
            # Count ONLY the 3 critical detection types (matching event log filter in PDF)
            device_alerts = [e for e in st.session_state.event_log if any(keyword in e['message'].lower() for keyword in ['device', 'phone', 'book', 'laptop', 'keyboard', 'mouse', 'remote'])]
            voice_alerts = [e for e in st.session_state.event_log if any(keyword in e['message'].lower() for keyword in ['voice', 'audio', 'noise'])]
            person_alerts = [e for e in st.session_state.event_log if 'multiple people' in e['message'].lower() or ('people detected' in e['message'].lower() and 'faces' in e['message'].lower())]
            
            # Total alerts = sum of the 3 categories only
            all_alerts = device_alerts + voice_alerts + person_alerts
            
            # Get gaze statistics
            gaze_stats = {}
            if st.session_state.processor and hasattr(st.session_state.processor, 'get_gaze_statistics'):
                gaze_stats = st.session_state.processor.get_gaze_statistics()
            
            stats = {
                'average_focus_score': sum(st.session_state.score_history) / len(st.session_state.score_history),
                'min_focus_score': min(st.session_state.score_history),
                'max_focus_score': max(st.session_state.score_history),
                'session_duration_seconds': session_duration_seconds,  # FIXED: Use actual elapsed time
                'total_alerts': len(all_alerts),
                'device_detections': len(device_alerts),
                'voice_detections': len(voice_alerts),
                'multiple_person_events': len(person_alerts),
                'focus_time_percentage': (len([s for s in st.session_state.score_history if s >= 70]) / len(st.session_state.score_history) * 100) if st.session_state.score_history else 0,
                # Add gaze statistics
                'gaze_forward_percentage': gaze_stats.get('forward_percentage', 0),
                'gaze_left_percentage': gaze_stats.get('left_percentage', 0),
                'gaze_right_percentage': gaze_stats.get('right_percentage', 0),
                'gaze_up_percentage': gaze_stats.get('up_percentage', 0),
                'gaze_down_percentage': gaze_stats.get('down_percentage', 0)
            }
            generator.add_statistics(stats)
        
        # Create and save timeline chart
        if st.session_state.score_history and st.session_state.time_history:
            fig = go.Figure()
            
            # Add score line
            fig.add_trace(go.Scatter(
                x=st.session_state.time_history,
                y=st.session_state.score_history,
                mode='lines',
                name='Focus Score',
                line=dict(color='#1f77b4', width=2)
            ))
            
            # Add color zones
            fig.add_hrect(y0=90, y1=100, fillcolor="rgba(0, 255, 0, 0.1)", line_width=0)
            fig.add_hrect(y0=70, y1=90, fillcolor="rgba(144, 238, 144, 0.1)", line_width=0)
            fig.add_hrect(y0=50, y1=70, fillcolor="rgba(255, 255, 0, 0.1)", line_width=0)
            fig.add_hrect(y0=30, y1=50, fillcolor="rgba(255, 165, 0, 0.1)", line_width=0)
            fig.add_hrect(y0=0, y1=30, fillcolor="rgba(255, 0, 0, 0.1)", line_width=0)
            
            fig.update_layout(
                title="Focus Score Timeline",
                xaxis_title="Time",
                yaxis_title="Focus Score",
                yaxis=dict(range=[0, 105]),
                showlegend=False,
                height=400,
                width=800
            )
            
            # Save chart as image
            chart_path = f"reports/timeline_{session_id}.png"
            os.makedirs("reports", exist_ok=True)
            fig.write_image(chart_path)
            
            generator.add_timeline_chart(chart_path)
        
        # Add events
        generator.add_events(st.session_state.event_log)
        
        # Generate PDF
        pdf_path = generator.generate()
        
        # Store in session state for download
        st.session_state.pdf_report_path = pdf_path
        
        return pdf_path
        
    except Exception as e:
        st.error(f"❌ Failed to generate PDF report: {e}")
        import traceback
        traceback.print_exc()
        return None


# =============================================================================
# MAIN APPLICATION
# =============================================================================

def main():
    """
    Main application function - runs on every Streamlit rerun.
    
    This function:
    1. Sets up the UI layout
    2. Handles button clicks
    3. Processes video frames
    4. Updates all dashboard components
    """
    # Initialize session state on first run
    initialize_session_state()
    
    # ==========================================================================
    # HEADER
    # ==========================================================================
    st.title("🎯 FocusGuard - AI Proctoring Assistant")
    st.markdown("""
    **Privacy-First Real-Time Focus Monitoring**  
    All processing runs locally on your device. No data is uploaded to the cloud.
    """)
    
    # ==========================================================================
    # SIDEBAR - Controls and Settings
    # ==========================================================================
    with st.sidebar:
        st.header("⚙️ Controls")
        
        # Session duration display
        if st.session_state.monitoring_active and st.session_state.session_start_time:
            duration = datetime.now() - st.session_state.session_start_time
            duration_str = str(duration).split('.')[0]  # Remove microseconds
            st.metric("Session Duration", duration_str)
        
        st.markdown("---")
        
        # Start/Stop buttons
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🎥 Start", type="primary", disabled=st.session_state.monitoring_active):
                start_monitoring()
                st.rerun()  # Refresh the page to show updated state
        
        with col2:
            if st.button("⏹️ Stop", type="secondary", disabled=not st.session_state.monitoring_active):
                stop_monitoring()
                st.rerun()
        
        st.markdown("---")
        
        # Session Report section (Stage H)
        st.header("📄 Session Report")
        
        # Show PDF generation button if session has stopped and has data
        if not st.session_state.monitoring_active and st.session_state.score_history:
            if st.button("📑 Generate PDF Report", type="primary", use_container_width=True):
                with st.spinner("Generating PDF report..."):
                    pdf_path = generate_pdf_report()
                    if pdf_path:
                        st.success("✓ PDF report generated successfully!")
                        st.session_state.pdf_report_path = pdf_path
            
            # Show download button if PDF exists
            if st.session_state.pdf_report_path:
                import os
                if os.path.exists(st.session_state.pdf_report_path):
                    with open(st.session_state.pdf_report_path, 'rb') as f:
                        pdf_data = f.read()
                    
                    st.download_button(
                        label="📥 Download PDF Report",
                        data=pdf_data,
                        file_name=os.path.basename(st.session_state.pdf_report_path),
                        mime="application/pdf",
                        use_container_width=True
                    )
            
            # Show session log info
            if st.session_state.session_log_path:
                st.info(f"🔒 Session log saved (encrypted): `{os.path.basename(st.session_state.session_log_path)}`")
        else:
            st.info("📝 Complete a monitoring session to generate a report")
        
        st.markdown("---")
        
        # Settings section
        st.header("📊 Settings")
        
        # Display current configuration
        st.markdown(f"""
        **Camera Settings:**
        - Camera Index: {config.CAMERA_INDEX}
        - Resolution: {config.FRAME_WIDTH}x{config.FRAME_HEIGHT}
        - Target FPS: {config.TARGET_FPS}
        
        **Detection Modules:**
        - Face Detection: ✓ Ready (Stage C)
        - Device Detection: ✓ Ready (Stage D)
        - Audio Detection: {'✓ Enabled' if config.ENABLE_AUDIO else '✗ Disabled'}
        
        **Privacy:**
        - Encryption: {'✓ Enabled' if config.ENABLE_ENCRYPTION else '✗ Disabled'}
        - Save Frames: {'✗ Disabled (Private)' if not config.SAVE_RAW_FRAMES else '✓ Enabled'}
        """)
        
        st.markdown("---")
        
        # Statistics
        if st.session_state.monitoring_active:
            st.header("📈 Statistics")
            st.metric("Frames Processed", st.session_state.total_frames_processed)
            
            if st.session_state.camera:
                fps = st.session_state.camera.get_fps()
                st.metric("Camera FPS", f"{fps:.1f}")
            
            # Show focus scorer statistics if available
            if st.session_state.processor and st.session_state.processor.focus_scorer:
                st.markdown("---")
                st.subheader("📊 Session Analysis")
                
                try:
                    stats = st.session_state.processor.focus_scorer.get_statistics()
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Avg Score", f"{stats['average_score']:.1f}")
                        st.metric("Min Score", f"{stats['min_score']:.0f}")
                    with col2:
                        st.metric("Max Score", f"{stats['max_score']:.0f}")
                        st.metric("Focus %", f"{stats['focus_time_percentage']:.1f}%")
                    
                    st.markdown(f"**Trend:** {stats['score_trend']}")
                    
                    # Show penalty breakdown
                    if stats['total_penalties'] > 0:
                        st.caption("**Total Penalties:**")
                        if stats['total_device_penalties'] > 0:
                            st.caption(f"• Devices: -{stats['total_device_penalties']}")
                        if stats['total_temporal_penalties'] > 0:
                            st.caption(f"• Looking away: -{stats['total_temporal_penalties']}")
                        if stats['total_person_penalties'] > 0:
                            st.caption(f"• Multiple people: -{stats['total_person_penalties']}")
                except Exception as e:
                    st.caption(f"Stats loading...")
            
            # Show audio detection statistics if available
            if st.session_state.processor and st.session_state.processor.audio_detector:
                st.markdown("---")
                st.subheader("🎤 Audio Monitoring")
                
                try:
                    audio_stats = st.session_state.processor.audio_detector.get_statistics()
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Voice Rate", f"{audio_stats['voice_detection_rate']:.1f}%")
                    with col2:
                        st.metric("Voice Alerts", audio_stats['voice_detections'])
                    
                    if audio_stats['seconds_since_last_voice'] is not None:
                        st.caption(f"Last voice: {audio_stats['seconds_since_last_voice']:.0f}s ago")
                    else:
                        st.caption("No voice detected yet")
                except Exception as e:
                    st.caption(f"Audio stats loading...")
    
    # ==========================================================================
    # MAIN CONTENT AREA
    # ==========================================================================
    
    if not st.session_state.monitoring_active:
        # Show welcome screen when not monitoring
        st.info("👆 Click **Start** in the sidebar to begin monitoring")
        
        st.markdown("---")
        
        # Show feature preview
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("### 👤 Face Detection")
            st.markdown("Real-time face tracking with 68-point landmarks")
            st.markdown("✓ Head pose estimation  \n✓ Gaze direction tracking")
        
        with col2:
            st.markdown("### 📱 Device Detection")
            st.markdown("Identifies unauthorized devices in frame")
            st.markdown("✓ Phones  \n✓ Books  \n✓ Laptops")
        
        with col3:
            st.markdown("### 🎤 Audio Analysis")
            st.markdown("Detects voice activity and anomalies")
            st.markdown("✓ Voice detection  \n✓ Noise alerts")
        
        st.markdown("---")
        
        # Privacy notice
        st.warning("""
        **🔒 Privacy Notice:**  
        FocusGuard processes all data locally on your device. No video or audio is uploaded to external servers.
        Logs are encrypted and stored only on your computer. You can delete all data at any time.
        """)
    
    else:
        # Monitoring is active - show live dashboard
        
        # Create two columns: video feed (left) and status panel (right)
        col_video, col_status = st.columns([2, 1])
        
        with col_video:
            st.subheader("📹 Live Video Feed")
            
            # Placeholder for video frame (will be updated continuously)
            video_placeholder = st.empty()
        
        with col_status:
            st.subheader("📊 Status Panel")
            
            # Placeholders for status information
            score_placeholder = st.empty()
            status_placeholder = st.empty()
        
        # =======================================================================
        # TIMELINE AND EVENT LOG (RENDER BEFORE VIDEO PROCESSING)
        # =======================================================================
        # This section must be rendered BEFORE st.rerun() to be visible
        st.markdown("---")
        
        # Quick statistics summary
        if len(st.session_state.score_history) > 0:
            col1, col2, col3, col4 = st.columns(4)
            
            import numpy as np
            current_score = st.session_state.score_history[-1]
            avg_score = np.mean(st.session_state.score_history)
            min_score = np.min(st.session_state.score_history)
            max_score = np.max(st.session_state.score_history)
            
            with col1:
                st.metric("Current Score", f"{current_score:.0f}/100", 
                         delta=f"{current_score - avg_score:+.0f} vs avg" if len(st.session_state.score_history) > 5 else None)
            with col2:
                st.metric("Average Score", f"{avg_score:.0f}/100")
            with col3:
                st.metric("Min Score", f"{min_score:.0f}/100")
            with col4:
                st.metric("Max Score", f"{max_score:.0f}/100")
            
            st.markdown("---")
        
        col_timeline, col_log = st.columns([2, 1])
        
        with col_timeline:
            st.subheader("📈 Focus Timeline")
            
            if len(st.session_state.score_history) > 1:
                # Create interactive Plotly timeline with color zones and markers
                import pandas as pd
                import plotly.graph_objects as go
                
                df = pd.DataFrame({
                    'Time': st.session_state.time_history,
                    'Score': st.session_state.score_history
                })
                
                # Create figure
                fig = go.Figure()
                
                # Add background color zones
                fig.add_hrect(y0=90, y1=100, fillcolor="green", opacity=0.1, line_width=0, annotation_text="Excellent", annotation_position="right")
                fig.add_hrect(y0=70, y1=90, fillcolor="lightgreen", opacity=0.1, line_width=0, annotation_text="Good", annotation_position="right")
                fig.add_hrect(y0=50, y1=70, fillcolor="yellow", opacity=0.1, line_width=0, annotation_text="Fair", annotation_position="right")
                fig.add_hrect(y0=30, y1=50, fillcolor="orange", opacity=0.1, line_width=0, annotation_text="Poor", annotation_position="right")
                fig.add_hrect(y0=0, y1=30, fillcolor="red", opacity=0.1, line_width=0, annotation_text="Critical", annotation_position="right")
                
                # Add focus score line with color based on value
                colors = []
                for score in df['Score']:
                    if score >= 90:
                        colors.append('green')
                    elif score >= 70:
                        colors.append('lightgreen')
                    elif score >= 50:
                        colors.append('gold')
                    elif score >= 30:
                        colors.append('orange')
                    else:
                        colors.append('red')
                
                # Main score line
                fig.add_trace(go.Scatter(
                    x=df['Time'],
                    y=df['Score'],
                    mode='lines+markers',
                    name='Focus Score',
                    line=dict(color='blue', width=3),
                    marker=dict(size=6, color=colors, line=dict(width=1, color='white')),
                    hovertemplate='<b>Time: %{x:.1f}s</b><br>Score: %{y:.0f}/100<extra></extra>'
                ))
                
                # Add event markers for device detections
                device_events = [e for e in st.session_state.event_log if e['type'] in ['WARNING', 'ALERT']]
                if device_events:
                    event_times = []
                    event_scores = []
                    event_labels = []
                    
                    for event in device_events[-20:]:  # Last 20 events
                        # Find closest time in timeline
                        event_time = float(event['time'].split(':')[0]) * 60 + float(event['time'].split(':')[1])
                        if event_time <= max(df['Time']):
                            # Find closest score
                            idx = (df['Time'] - event_time).abs().idxmin()
                            event_times.append(df.loc[idx, 'Time'])
                            event_scores.append(df.loc[idx, 'Score'])
                            event_labels.append(event['message'])
                    
                    if event_times:
                        fig.add_trace(go.Scatter(
                            x=event_times,
                            y=event_scores,
                            mode='markers',
                            name='Alerts',
                            marker=dict(size=12, color='red', symbol='x', line=dict(width=2, color='darkred')),
                            text=event_labels,
                            hovertemplate='<b>Alert!</b><br>%{text}<br>Time: %{x:.1f}s<extra></extra>'
                        ))
                
                # Update layout
                fig.update_layout(
                    xaxis_title="Time (seconds)",
                    yaxis_title="Focus Score",
                    yaxis=dict(range=[0, 105]),
                    hovermode='x unified',
                    height=400,
                    showlegend=True,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    margin=dict(l=50, r=50, t=30, b=50)
                )
                
                # Display interactive chart
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Timeline will appear after a few seconds of monitoring...")
        
        with col_log:
            st.subheader("📋 Event Log")
            
            if st.session_state.event_log:
                # Filter options
                col_filter1, col_filter2 = st.columns(2)
                with col_filter1:
                    show_all = st.checkbox("Show all events", value=False)
                with col_filter2:
                    event_limit = st.selectbox("Show last", [5, 10, 20, 50], index=1)
                
                # Filter events
                events_to_show = st.session_state.event_log[-event_limit:] if not show_all else st.session_state.event_log
                
                # Display events in a nice container
                st.markdown("---")
                for event in reversed(events_to_show):
                    # Choose emoji and color based on event type
                    if event['type'] == 'INFO':
                        emoji = "ℹ️"
                        color = "#3498db"  # Blue
                    elif event['type'] == 'WARNING':
                        emoji = "⚠️"
                        color = "#f39c12"  # Orange
                    elif event['type'] == 'ALERT':
                        emoji = "🚨"
                        color = "#e74c3c"  # Red
                    else:
                        emoji = "�"
                        color = "#95a5a6"  # Gray
                    
                    # Display with colored badge
                    st.markdown(
                        f'<div style="padding: 8px; margin: 4px 0; border-left: 3px solid {color}; background-color: rgba(0,0,0,0.05);">'
                        f'{emoji} <b>{event["time"]}</b> — {event["message"]}'
                        f'</div>',
                        unsafe_allow_html=True
                    )
            else:
                st.info("No events yet...")
        
        # =======================================================================
        # VIDEO PROCESSING LOOP (AT THE END, AFTER ALL UI IS RENDERED)
        # =======================================================================
        # This section processes frames continuously while monitoring is active
        
        if st.session_state.camera and st.session_state.processor:
            # Check if camera is still active
            if not st.session_state.camera.is_running:
                st.error("⚠️ Camera thread stopped unexpectedly. Click Stop and then Start again.")
                st.info("💡 Tip: Make sure no other application is using the camera.")
            else:
                # Continuous processing loop - process more frames per cycle for maximum smoothness!
                frame_count = 0
                max_frames_per_cycle = 60  # Process 60 frames (~2 seconds at 30 FPS) per cycle for smoother UI
                
                while frame_count < max_frames_per_cycle and st.session_state.monitoring_active:
                    # Read frame from camera
                    success, frame = st.session_state.camera.read_frame()
                    
                    if success and frame is not None:
                        # Process the frame through AI pipeline
                        result = st.session_state.processor.process_frame(frame)
                        
                        # Add alerts to event log with INTELLIGENT TIME-BASED DEDUPLICATION
                        # Only count as new event if 3+ seconds passed since last similar event
                        if result['alerts']:
                            current_time = time.time()
                            
                            # Initialize last alert times if not exists
                            if not hasattr(st.session_state, 'last_alert_times'):
                                st.session_state.last_alert_times = {}
                            
                            for alert in result['alerts']:
                                # Determine alert type based on content
                                if '[AUDIO]' in alert or 'voice' in alert.lower() or 'noise' in alert.lower():
                                    alert_type = 'ALERT'
                                    alert_category = 'audio'
                                elif 'device' in alert.lower() or 'phone' in alert.lower() or 'laptop' in alert.lower():
                                    alert_type = 'ALERT'
                                    alert_category = 'device'
                                elif 'multiple people' in alert.lower() or 'person' in alert.lower():
                                    alert_type = 'CRITICAL'
                                    alert_category = 'person'
                                else:
                                    alert_type = 'WARNING'
                                    alert_category = 'other'
                                
                                # Check if enough time passed since last alert of this category
                                last_time = st.session_state.last_alert_times.get(alert_category, 0)
                                time_since_last = current_time - last_time
                                
                                # Only add if 3+ seconds passed (prevents 40-50 duplicate detections per second!)
                                if time_since_last >= 3.0:
                                    st.session_state.event_log.append({
                                        'time': datetime.now().strftime('%H:%M:%S'),
                                        'type': alert_type,
                                        'message': alert
                                    })
                                    st.session_state.last_alert_times[alert_category] = current_time
                        
                        # Update statistics
                        st.session_state.total_frames_processed += 1
                        
                        # Update history for timeline (keep last 1000 points)
                        current_time = time.time()
                        if st.session_state.session_start_time:
                            elapsed = current_time - st.session_state.session_start_time.timestamp()
                            st.session_state.time_history.append(elapsed)
                            st.session_state.score_history.append(result['focus_score'])
                            
                            # Trim history if too long
                            if len(st.session_state.score_history) > config.TIMELINE_HISTORY_POINTS:
                                st.session_state.score_history = st.session_state.score_history[-config.TIMELINE_HISTORY_POINTS:]
                                st.session_state.time_history = st.session_state.time_history[-config.TIMELINE_HISTORY_POINTS:]
                        
                        # Convert BGR (OpenCV) to RGB (Streamlit)
                        annotated_frame_rgb = cv2.cvtColor(result['annotated_frame'], cv2.COLOR_BGR2RGB)
                        
                        # Display the video frame - stretch to fill container width
                        video_placeholder.image(
                            annotated_frame_rgb,
                            channels="RGB",
                            caption=f"Frame {result['frame_number']} | Processing: {result['processing_time_ms']:.1f}ms"
                        )
                        
                        # Update status panels only every 5th frame (more frequent UI updates for smoother experience)
                        if frame_count % 5 == 0:
                            # Update status panel with enhanced focus score
                            with score_placeholder.container():
                                # Display focus score as a large metric
                                score_color = result['focus_color']
                                score_emoji = "🟢" if score_color == "green" else "🟡" if score_color == "yellow" else "🔴"
                                
                                st.metric(
                                    label="Focus Score",
                                    value=f"{result['focus_score']:.0f}/100 {score_emoji}",
                                    delta=None
                                )
                                
                                # Show detailed breakdown if Stage E is active
                                if result.get('focus_score_data'):
                                    score_data = result['focus_score_data']
                                    
                                    # Show penalty breakdown
                                    st.caption("**Score Breakdown:**")
                                    st.caption(f"• Base: {score_data['base_score']:.0f}")
                                    
                                    if score_data['device_penalty_applied'] > 0:
                                        st.caption(f"• Device penalty: -{score_data['device_penalty_applied']}")
                                    if score_data['temporal_penalty_applied'] > 0:
                                        st.caption(f"• Looking away: -{score_data['temporal_penalty_applied']}")
                                    if score_data['multiple_person_penalty_applied'] > 0:
                                        st.caption(f"• Multiple people: -{score_data['multiple_person_penalty_applied']}")
                            
                            with status_placeholder.container():
                                # Display current status
                                st.markdown(f"**Status:** {result['focus_label']}")
                                
                                # Show person count with warning if multiple people
                                person_count = result.get('person_count', 1)
                                if person_count > 1:
                                    st.error(f"👥 **{person_count} People Detected!**", icon="🚨")
                                elif person_count == 1:
                                    st.markdown(f"**People:** 1 ✓")
                                else:
                                    st.markdown(f"**People:** 0")
                                
                                st.markdown(f"**Alerts:** {len(result['alerts'])}")
                                
                                # Show active warnings
                                if result['alerts']:
                                    for alert in result['alerts'][-3:]:  # Show last 3 alerts
                                        st.warning(alert, icon="⚠️")
                        
                        # No artificial delay - let it run at maximum speed!
                        # Your RTX 2050 + i5 13th Gen can easily handle 40-50 FPS
                        frame_count += 1
                    
                    elif st.session_state.total_frames_processed == 0:
                        # First frame attempt failed - camera still initializing
                        video_placeholder.info("🔄 Camera initializing... Please wait a moment.")
                        time.sleep(0.5)
                        break
                    
                    else:
                        # Subsequent frame read failed
                        st.error("⚠️ Failed to read frame from camera.")
                        break
                
                # After processing batch, rerun immediately for next batch
                if st.session_state.monitoring_active:
                    st.rerun()  # No delay - rerun immediately for continuous flow
        
        else:
            # No camera or processor - should not happen if monitoring is active
            if st.session_state.monitoring_active:
                st.warning("**Possible causes:**\n"
                          "- Camera disconnected\n"
                          "- Another app is using the camera\n"
                          "- Camera permissions denied\n\n"
                          "**Solution:** Click Stop, close other camera apps, then Start again.")
                
                # Show last good frame if available
                if st.session_state.total_frames_processed > 0:
                    st.info(f"Last successful frame: #{st.session_state.total_frames_processed}")


# =============================================================================
# ENTRY POINT
# =============================================================================
if __name__ == "__main__":
    # Run the main application
    main()
