"""
=============================================================================
EMAIL SERVICE MODULE
=============================================================================
Handles automated email report generation and scheduling
=============================================================================
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
import json
import os


class EmailService:
    """Email service for sending automated reports"""
    
    def __init__(self):
        self.load_email_config()
    
    def load_email_config(self) -> Dict[str, Any]:
        """Load email configuration from .env file"""
        env_file = Path(__file__).parent / ".env"
        config = {
            "enabled": False,
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 465,
            "sender_email": "",
            "sender_password": "",
            "recipient_emails": []
        }
        
        if env_file.exists():
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        if key == 'EMAIL_ENABLED':
                            config['enabled'] = value.lower() == 'true'
                        elif key == 'EMAIL_SMTP_SERVER':
                            config['smtp_server'] = value
                        elif key == 'EMAIL_SMTP_PORT':
                            config['smtp_port'] = int(value)
                        elif key == 'EMAIL_SENDER_EMAIL':
                            config['sender_email'] = value
                        elif key == 'EMAIL_SENDER_PASSWORD':
                            config['sender_password'] = value
                        elif key == 'EMAIL_RECIPIENT_EMAIL':
                            # Support both comma and semicolon separated emails
                            value = value.replace(',', ';')
                            config['recipient_emails'] = [e.strip() for e in value.split(';') if e.strip()]
        
        self.config = config
        return config
    
    def send_report_email(self, report_data: Dict[str, Any], 
                         recipients: Optional[List[str]] = None) -> Dict[str, Any]:
        """Send report via email to each recipient individually"""
        
        if not self.config['enabled']:
            return {
                "status": "disabled",
                "message": "Email service is disabled. Enable in .env file"
            }
        
        if not self.config['sender_email'] or not self.config['sender_password']:
            return {
                "status": "error",
                "message": "Email credentials not configured in .env file"
            }
        
        recipients = recipients or self.config['recipient_emails']
        if not recipients:
            return {
                "status": "error",
                "message": "No recipient emails configured"
            }
        
        # Generate HTML content once
        html_content = self._generate_html_report(report_data)
        subject = self._generate_subject(report_data)
        
        try:
            context = ssl.create_default_context()
            
            if self.config['smtp_port'] == 465:
                with smtplib.SMTP_SSL(self.config['smtp_server'], 
                                     self.config['smtp_port'], 
                                     context=context) as server:
                    server.login(self.config['sender_email'], self.config['sender_password'])
                    
                    # Send individual email to each recipient
                    for recipient in recipients:
                        message = MIMEMultipart("alternative")
                        message["Subject"] = subject
                        message["From"] = self.config['sender_email']
                        message["To"] = recipient.strip()
                        message.attach(MIMEText(html_content, "html"))
                        server.sendmail(self.config['sender_email'], [recipient.strip()], message.as_string())
                        
            else:
                with smtplib.SMTP(self.config['smtp_server'], 
                                self.config['smtp_port']) as server:
                    server.starttls(context=context)
                    server.login(self.config['sender_email'], self.config['sender_password'])
                    
                    # Send individual email to each recipient
                    for recipient in recipients:
                        message = MIMEMultipart("alternative")
                        message["Subject"] = subject
                        message["From"] = self.config['sender_email']
                        message["To"] = recipient.strip()
                        message.attach(MIMEText(html_content, "html"))
                        server.sendmail(self.config['sender_email'], [recipient.strip()], message.as_string())
            
            return {
                "status": "success",
                "message": f"Report sent to {len(recipients)} recipient(s)",
                "recipients": [r.strip() for r in recipients]
            }
        
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to send email: {str(e)}"
            }
    
    def _generate_subject(self, report_data: Dict[str, Any]) -> str:
        """Generate email subject line"""
        report_type = report_data.get('report_type', 'Report')
        date = report_data.get('date') or report_data.get('period', datetime.now().strftime('%Y-%m-%d'))
        return f"Security System {report_type} - {date}"
    
    def _generate_html_report(self, report_data: Dict[str, Any]) -> str:
        """Generate HTML email template"""
        
        report_type = report_data.get('report_type', 'Report')
        period = report_data.get('date') or report_data.get('period', 'N/A')
        
        # Extract summary data
        summary = report_data.get('summary', {})
        kpis = report_data.get('kpis', {})
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #ffffff;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }}
        .header {{
            text-align: center;
            margin-bottom: 40px;
            padding-bottom: 20px;
            border-bottom: 2px solid rgba(0, 212, 255, 0.3);
        }}
        .header h1 {{
            background: linear-gradient(135deg, #00d4ff 0%, #7c3aed 50%, #ec4899 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 2.5rem;
            margin: 0 0 10px 0;
        }}
        .header p {{
            color: #94a3b8;
            font-size: 1.1rem;
            margin: 5px 0;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        .metric-card {{
            background: rgba(255, 255, 255, 0.08);
            border-radius: 15px;
            padding: 25px;
            text-align: center;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}
        .metric-value {{
            font-size: 2.5rem;
            font-weight: bold;
            color: #00d4ff;
            margin: 10px 0;
        }}
        .metric-label {{
            color: #94a3b8;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .section {{
            margin: 30px 0;
            padding: 25px;
            background: rgba(255, 255, 255, 0.03);
            border-radius: 15px;
            border-left: 4px solid #00d4ff;
        }}
        .section h2 {{
            color: #00d4ff;
            font-size: 1.5rem;
            margin-top: 0;
        }}
        .insight-item {{
            background: rgba(124, 58, 237, 0.1);
            border-radius: 10px;
            padding: 15px;
            margin: 10px 0;
            border-left: 3px solid #7c3aed;
        }}
        .recommendation {{
            background: rgba(236, 72, 153, 0.1);
            border-radius: 10px;
            padding: 15px;
            margin: 10px 0;
            border-left: 3px solid #ec4899;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
            color: #94a3b8;
            font-size: 0.9rem;
        }}
        .status-badge {{
            display: inline-block;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
            background: rgba(34, 197, 94, 0.15);
            color: #4ade80;
            border: 1px solid rgba(34, 197, 94, 0.3);
        }}
        .status-badge.warning {{
            background: rgba(245, 158, 11, 0.15);
            color: #fbbf24;
            border-color: rgba(245, 158, 11, 0.3);
        }}
        .status-badge.danger {{
            background: rgba(239, 68, 68, 0.15);
            color: #fca5a5;
            border-color: rgba(239, 68, 68, 0.3);
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛡️ Security System Report</h1>
            <p><strong>{report_type}</strong></p>
            <p>Period: {period}</p>
            <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-label">Total Detections</div>
                <div class="metric-value">{summary.get('total_detections', 0):,}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Violations</div>
                <div class="metric-value" style="color: #ef4444;">{summary.get('total_violations', 0):,}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Violation Rate</div>
                <div class="metric-value" style="color: #f59e0b;">{summary.get('violation_rate', 0):.1f}%</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Avg Confidence</div>
                <div class="metric-value" style="color: #22c55e;">{summary.get('avg_confidence', 0):.1f}%</div>
            </div>
        </div>
"""
        
        # Add KPIs if available
        if kpis:
            html += """
        <div class="section">
            <h2>📊 Key Performance Indicators</h2>
"""
            if 'mttr' in kpis:
                mttr = kpis['mttr']
                html += f"""
            <div class="insight-item">
                <strong>Mean Time To Respond:</strong> {mttr.get('mttr_minutes', 0):.1f} minutes
                <br>Total Incidents: {mttr.get('total_incidents', 0)}
            </div>
"""
            if 'false_positive_rate' in kpis:
                fpr = kpis['false_positive_rate']
                html += f"""
            <div class="insight-item">
                <strong>False Positive Rate:</strong> {fpr.get('false_positive_rate', 0):.1f}%
                <br>Detection Accuracy: {fpr.get('precision', 0):.1f}%
            </div>
"""
            if 'coverage' in kpis:
                cov = kpis['coverage']
                html += f"""
            <div class="insight-item">
                <strong>System Coverage:</strong> {cov.get('coverage_percentage', 0):.1f}%
                <br>Uptime: {cov.get('uptime_percentage', 0):.1f}%
            </div>
"""
            html += """
        </div>
"""
        
        # Add executive summary if available
        if 'executive_summary' in report_data:
            exec_sum = report_data['executive_summary']
            insights = exec_sum.get('insights', [])
            recommendations = exec_sum.get('recommendations', [])
            
            if insights:
                html += """
        <div class="section">
            <h2>💡 Key Insights</h2>
"""
                for insight in insights:
                    html += f"""
            <div class="insight-item">{insight}</div>
"""
                html += """
        </div>
"""
            
            if recommendations:
                html += """
        <div class="section">
            <h2>🎯 Recommendations</h2>
"""
                for rec in recommendations:
                    html += f"""
            <div class="recommendation">{rec}</div>
"""
                html += """
        </div>
"""
        
        # Footer
        html += """
        <div class="footer">
            <p>🔒 Real-Time Restricted Area Monitoring System</p>
            <p>This is an automated report. Please do not reply to this email.</p>
        </div>
    </div>
</body>
</html>
"""
        return html
    
    def test_email_connection(self) -> Dict[str, Any]:
        """Test email configuration"""
        if not self.config['enabled']:
            return {
                "status": "disabled",
                "message": "Email service is disabled"
            }
        
        if not self.config['sender_email'] or not self.config['sender_password']:
            return {
                "status": "error",
                "message": "Email credentials not configured"
            }
        
        try:
            context = ssl.create_default_context()
            
            if self.config['smtp_port'] == 465:
                with smtplib.SMTP_SSL(self.config['smtp_server'], 
                                     self.config['smtp_port'], 
                                     context=context) as server:
                    server.login(self.config['sender_email'], self.config['sender_password'])
            else:
                with smtplib.SMTP(self.config['smtp_server'], 
                                self.config['smtp_port']) as server:
                    server.starttls(context=context)
                    server.login(self.config['sender_email'], self.config['sender_password'])
            
            return {
                "status": "success",
                "message": "Email connection successful"
            }
        
        except Exception as e:
            return {
                "status": "error",
                "message": f"Connection failed: {str(e)}"
            }
    
    def send_violation_alert(self, violation_data: Dict[str, Any], 
                            recipients: Optional[List[str]] = None,
                            snapshot_path: Optional[str] = None,
                            video_path: Optional[str] = None) -> Dict[str, Any]:
        """Send immediate violation alert email with optional snapshot/video attachments"""
        
        if not self.config['enabled']:
            return {
                "status": "disabled",
                "message": "Email service is disabled. Enable in .env file"
            }
        
        if not self.config['sender_email'] or not self.config['sender_password']:
            return {
                "status": "error",
                "message": "Email credentials not configured in .env file"
            }
        
        recipients = recipients or self.config['recipient_emails']
        if not recipients:
            return {
                "status": "error",
                "message": "No recipient emails configured"
            }
        
        # Generate violation alert HTML once
        html_content = self._generate_violation_alert_html(violation_data, snapshot_path)
        subject = f"🚨 VIOLATION ALERT - {violation_data.get('class_name', 'Unknown')} Detected!"
        
        try:
            context = ssl.create_default_context()
            
            if self.config['smtp_port'] == 465:
                with smtplib.SMTP_SSL(self.config['smtp_server'], 
                                     self.config['smtp_port'], 
                                     context=context) as server:
                    server.login(self.config['sender_email'], self.config['sender_password'])
                    
                    # Send individual email to each recipient
                    for recipient in recipients:
                        message = MIMEMultipart("alternative")
                        message["Subject"] = subject
                        message["From"] = self.config['sender_email']
                        message["To"] = recipient.strip()
                        message.attach(MIMEText(html_content, "html"))
                        
                        # Attach snapshot if provided
                        if snapshot_path and os.path.exists(snapshot_path):
                            self._attach_file(message, snapshot_path, "snapshot.jpg", "image/jpeg")
                        
                        # Attach video if provided
                        if video_path and os.path.exists(video_path):
                            self._attach_file(message, video_path, "recording.mp4", "video/mp4")
                        
                        server.sendmail(self.config['sender_email'], [recipient.strip()], message.as_string())
                        
            else:
                with smtplib.SMTP(self.config['smtp_server'], 
                                self.config['smtp_port']) as server:
                    server.starttls(context=context)
                    server.login(self.config['sender_email'], self.config['sender_password'])
                    
                    # Send individual email to each recipient
                    for recipient in recipients:
                        message = MIMEMultipart("alternative")
                        message["Subject"] = subject
                        message["From"] = self.config['sender_email']
                        message["To"] = recipient.strip()
                        message.attach(MIMEText(html_content, "html"))
                        
                        # Attach snapshot if provided
                        if snapshot_path and os.path.exists(snapshot_path):
                            self._attach_file(message, snapshot_path, "snapshot.jpg", "image/jpeg")
                        
                        # Attach video if provided
                        if video_path and os.path.exists(video_path):
                            self._attach_file(message, video_path, "recording.mp4", "video/mp4")
                        
                        server.sendmail(self.config['sender_email'], [recipient.strip()], message.as_string())
            
            attachments = []
            if snapshot_path and os.path.exists(snapshot_path):
                attachments.append("snapshot.jpg")
            if video_path and os.path.exists(video_path):
                attachments.append("recording.mp4")
            
            return {
                "status": "success",
                "message": f"Violation alert sent to {len(recipients)} recipient(s) with {len(attachments)} attachment(s)",
                "recipients": [r.strip() for r in recipients],
                "violation": violation_data,
                "attachments": attachments
            }
        
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to send violation alert: {str(e)}"
            }
    
    def _attach_file(self, message: MIMEMultipart, file_path: str, filename: str, mime_type: str):
        """Attach a file to the email message"""
        try:
            with open(file_path, 'rb') as fp:
                part = MIMEBase(mime_type.split('/')[0], mime_type.split('/')[1])
                part.set_payload(fp.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', 'attachment', filename=filename)
                message.attach(part)
        except Exception as e:
            print(f"Warning: Could not attach file {file_path}: {e}")
    
    def _generate_violation_alert_html(self, violation_data: Dict[str, Any], snapshot_path: Optional[str] = None) -> str:
        """Generate HTML email template for violation alerts"""
        
        class_name = violation_data.get('class_name', 'Unknown')
        confidence = violation_data.get('confidence', 0)
        timestamp = violation_data.get('timestamp', 'N/A')
        location = violation_data.get('location', 'Main Camera')
        camera_id = violation_data.get('camera_id', 'CAM-001')
        
        # Snapshot section if attachment exists
        snapshot_section = ""
        if snapshot_path:
            snapshot_section = f"""
        <div class="snapshot-section">
            <h3>📸 Snapshot</h3>
            <p>A snapshot has been attached to this email.</p>
            <p><strong>File:</strong> snapshot.jpg</p>
        </div>
"""
        
        # Video section if attachment exists
        video_section = ""
        if violation_data.get('video_path'):
            video_section = f"""
        <div class="video-section">
            <h3>🎬 Video Recording</h3>
            <p>A video recording has been attached to this email.</p>
            <p><strong>File:</strong> recording.mp4</p>
        </div>
"""
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #ffffff;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(239, 68, 68, 0.3);
        }}
        .alert-header {{
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid rgba(239, 68, 68, 0.5);
        }}
        .alert-icon {{
            font-size: 4rem;
            margin-bottom: 10px;
            animation: pulse 1s infinite;
        }}
        @keyframes pulse {{
            0%, 100% {{ transform: scale(1); }}
            50% {{ transform: scale(1.1); }}
        }}
        .alert-title {{
            background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 2rem;
            font-weight: bold;
            margin: 10px 0;
        }}
        .alert-subtitle {{
            color: #fca5a5;
            font-size: 1.1rem;
        }}
        .violation-details {{
            background: rgba(239, 68, 68, 0.1);
            border-radius: 15px;
            padding: 25px;
            margin: 20px 0;
            border-left: 4px solid #ef4444;
        }}
        .detail-row {{
            display: flex;
            justify-content: space-between;
            padding: 12px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }}
        .detail-row:last-child {{
            border-bottom: none;
        }}
        .detail-label {{
            color: #94a3b8;
            font-weight: 500;
        }}
        .detail-value {{
            color: #ffffff;
            font-weight: 600;
        }}
        .confidence-bar {{
            width: 100%;
            height: 10px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 5px;
            margin-top: 10px;
            overflow: hidden;
        }}
        .confidence-fill {{
            height: 100%;
            background: linear-gradient(90deg, #ef4444, #f59e0b);
            border-radius: 5px;
            transition: width 0.3s ease;
        }}
        .action-required {{
            background: rgba(245, 158, 11, 0.1);
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
            border-left: 4px solid #f59e0b;
        }}
        .action-title {{
            color: #fbbf24;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        .action-text {{
            color: #fcd34d;
            font-size: 0.95rem;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
            color: #64748b;
            font-size: 0.85rem;
        }}
        .priority-badge {{
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .priority-high {{
            background: rgba(239, 68, 68, 0.2);
            color: #fca5a5;
            border: 1px solid rgba(239, 68, 68, 0.5);
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="alert-header">
            <div class="alert-icon">🚨</div>
            <div class="alert-title">RESTRICTED AREA VIOLATION</div>
            <div class="alert-subtitle">Immediate Attention Required</div>
            <span class="priority-badge priority-high">High Priority</span>
        </div>
        
        <div class="violation-details">
            <div class="detail-row">
                <span class="detail-label">Detection Time</span>
                <span class="detail-value">{timestamp}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Object Detected</span>
                <span class="detail-value" style="color: #ef4444; font-size: 1.2rem;">{class_name}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Confidence Level</span>
                <span class="detail-value">{confidence:.1f}%</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Camera Location</span>
                <span class="detail-value">{location}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Camera ID</span>
                <span class="detail-value">{camera_id}</span>
            </div>
            <div class="confidence-bar">
                <div class="confidence-fill" style="width: {confidence}%"></div>
            </div>
        </div>
        
        <div class="action-required">
            <div class="action-title">⚠️ Required Action</div>
            <div class="action-text">
                A {class_name} has been detected in the restricted area. 
                Please verify the situation immediately and take appropriate action.
            </div>
        </div>
        
        <div class="footer">
            <p>🔒 Real-Time Restricted Area Monitoring System</p>
            <p>This is an automated violation alert. Please do not reply to this email.</p>
            <p>System generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>
"""
        return html
