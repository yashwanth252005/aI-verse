"""
PDF Report Generator Module
============================
Generates professional PDF reports for proctoring sessions.

Creates comprehensive reports with:
- Session summary and statistics
- Focus score timeline with visual chart
- Event log with all detections and alerts
- Professional formatting and branding

Author: FocusGuard Team
Date: October 24, 2025
"""

import os
from datetime import datetime
from typing import Dict, List, Optional
import io

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


class ReportGenerator:
    """
    Generates PDF proctoring session reports.
    
    Creates professional PDF documents with session data including:
    - Header with session details
    - Statistics summary (avg/min/max scores, duration)
    - Focus timeline chart (if image provided)
    - Event log table with all detections
    - Footer with timestamp and page numbers
    
    Example:
        generator = ReportGenerator(
            session_id="session_001",
            output_dir="reports"
        )
        
        generator.add_statistics({...})
        generator.add_timeline_chart("timeline.png")
        generator.add_events([...])
        
        pdf_path = generator.generate()
    """
    
    def __init__(
        self,
        session_id: str,
        output_dir: str = "reports",
        page_size=letter
    ):
        """
        Initialize report generator.
        
        Args:
            session_id: Session identifier
            output_dir: Directory to save reports
            page_size: PDF page size (letter or A4)
        """
        self.session_id = session_id
        self.output_dir = output_dir
        self.page_size = page_size
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Set up report file path
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.report_path = os.path.join(
            output_dir,
            f"report_{timestamp}_{session_id}.pdf"
        )
        
        # Initialize data containers
        self.statistics = {}
        self.events = []
        self.timeline_chart_path = None
        self.session_info = {}
        
        # Set up styles
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        
        print(f"✓ ReportGenerator initialized")
        print(f"  → Report will be saved to: {self.report_path}")
    
    def _setup_custom_styles(self):
        """Set up custom paragraph styles."""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            textColor=colors.HexColor('#1f4788'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#2c5aa0'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        ))
        
        # Subsection header style
        self.styles.add(ParagraphStyle(
            name='SubsectionHeader',
            parent=self.styles['Heading2'],
            fontSize=13,
            textColor=colors.HexColor('#34495e'),
            spaceAfter=8,
            spaceBefore=8,
            fontName='Helvetica-Bold'
        ))
        
        # Info text style
        self.styles.add(ParagraphStyle(
            name='InfoText',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#34495e'),
            spaceAfter=6
        ))
        
        # Footer style
        self.styles.add(ParagraphStyle(
            name='Footer',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.gray,
            alignment=TA_CENTER
        ))
    
    def add_session_info(self, info: Dict):
        """
        Add session information.
        
        Args:
            info: Session info dictionary (user_id, exam_name, start_time, etc.)
        """
        self.session_info = info
    
    def add_statistics(self, stats: Dict):
        """
        Add session statistics.
        
        Args:
            stats: Statistics dictionary with scores, counts, duration
        """
        self.statistics = stats
    
    def add_events(self, events: List[Dict]):
        """
        Add event log.
        
        Args:
            events: List of event dictionaries
        """
        self.events = events
    
    def add_timeline_chart(self, chart_image_path: str):
        """
        Add timeline chart image.
        
        Args:
            chart_image_path: Path to timeline chart image file
        """
        if os.path.exists(chart_image_path):
            self.timeline_chart_path = chart_image_path
            print(f"  ✓ Timeline chart added: {chart_image_path}")
        else:
            print(f"  ⚠️  Timeline chart not found: {chart_image_path}")
    
    def _build_header(self) -> List:
        """Build report header section."""
        elements = []
        
        # Title
        elements.append(Paragraph(
            "FocusGuard AI Proctoring Report",
            self.styles['CustomTitle']
        ))
        
        elements.append(Spacer(1, 0.2 * inch))
        
        # Session info table
        session_data = [
            ['Session ID:', self.session_id],
            ['Generated:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
        ]
        
        if self.session_info:
            if 'user_id' in self.session_info:
                session_data.append(['User ID:', self.session_info['user_id']])
            if 'exam_name' in self.session_info:
                session_data.append(['Exam:', self.session_info['exam_name']])
            if 'start_time' in self.session_info:
                session_data.append(['Start Time:', self.session_info['start_time']])
            if 'end_time' in self.session_info:
                session_data.append(['End Time:', self.session_info['end_time']])
        
        session_table = Table(session_data, colWidths=[2*inch, 4*inch])
        session_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#2c5aa0')),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(session_table)
        elements.append(Spacer(1, 0.3 * inch))
        
        return elements
    
    def _build_statistics_section(self) -> List:
        """Build statistics summary section."""
        elements = []
        
        elements.append(Paragraph(
            "Session Statistics",
            self.styles['SectionHeader']
        ))
        
        if not self.statistics:
            elements.append(Paragraph(
                "No statistics available.",
                self.styles['InfoText']
            ))
            return elements
        
        # Statistics table
        stats_data = []
        
        # Focus scores
        if 'average_focus_score' in self.statistics:
            stats_data.append([
                'Average Focus Score:',
                f"{self.statistics['average_focus_score']:.1f} / 100"
            ])
        
        if 'min_focus_score' in self.statistics:
            stats_data.append([
                'Minimum Focus Score:',
                f"{self.statistics['min_focus_score']:.1f} / 100"
            ])
        
        if 'max_focus_score' in self.statistics:
            stats_data.append([
                'Maximum Focus Score:',
                f"{self.statistics['max_focus_score']:.1f} / 100"
            ])
        
        # Session duration
        if 'session_duration_seconds' in self.statistics:
            duration = self.statistics['session_duration_seconds']
            minutes = int(duration // 60)
            seconds = int(duration % 60)
            stats_data.append([
                'Session Duration:',
                f"{minutes}m {seconds}s"
            ])
        
        # Alert counts
        if 'total_alerts' in self.statistics:
            stats_data.append([
                'Total Alerts:',
                str(self.statistics['total_alerts'])
            ])
        
        if 'device_detections' in self.statistics:
            stats_data.append([
                'Device Detections:',
                str(self.statistics['device_detections'])
            ])
        
        if 'voice_detections' in self.statistics:
            stats_data.append([
                'Voice Detections:',
                str(self.statistics['voice_detections'])
            ])
        
        if 'multiple_person_events' in self.statistics:
            stats_data.append([
                'Multiple Person Events:',
                str(self.statistics['multiple_person_events'])
            ])
        
        # Focus percentage
        if 'focus_time_percentage' in self.statistics:
            stats_data.append([
                'Time Focused:',
                f"{self.statistics['focus_time_percentage']:.1f}%"
            ])
        
        # Gaze Analysis Section
        if any(k.startswith('gaze_') for k in self.statistics.keys()):
            # Add a separator
            stats_data.append(['', ''])
            stats_data.append([
                'Gaze Analysis:',
                ''
            ])
            
            if 'gaze_forward_percentage' in self.statistics:
                stats_data.append([
                    '  • Looking Forward:',
                    f"{self.statistics['gaze_forward_percentage']:.1f}%"
                ])
            
            if 'gaze_left_percentage' in self.statistics:
                stats_data.append([
                    '  • Looking Left:',
                    f"{self.statistics['gaze_left_percentage']:.1f}%"
                ])
            
            if 'gaze_right_percentage' in self.statistics:
                stats_data.append([
                    '  • Looking Right:',
                    f"{self.statistics['gaze_right_percentage']:.1f}%"
                ])
            
            if 'gaze_up_percentage' in self.statistics:
                stats_data.append([
                    '  • Looking Up:',
                    f"{self.statistics['gaze_up_percentage']:.1f}%"
                ])
            
            if 'gaze_down_percentage' in self.statistics:
                stats_data.append([
                    '  • Looking Down:',
                    f"{self.statistics['gaze_down_percentage']:.1f}%"
                ])
        
        if stats_data:
            stats_table = Table(stats_data, colWidths=[2.5*inch, 3.5*inch])
            stats_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#2c5aa0')),
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
            ]))
            
            elements.append(stats_table)
        
        elements.append(Spacer(1, 0.3 * inch))
        
        return elements
    
    def _build_timeline_section(self) -> List:
        """Build timeline chart section."""
        elements = []
        
        elements.append(Paragraph(
            "Focus Timeline",
            self.styles['SectionHeader']
        ))
        
        if self.timeline_chart_path and os.path.exists(self.timeline_chart_path):
            # Add chart image
            img = Image(self.timeline_chart_path, width=6.5*inch, height=3.5*inch)
            elements.append(img)
        else:
            elements.append(Paragraph(
                "Timeline chart not available.",
                self.styles['InfoText']
            ))
        
        elements.append(Spacer(1, 0.3 * inch))
        
        return elements
    
    def _build_events_section(self) -> List:
        """Build event log section."""
        elements = []
        
        elements.append(Paragraph(
            "Event Log",
            self.styles['SectionHeader']
        ))
        
        if not self.events:
            elements.append(Paragraph(
                "No events recorded.",
                self.styles['InfoText']
            ))
            return elements
        
        # ULTRA-SMART FILTERING WITH 1-MINUTE DEDUPLICATION:
        # Step 1: Only show 3 CRITICAL detection types (device/voice/person)
        # Step 2: Within same minute, only show FIRST occurrence of same alert type
        # This prevents "Device detected" appearing 20 times if phone shown for 1 minute!
        
        critical_events = []
        last_alert_minute = {}  # Track last minute each alert type was logged
        
        for e in self.events:
            msg_lower = e.get('message', '').lower()
            
            # Determine alert category
            alert_category = None
            if any(kw in msg_lower for kw in ['device', 'phone', 'laptop', 'book', 'keyboard', 'mouse', 'remote']):
                alert_category = 'device'
            elif any(kw in msg_lower for kw in ['voice', 'audio', 'noise']):
                alert_category = 'voice'
            elif 'multiple people' in msg_lower or 'people detected' in msg_lower:
                alert_category = 'person'
            
            # Skip if not a critical event
            if not alert_category:
                continue
            
            # Extract timestamp and determine minute bucket
            timestamp = e.get('timestamp', e.get('time', '00:00:00'))
            try:
                # Parse HH:MM:SS to get minute bucket
                if ':' in timestamp:
                    parts = timestamp.split(':')
                    hours = int(parts[0]) if len(parts) > 0 else 0
                    minutes = int(parts[1]) if len(parts) > 1 else 0
                    minute_bucket = hours * 60 + minutes  # Convert to total minutes
                else:
                    minute_bucket = 0
            except:
                minute_bucket = 0
            
            # Check if same alert type happened in same minute
            last_minute = last_alert_minute.get(alert_category, -999)
            
            if minute_bucket != last_minute:
                # Different minute OR first occurrence - add to log
                critical_events.append(e)
                last_alert_minute[alert_category] = minute_bucket
            # else: Same alert in same minute - SKIP (prevents spam!)
        
        # If no critical detections, show clean summary
        if not critical_events:
            elements.append(Paragraph(
                f"<b>✓ No integrity violations detected</b><br/>"
                f"No unauthorized devices, voice activity, or multiple people detected during session.<br/>"
                f"<i>Note: Only device, voice, and multiple-person detections are shown in event log.</i>",
                self.styles['InfoText']
            ))
            return elements
        
        # Show summary at top
        elements.append(Paragraph(
            f"<b>Detected {len(critical_events)} integrity events</b> "
            f"(Device/Voice/Multiple-Person detections, deduplicated within same minute)",
            self.styles['InfoText']
        ))
        elements.append(Spacer(1, 0.1 * inch))
        
        # Event table header
        event_data = [['Time', 'Type', 'Message']]
        
        # Add deduplicated critical events (already filtered above)
        # No need for additional limiting - deduplication handles it!
        display_events = critical_events  # Use all deduplicated events (won't be too many!)
        
        for event in display_events:
            # Try both 'timestamp' (from logger) and 'time' (from UI event log)
            timestamp = event.get('timestamp', event.get('time', 'N/A'))
            event_type = event.get('type', 'N/A')
            message = event.get('message', '')
            
            # Format timestamp - handle both ISO format and HH:MM:SS format
            if timestamp != 'N/A':
                try:
                    # Try parsing as ISO format first
                    dt = datetime.fromisoformat(timestamp)
                    timestamp = dt.strftime('%H:%M:%S')
                except:
                    # If that fails, assume it's already in HH:MM:SS format
                    # Just pass it through as-is
                    pass
            
            # Truncate long messages
            if len(message) > 80:
                message = message[:77] + '...'
            
            event_data.append([timestamp, event_type, message])
        
        # Create table
        event_table = Table(
            event_data,
            colWidths=[1*inch, 1.3*inch, 4.2*inch],
            repeatRows=1
        )
        
        # Style table
        table_style = [
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5aa0')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            
            # Data rows
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 0), (1, -1), 'CENTER'),
            ('ALIGN', (2, 0), (2, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ]
        
        event_table.setStyle(TableStyle(table_style))
        
        elements.append(event_table)
        
        # Add note if events were truncated
        if len(self.events) > 50:
            elements.append(Spacer(1, 0.1 * inch))
            elements.append(Paragraph(
                f"<i>Note: Showing last 50 of {len(self.events)} total events.</i>",
                self.styles['InfoText']
            ))
        
        return elements
    
    def _build_footer(self, canvas, doc):
        """Build page footer with page numbers."""
        canvas.saveState()
        
        # Footer text
        footer_text = f"FocusGuard AI Proctoring System | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.gray)
        canvas.drawString(inch, 0.5 * inch, footer_text)
        
        # Page number
        page_num = canvas.getPageNumber()
        canvas.drawRightString(
            self.page_size[0] - inch,
            0.5 * inch,
            f"Page {page_num}"
        )
        
        canvas.restoreState()
    
    def generate(self) -> str:
        """
        Generate the PDF report.
        
        Returns:
            Path to generated PDF file
        """
        print(f"\n📄 Generating PDF report...")
        
        # Create PDF document
        doc = SimpleDocTemplate(
            self.report_path,
            pagesize=self.page_size,
            rightMargin=inch,
            leftMargin=inch,
            topMargin=inch,
            bottomMargin=inch
        )
        
        # Build story (content)
        story = []
        
        # Add sections
        story.extend(self._build_header())
        story.extend(self._build_statistics_section())
        story.extend(self._build_timeline_section())
        story.extend(self._build_events_section())
        
        # Build PDF
        doc.build(story, onFirstPage=self._build_footer, onLaterPages=self._build_footer)
        
        print(f"✓ PDF report generated: {self.report_path}")
        print(f"  Size: {os.path.getsize(self.report_path) / 1024:.1f} KB")
        
        return self.report_path
    
    def generate_report(self, session_data, output_path: str):
        """
        Generate PDF report from SessionData (API integration method).
        
        Args:
            session_data: SessionData object from api.session_manager
            output_path: Full path where PDF should be saved
            
        Returns:
            str: Path to generated PDF file
        """
        from datetime import timedelta
        
        # Update report path
        self.report_path = output_path
        
        # Extract session info
        self.session_info = {
            'session_id': session_data.session_id,
            'student_id': session_data.student_id,
            'exam_id': session_data.exam_id,
            'institution_id': session_data.institution_id,
            'start_time': session_data.created_at.strftime("%Y-%m-%d %H:%M:%S") if session_data.created_at else "N/A",
            'end_time': session_data.ended_at.strftime("%Y-%m-%d %H:%M:%S") if session_data.ended_at else "In Progress"
        }
        
        # Calculate duration
        if session_data.ended_at and session_data.created_at:
            duration = session_data.ended_at - session_data.created_at
            duration_str = str(timedelta(seconds=int(duration.total_seconds())))
        else:
            duration_str = "N/A"
        
        # Calculate statistics
        avg_score = sum(session_data.score_history) / len(session_data.score_history) if session_data.score_history else 0
        min_score = min(session_data.score_history, default=0)
        max_score = max(session_data.score_history, default=100)
        
        self.statistics = {
            'frames_analyzed': session_data.frames_processed,
            'average_focus_score': round(avg_score, 1),
            'min_focus_score': round(min_score, 1),
            'max_focus_score': round(max_score, 1),
            'duration': duration_str,
            'device_detections': session_data.device_detections,
            'voice_detections': session_data.voice_detections,
            'multiple_person_events': session_data.multiple_person_events,
            'total_alerts': session_data.device_detections + session_data.voice_detections + session_data.multiple_person_events
        }
        
        # Build events list from event_log
        self.events = []
        
        # Add start event
        self.events.append({
            'timestamp': session_data.created_at.strftime("%H:%M:%S") if session_data.created_at else "00:00:00",
            'type': 'INFO',
            'message': f'Session started - Student: {session_data.student_id}'
        })
        
        # Add events from event_log
        for event in session_data.event_log:
            event_type = 'INFO'
            if 'device' in event.get('message', '').lower():
                event_type = 'ALERT'
            elif 'voice' in event.get('message', '').lower() or 'audio' in event.get('message', '').lower():
                event_type = 'WARNING'
            elif 'multiple' in event.get('message', '').lower() or 'person' in event.get('message', '').lower():
                event_type = 'CRITICAL'
            
            self.events.append({
                'timestamp': event.get('timestamp', 'N/A'),
                'type': event_type,
                'message': event.get('message', 'Unknown event')
            })
        
        # Add summary events based on detection counts
        if session_data.device_detections > 0:
            self.events.append({
                'timestamp': 'Summary',
                'type': 'ALERT',
                'message': f'Total device detections: {session_data.device_detections}'
            })
        
        if session_data.voice_detections > 0:
            self.events.append({
                'timestamp': 'Summary',
                'type': 'WARNING',
                'message': f'Total voice/audio anomalies: {session_data.voice_detections}'
            })
        
        if session_data.multiple_person_events > 0:
            self.events.append({
                'timestamp': 'Summary',
                'type': 'CRITICAL',
                'message': f'Total multiple person events: {session_data.multiple_person_events}'
            })
        
        # Add end event
        if session_data.ended_at:
            self.events.append({
                'timestamp': session_data.ended_at.strftime("%H:%M:%S"),
                'type': 'INFO',
                'message': 'Session ended'
            })
        
        # If no specific events, add a placeholder
        if len(self.events) <= 2:  # Only start and possibly end
            self.events.insert(1, {
                'timestamp': 'N/A',
                'type': 'INFO',
                'message': 'No significant events detected during session'
            })
        
        # Generate the PDF
        return self.generate()


# =============================================================================
# EXAMPLE USAGE
# =============================================================================
if __name__ == "__main__":
    print("=== ReportGenerator Test ===\n")
    
    # Create generator
    generator = ReportGenerator(
        session_id="test_session_001",
        output_dir="reports"
    )
    
    # Add session info
    generator.add_session_info({
        'user_id': 'student_12345',
        'exam_name': 'Final Exam - AI Proctoring',
        'start_time': '2025-01-24 14:30:00',
        'end_time': '2025-01-24 15:45:00'
    })
    
    # Add statistics
    generator.add_statistics({
        'average_focus_score': 87.5,
        'min_focus_score': 45.0,
        'max_focus_score': 98.5,
        'session_duration_seconds': 4500,
        'total_alerts': 12,
        'device_detections': 3,
        'voice_detections': 5,
        'multiple_person_events': 1,
        'focus_time_percentage': 85.3
    })
    
    # Add events
    events = [
        {'timestamp': '2025-01-24T14:30:05', 'type': 'INFO', 'message': 'Session started'},
        {'timestamp': '2025-01-24T14:35:12', 'type': 'ALERT', 'message': 'Device detected: cell_phone (confidence: 0.87)'},
        {'timestamp': '2025-01-24T14:42:30', 'type': 'WARNING', 'message': 'Voice detected (score: 75/100)'},
        {'timestamp': '2025-01-24T14:58:45', 'type': 'CRITICAL', 'message': 'Multiple people detected (2 faces)'},
        {'timestamp': '2025-01-24T15:15:20', 'type': 'INFO', 'message': 'Focus regained - looking at screen'},
        {'timestamp': '2025-01-24T15:45:00', 'type': 'INFO', 'message': 'Session ended'}
    ]
    generator.add_events(events)
    
    # Generate report
    pdf_path = generator.generate()
    
    print(f"\n✓ Test complete!")
    print(f"  Report saved to: {pdf_path}")
