"""
=============================================================================
ADVANCED EMAIL REPORTING MODULE
=============================================================================
Scheduled email reports with custom templates and PDF/CSV attachments
=============================================================================
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.application import MIMEApplication
from email import encoders
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path
import json
import os
import csv
from io import StringIO, BytesIO

# Optional PDF generation
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

import pandas as pd
from business_intelligence import AnalyticsDashboard, ReportGenerator


class EmailReportTemplate:
    """Email report template manager"""
    
    # Template definitions
    TEMPLATES = {
        "summary": {
            "name": "Executive Summary",
            "description": "High-level overview of key metrics",
            "sections": ["kpi_summary", "key_findings", "recommendations"]
        },
        "detailed": {
            "name": "Detailed Analysis",
            "description": "Comprehensive analysis with charts and data",
            "sections": ["executive_summary", "detections_analysis", "violations_analysis", "trend_analysis", "recommendations"]
        },
        "compliance": {
            "name": "Compliance Report",
            "description": "Regulatory and compliance-focused report",
            "sections": ["compliance_metrics", "violations_log", "incident_summary", "recommendations"]
        },
        "operational": {
            "name": "Operational Report",
            "description": "Day-to-day operational metrics",
            "sections": ["daily_summary", "hourly_breakdown", "top_incidents", "system_status"]
        }
    }
    
    @staticmethod
    def get_template(template_type: str) -> Dict[str, Any]:
        """Get template configuration"""
        return EmailReportTemplate.TEMPLATES.get(template_type, EmailReportTemplate.TEMPLATES["summary"])
    
    @staticmethod
    def list_templates() -> List[Dict[str, str]]:
        """List all available templates"""
        return [
            {
                "id": key,
                "name": val["name"],
                "description": val["description"]
            }
            for key, val in EmailReportTemplate.TEMPLATES.items()
        ]


class AdvancedEmailReporter:
    """Advanced email reporting with templates and attachments"""
    
    def __init__(self):
        self.load_email_config()
        self.analytics = AnalyticsDashboard()
        self.report_gen = ReportGenerator()
    
    def load_email_config(self) -> Dict[str, Any]:
        """Load email configuration from .env file"""
        env_file = Path(__file__).parent / ".env"
        self.config = {
            "enabled": False,
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 465,
            "sender_email": "",
            "sender_password": "",
            "sender_name": "Intrusion Detection System",
            "recipient_emails": []
        }
        
        if env_file.exists():
            try:
                with open(env_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip()
                            
                            if key == 'EMAIL_ENABLED':
                                self.config['enabled'] = value.lower() == 'true'
                            elif key == 'EMAIL_SMTP_SERVER':
                                self.config['smtp_server'] = value
                            elif key == 'EMAIL_SMTP_PORT':
                                self.config['smtp_port'] = int(value)
                            elif key == 'EMAIL_SENDER_EMAIL':
                                self.config['sender_email'] = value
                            elif key == 'EMAIL_SENDER_PASSWORD':
                                self.config['sender_password'] = value
                            elif key == 'EMAIL_SENDER_NAME':
                                self.config['sender_name'] = value
                            elif key == 'EMAIL_RECIPIENT_EMAIL':
                                self.config['recipient_emails'] = [e.strip() for e in value.split(',')]
            except Exception as e:
                print(f"Warning: Error loading email config: {e}")
        
        return self.config
    
    def send_scheduled_report(self, 
                            report_type: str = "daily",
                            template_type: str = "summary",
                            recipients: Optional[List[str]] = None,
                            include_csv: bool = True,
                            include_pdf: bool = False) -> Dict[str, Any]:
        """
        Send scheduled report email
        
        Args:
            report_type: 'daily', 'weekly', 'monthly'
            template_type: Template to use
            recipients: Email recipients (uses config if None)
            include_csv: Include CSV attachment
            include_pdf: Include PDF attachment
        
        Returns:
            Status dictionary
        """
        try:
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
            
            # Generate report data
            report_data = self._generate_report_data(report_type, template_type)
            
            # Create email
            message = MIMEMultipart("mixed")
            message["Subject"] = report_data["subject"]
            message["From"] = f"{self.config['sender_name']} <{self.config['sender_email']}>"
            message["To"] = ", ".join(recipients)
            
            # Create email body
            html_content = self._generate_html_body(report_data, template_type)
            html_part = MIMEText(html_content, "html")
            message.attach(html_part)
            
            # Add attachments
            if include_csv:
                csv_data = self._generate_csv_attachment(report_type)
                if csv_data:
                    csv_part = MIMEBase('application', 'octet-stream')
                    csv_part.set_payload(csv_data)
                    encoders.encode_base64(csv_part)
                    csv_part.add_header('Content-Disposition', 'attachment', 
                                      filename=f'report_{report_type}_{datetime.now().strftime("%Y%m%d")}.csv')
                    message.attach(csv_part)
            
            if include_pdf and HAS_REPORTLAB:
                pdf_data = self._generate_pdf_attachment(report_data, report_type)
                if pdf_data:
                    pdf_part = MIMEApplication(pdf_data, 'octet-stream')
                    pdf_part.add_header('Content-Disposition', 'attachment',
                                      filename=f'report_{report_type}_{datetime.now().strftime("%Y%m%d")}.pdf')
                    message.attach(pdf_part)
            
            # Send email
            self._send_smtp(message, recipients)
            
            return {
                "status": "success",
                "message": f"Report sent to {len(recipients)} recipient(s)",
                "recipients": recipients,
                "report_type": report_type,
                "timestamp": datetime.now().isoformat()
            }
        
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    def _generate_report_data(self, report_type: str, template_type: str) -> Dict[str, Any]:
        """Generate report data based on type"""
        # Get analytics data from available methods
        try:
            analytics_data = self.analytics.get_executive_summary()
            # Flatten key_metrics to top level for easier access
            if 'key_metrics' in analytics_data:
                for key, value in analytics_data['key_metrics'].items():
                    analytics_data[key] = value
        except Exception as e:
            # Fallback if executive summary fails
            analytics_data = {
                "period": "Error retrieving data",
                "total_detections": 0,
                "total_violations": 0,
                "avg_confidence": 0,
                "violation_rate": 0,
                "key_metrics": {},
                "insights": [str(e)],
                "recommendations": []
            }
        
        if report_type == "daily":
            period = "Daily"
            date_range = f"{datetime.now().strftime('%Y-%m-%d')}"
        elif report_type == "weekly":
            period = "Weekly"
            start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            end_date = datetime.now().strftime('%Y-%m-%d')
            date_range = f"{start_date} to {end_date}"
        else:  # monthly
            period = "Monthly"
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            end_date = datetime.now().strftime('%Y-%m-%d')
            date_range = f"{start_date} to {end_date}"
        
        return {
            "title": f"{period} Security Report",
            "subject": f"[Security Report] {period} Intrusion Detection Summary - {datetime.now().strftime('%Y-%m-%d')}",
            "period": period,
            "date_range": date_range,
            "generated_at": datetime.now().isoformat(),
            "analytics": analytics_data,
            "template": template_type
        }
    
    def _generate_html_body(self, report_data: Dict[str, Any], template_type: str) -> str:
        """Generate HTML email body"""
        analytics = report_data.get("analytics", {})
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f5f5f5; margin: 0; padding: 0; }}
                .container {{ max-width: 800px; margin: 0 auto; background-color: white; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }}
                .header h1 {{ margin: 0; font-size: 28px; }}
                .header p {{ margin: 10px 0 0 0; opacity: 0.9; }}
                .content {{ padding: 30px; }}
                .section {{ margin-bottom: 30px; }}
                .section-title {{ font-size: 18px; font-weight: bold; color: #333; border-bottom: 3px solid #667eea; padding-bottom: 10px; margin-bottom: 15px; }}
                .kpi-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; margin-bottom: 20px; }}
                .kpi-card {{ background-color: #f8f9fa; border-left: 4px solid #667eea; padding: 15px; border-radius: 4px; }}
                .kpi-label {{ font-size: 12px; color: #666; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; }}
                .kpi-value {{ font-size: 24px; font-weight: bold; color: #333; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
                th {{ background-color: #667eea; color: white; padding: 12px; text-align: left; font-weight: 600; }}
                td {{ padding: 12px; border-bottom: 1px solid #eee; }}
                tr:hover {{ background-color: #f5f5f5; }}
                .footer {{ background-color: #f8f9fa; padding: 20px; text-align: center; color: #666; font-size: 12px; border-top: 1px solid #eee; }}
                .alert {{ padding: 15px; margin-bottom: 15px; border-radius: 4px; }}
                .alert-warning {{ background-color: #fff3cd; border-left: 4px solid #ffc107; color: #856404; }}
                .alert-success {{ background-color: #d4edda; border-left: 4px solid #28a745; color: #155724; }}
                .alert-danger {{ background-color: #f8d7da; border-left: 4px solid #dc3545; color: #721c24; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🛡️ Intrusion Detection System</h1>
                    <p>{report_data['title']}</p>
                    <p style="font-size: 14px; margin-top: 5px;">{report_data['date_range']}</p>
                </div>
                
                <div class="content">
        """
        
        # Add KPI section
        html += """
                    <div class="section">
                        <div class="section-title">📊 Key Performance Indicators</div>
                        <div class="kpi-grid">
        """
        
        if analytics:
            # Extract values with proper defaults
            total_detections = analytics.get("total_detections", 0)
            total_violations = analytics.get("total_violations", 0)
            avg_conf = analytics.get("avg_confidence", 0)
            mttr = analytics.get("mttr_minutes", analytics.get("mttr", "N/A"))
            
            kpis = [
                ("Total Detections", total_detections if total_detections else 0),
                ("Violations", total_violations if total_violations else 0),
                ("Avg Confidence", f"{float(avg_conf):.1f}%" if avg_conf else "0.0%"),
                ("MTTR", f"{float(mttr):.1f} min" if isinstance(mttr, (int, float)) else str(mttr)),
            ]
            
            for label, value in kpis:
                html += f"""
                            <div class="kpi-card">
                                <div class="kpi-label">{label}</div>
                                <div class="kpi-value">{value}</div>
                            </div>
                """
            
            html += """
                        </div>
        """
            
            # Add findings section
            if analytics.get("executive_summary"):
                summary = analytics["executive_summary"]
                html += f"""
                    <div class="section">
                        <div class="section-title">📋 Executive Summary</div>
                        <p>{summary.get('summary', 'No summary available')}</p>
                    </div>
                """
            
            # Add recommendations
            recommendations_list = analytics.get("recommendations", [])
            if recommendations_list:
                html += """
                    <div class="section">
                        <div class="section-title">💡 Recommendations</div>
                        <ul>
                """
                for rec in recommendations_list[:5]:
                    html += f"<li>{rec}</li>"
                html += """
                        </ul>
                    </div>
                """
        
        html += """
                </div>
                
                <div class="footer">
                    <p>This is an automated report generated by the Intrusion Detection System.</p>
                    <p>Generated: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _generate_csv_attachment(self, report_type: str) -> Optional[str]:
        """Generate CSV data"""
        try:
            # Load detection data
            df = pd.read_csv("data/detection_log.csv")
            
            # Filter by date range
            df['Date'] = pd.to_datetime(df.get('Date', df.get('Timestamp', None)))
            
            if report_type == "daily":
                cutoff = datetime.now() - timedelta(days=1)
            elif report_type == "weekly":
                cutoff = datetime.now() - timedelta(days=7)
            else:  # monthly
                cutoff = datetime.now() - timedelta(days=30)
            
            df_filtered = df[df['Date'] >= cutoff]
            
            # Convert to CSV string
            csv_buffer = StringIO()
            df_filtered.to_csv(csv_buffer, index=False)
            return csv_buffer.getvalue()
        
        except Exception as e:
            print(f"Error generating CSV: {e}")
            return None
    
    def _generate_pdf_attachment(self, report_data: Dict[str, Any], report_type: str) -> Optional[bytes]:
        """Generate PDF attachment"""
        if not HAS_REPORTLAB:
            return None
        
        try:
            from io import BytesIO
            
            pdf_buffer = BytesIO()
            doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
            elements = []
            
            styles = getSampleStyleSheet()
            style_title = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#667eea'),
                spaceAfter=6,
                alignment=TA_CENTER
            )
            
            style_heading = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                textColor=colors.HexColor('#333333'),
                spaceAfter=12,
                spaceBefore=12
            )
            
            # Title
            elements.append(Paragraph(report_data['title'], style_title))
            elements.append(Paragraph(f"Period: {report_data['date_range']}", styles['Normal']))
            elements.append(Spacer(1, 0.3*inch))
            
            # KPI Section
            elements.append(Paragraph("Key Performance Indicators", style_heading))
            
            analytics = report_data.get('analytics', {})
            kpi_data = [
                ['Metric', 'Value'],
                ['Total Detections', str(analytics.get('total_detections', 0))],
                ['Violations', str(analytics.get('total_violations', 0))],
                ['Avg Confidence', f"{analytics.get('avg_confidence', 0):.1f}%"],
                ['MTTR', str(analytics.get('mttr', 'N/A'))]
            ]
            
            table = Table(kpi_data, colWidths=[3*inch, 3*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(table)
            elements.append(Spacer(1, 0.3*inch))
            
            # Build PDF
            doc.build(elements)
            pdf_buffer.seek(0)
            return pdf_buffer.read()
        
        except Exception as e:
            print(f"Error generating PDF: {e}")
            return None
    
    def _send_smtp(self, message: MIMEMultipart, recipients: List[str]):
        """Send via SMTP"""
        context = ssl.create_default_context()
        
        with smtplib.SMTP_SSL(self.config['smtp_server'], self.config['smtp_port'], context=context) as server:
            server.login(self.config['sender_email'], self.config['sender_password'])
            server.sendmail(self.config['sender_email'], recipients, message.as_string())


class ReportScheduleManager:
    """Manage scheduled report delivery"""
    
    def __init__(self, schedules_file: str = "data/report_schedules.json"):
        self.schedules_file = Path(schedules_file)
        self.schedules_file.parent.mkdir(parents=True, exist_ok=True)
        self.reporter = AdvancedEmailReporter()
    
    def add_schedule(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Add new report schedule"""
        try:
            schedules = self.get_schedules()
            
            schedule_id = f"schedule_{len(schedules) + 1}_{int(datetime.now().timestamp())}"
            config['id'] = schedule_id
            config['created_at'] = datetime.now().isoformat()
            config['last_sent'] = None
            config['next_send'] = self._calculate_next_send(config)
            config['active'] = config.get('active', True)
            
            schedules.append(config)
            self._save_schedules(schedules)
            
            return {
                "status": "success",
                "schedule_id": schedule_id,
                "message": "Schedule created successfully"
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def update_schedule(self, schedule_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing schedule"""
        try:
            schedules = self.get_schedules()
            
            for schedule in schedules:
                if schedule['id'] == schedule_id:
                    schedule.update(config)
                    schedule['next_send'] = self._calculate_next_send(schedule)
                    self._save_schedules(schedules)
                    return {
                        "status": "success",
                        "message": "Schedule updated successfully"
                    }
            
            return {"status": "error", "message": "Schedule not found"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def delete_schedule(self, schedule_id: str) -> Dict[str, Any]:
        """Delete schedule"""
        try:
            schedules = self.get_schedules()
            schedules = [s for s in schedules if s['id'] != schedule_id]
            self._save_schedules(schedules)
            return {
                "status": "success",
                "message": "Schedule deleted successfully"
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def get_schedules(self) -> List[Dict[str, Any]]:
        """Get all schedules"""
        try:
            if self.schedules_file.exists():
                with open(self.schedules_file, 'r') as f:
                    return json.load(f)
            return []
        except Exception as e:
            print(f"Error loading schedules: {e}")
            return []
    
    def trigger_report(self, schedule_id: str) -> Dict[str, Any]:
        """Manually trigger a scheduled report"""
        try:
            schedules = self.get_schedules()
            
            for schedule in schedules:
                if schedule['id'] == schedule_id:
                    result = self.reporter.send_scheduled_report(
                        report_type=schedule.get('report_type', 'daily'),
                        template_type=schedule.get('template_type', 'summary'),
                        recipients=schedule.get('recipients', []),
                        include_csv=schedule.get('include_csv', True),
                        include_pdf=schedule.get('include_pdf', False)
                    )
                    
                    if result['status'] == 'success':
                        schedule['last_sent'] = datetime.now().isoformat()
                        self._save_schedules(schedules)
                    
                    return result
            
            return {"status": "error", "message": "Schedule not found"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def _calculate_next_send(self, schedule: Dict[str, Any]) -> str:
        """Calculate next send time"""
        now = datetime.now()
        send_time = schedule.get('send_time', '08:00')
        
        hour, minute = map(int, send_time.split(':'))
        next_send = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        if next_send <= now:
            next_send += timedelta(days=1)
        
        return next_send.isoformat()
    
    def _save_schedules(self, schedules: List[Dict[str, Any]]):
        """Save schedules to file"""
        with open(self.schedules_file, 'w') as f:
            json.dump(schedules, f, indent=2)
