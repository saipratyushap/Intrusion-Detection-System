import os
import json
import sys
import uuid
import threading
import time
import platform
import psutil
from pathlib import Path
from flask import Flask, request, jsonify, send_file, render_template_string, abort, Response
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import pandas as pd
from collections import Counter
from datetime import datetime, timedelta
from ultralytics import YOLO
import cv2
import numpy as np
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Import Business Intelligence modules
from business_intelligence import AnalyticsDashboard, ReportGenerator, CostAnalyzer, _convert_to_native_types
from email_service import EmailService
from report_scheduler import get_scheduler

# Import Advanced Analytics & Email Reporting modules
try:
    from advanced_analytics import (
        PredictiveAnalytics, AnomalyDetection, StatisticalAnalyzer,
        get_predictive_forecast, get_trend_analysis, detect_anomalies,
        detect_behavioral_anomalies, calculate_kpis, get_correlation_analysis,
        get_percentile_analysis
    )
    HAS_ADVANCED_ANALYTICS = True
except ImportError:
    HAS_ADVANCED_ANALYTICS = False
    print("Warning: advanced_analytics.py not found")

try:
    from advanced_email_reporting import (
        AdvancedEmailReporter, ReportScheduleManager, EmailReportTemplate
    )
    HAS_EMAIL_REPORTING = True
except ImportError:
    HAS_EMAIL_REPORTING = False
    print("Warning: advanced_email_reporting.py not found")

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# App & Extensions
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
app = Flask(__name__,
            static_folder=str(Path(__file__).parent.parent / "frontend" / "static"),
            static_url_path="/static",
            template_folder=str(Path(__file__).parent.parent / "frontend" / "templates"))

CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

app.camera_active = False
app.alert_active = False
last_email_time = {}

def send_violation_email_internal(class_name, confidence, snapshot_path=None):
    ALERT_RECIPIENT = "gopalmuri1919@gmail.com"
    ALERT_SENDER = os.environ.get('EMAIL_SENDER_EMAIL', 'p.saipratyusha732@gmail.com')
    ALERT_PASSWORD = os.environ.get('EMAIL_SENDER_PASSWORD', 'miduuotoblozqzqj')
    print(f"🔍 send_violation_email_internal started for {class_name}")
    try:
        msg = MIMEMultipart()
        msg['From'] = ALERT_SENDER
        msg['To'] = ALERT_RECIPIENT
        msg['Subject'] = f'🚨 INTRUSION ALERT: {class_name} Detected!'
        body = f"""
        <html><body style='font-family:Arial,sans-serif;padding:20px;'>
        <div style='max-width:600px;margin:0 auto;border:2px solid #dc3545;border-radius:10px;padding:20px;'>
            <h2 style='color:#dc3545;'>🚨 Intrusion Detection Alert</h2>
            <p><strong>Object Detected:</strong> {class_name}</p>
            <p><strong>Confidence:</strong> {confidence:.1%}</p>
            <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>Location:</strong> Main Camera (CAM-001)</p>
            <p style='color:#dc3545;font-weight:bold;'>⚠️ Immediate action may be required!</p>
        </div>
        </body></html>
        """
        msg.attach(MIMEText(body, 'html'))
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(ALERT_SENDER, ALERT_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"✅ Alert email sent to {ALERT_RECIPIENT} for {class_name}")
        return True
    except Exception as e:
        print(f"❌ Error sending alert email: {e}")
        return False

def send_email_notification(class_name, confidence, snapshot_path=None):
    global last_email_time
    print(f"📧 send_email_notification called for {class_name}")
    current_time = time.time()
    if class_name in last_email_time:
        if current_time - last_email_time[class_name] < 10:
            print(f"⏰ Rate limited: skipping email for {class_name} (last sent < 10s ago)")
            return
    last_email_time[class_name] = current_time
    def email_worker():
        print(f"🔧 email_worker starting for {class_name}")
        if send_violation_email_internal(class_name, confidence, snapshot_path):
            print(f"✅ Email sent successfully for {class_name} violation")
        else:
            print(f"❌ Email sending failed for {class_name}")
    thread = threading.Thread(target=email_worker, daemon=True)
    thread.start()

# ─────────────────────────────────────────────────
# YOLO & Camera State
# ─────────────────────────────────────────────────
yolo_model = None
try:
    _model_path = os.path.abspath(os.path.join(str(Path(__file__).parent.parent), 'model', 'best.pt'))
    if os.path.exists(_model_path):
        yolo_model = YOLO(_model_path)
except Exception as e:
    print(f"Failed to load YOLO model: {e}")

global_cap = None
camera_lock = threading.Lock()
camera_settings = {
    "conf_threshold": 0.15,
    "detect_classes": [] if not yolo_model else list(yolo_model.names.values()),
    "alert_classes": [] if not yolo_model else list(yolo_model.names.values()),
    "recording": False,
    "video_writer": None,
    "recording_start_time": None
}

class_colors = {}
if yolo_model:
    import random
    class_colors = {yolo_model.names[class_id]: tuple(random.randint(0, 255) for _ in range(3)) for class_id in yolo_model.names}

object_entry_times = {}

def draw_restricted_area(frame):
    h, w, _ = frame.shape
    center = (w // 2, h // 2)
    axes = (w // 4, h // 8)
    cv2.ellipse(frame, center, axes, 0, 0, 360, (0, 0, 255), 2)
    return frame, center, axes

def is_near_restricted_area(box, center, axes):
    x1, y1, x2, y2 = box
    obj_center = ((x1 + x2) // 2, (y1 + y2) // 2)
    distance = np.linalg.norm(np.array(center) - np.array(obj_center))
    return distance < (min(axes) + 50)

def generate_frames():
    global global_cap, object_entry_times
    while True:
        with camera_lock:
            if not global_cap:
                time.sleep(0.5)
                continue
            ret, frame = global_cap.read()
        
        if not ret or frame is None:
            time.sleep(0.1)
            continue
            
        annotated_frame = frame.copy()
        object_inside = False
        
        if yolo_model and camera_settings.get("detect_classes"):
            results = yolo_model(frame, conf=camera_settings["conf_threshold"], iou=0.3)
            annotated_frame, center, axes = draw_restricted_area(annotated_frame)
            
            for result in results[0].boxes:
                class_id = int(result.cls)
                class_name = yolo_model.names[class_id]
                
                if class_name in camera_settings["detect_classes"]:
                    color = class_colors.get(class_name, (0, 255, 0))
                    x1, y1, x2, y2 = map(int, result.xyxy[0])
                    conf = float(result.conf[0])
                    cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 3)
                    cv2.putText(annotated_frame, f"{class_name} {conf:.2f}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                    
                    if is_near_restricted_area([x1, y1, x2, y2], center, axes):
                        if class_name in camera_settings["alert_classes"]:
                            object_inside = True
                            cv2.putText(annotated_frame, f"{class_name} in Restricted Area!", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                            
                            if class_name not in object_entry_times:
                                object_entry_times[class_name] = time.time()
                            
                            elapsed = time.time() - object_entry_times[class_name]
                            remaining = max(0, 2.0 - elapsed)
                            
                            if remaining > 0:
                                cv2.putText(annotated_frame, f"Alert in {remaining:.1f}s", (x1, y1 - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
                                
                            if elapsed > 2:
                                print(f"🚨 VIOLATION DETECTED: {class_name} with {conf:.2%} confidence")
                                data = {"Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Class": class_name, "Confidence": conf, "Restricted Area Violation": "Yes"}
                                df = pd.DataFrame([data])
                                df.to_csv(csv_file, mode='a', header=False, index=False)
                                object_entry_times[class_name] = time.time()
                                
                                # Snapshot
                                try:
                                    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                                    filename = f"frame_{ts}.jpg"
                                    filepath = os.path.join(frames_dir, filename)
                                    cv2.imwrite(filepath, annotated_frame)
                                    print(f"📸 Snapshot saved: {filepath}")
                                    
                                    print(f"📧 Sending email alert for {class_name}...")
                                    send_email_notification(class_name, conf, filepath)
                                except Exception as e:
                                    print(f"Snapshot/Email error: {e}")
                                
                                cv2.putText(annotated_frame, "ALERT LOGGED!", (x1, y1 - 55), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                                
        app.alert_active = object_inside
        
        ret, buffer = cv2.imencode('.jpg', annotated_frame)
        if app.camera_active:
            # Recording logic
            if camera_settings["recording"] and camera_settings["video_writer"]:
                try:
                    camera_settings["video_writer"].write(annotated_frame)
                except Exception as e:
                    print(f"Recording error: {e}")

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
        else:
            time.sleep(0.5)

# ─────────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────────
csv_file    = str(Path(__file__).parent.parent / "data" / "detection_log.csv")
frames_dir  = str(Path(__file__).parent.parent / "data" / "frames")
recordings_dir = str(Path(__file__).parent.parent / "data" / "recordings")
data_dir    = str(Path(__file__).parent.parent / "data")
CAMERAS_FILE      = str(Path(__file__).parent.parent / "data" / "cameras.json")
USER_ACTIVITY_FILE = str(Path(__file__).parent.parent / "data" / "user_activity.json")

# Ensure directories exist
for d in [frames_dir, recordings_dir, data_dir]:
    os.makedirs(d, exist_ok=True)

# ─────────────────────────────────────────────────
# Video Recording Helpers
# ─────────────────────────────────────────────────
def get_video_writer(filepath, fps=20, width=640, height=480):
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    writer = cv2.VideoWriter(filepath, fourcc, fps, (width, height))
    if writer.isOpened():
        print(f"✓ Video writer initialized: {filepath}")
        return writer
    print("❌ Failed to initialize video writer")
    return None

@app.route('/api/recording/start', methods=['POST'])
def start_recording_api():
    global camera_settings
    if camera_settings["recording"]:
        return jsonify({"status": "already_recording"})
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"recording_{timestamp}.avi"
    filepath = os.path.join(recordings_dir, filename)
    
    # Try to get frame size from global_cap
    width, height = 640, 480
    if global_cap and global_cap.isOpened():
        width = int(global_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(global_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    writer = get_video_writer(filepath, 20, width, height)
    if writer:
        camera_settings["recording"] = True
        camera_settings["video_writer"] = writer
        camera_settings["recording_start_time"] = time.time()
        return jsonify({"status": "started", "file": filename})
    return jsonify({"status": "error", "message": "Could not start recording"}), 500

@app.route('/api/recording/stop', methods=['POST'])
def stop_recording_api():
    global camera_settings
    if not camera_settings["recording"]:
        return jsonify({"status": "not_recording"})
    
    if camera_settings["video_writer"]:
        camera_settings["video_writer"].release()
        camera_settings["video_writer"] = None
    
    camera_settings["recording"] = False
    return jsonify({"status": "stopped"})

@app.route('/api/alerts/stats')
def get_alert_stats():
    try:
        if not os.path.exists(csv_file):
            return jsonify({
                "total_alerts": 0, "today_alerts": 0, 
                "week_alerts": 0, "top_class": "N/A"
            })
            
        df = pd.read_csv(csv_file)
        if df.empty:
            return jsonify({
                "total_alerts": 0, "today_alerts": 0, 
                "week_alerts": 0, "top_class": "N/A"
            })
            
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        violations = df[df["Restricted Area Violation"] == "Yes"]
        
        total_alerts = len(violations)
        now = datetime.now()
        today_alerts = len(violations[violations['Timestamp'].dt.date == now.date()])
        week_ago = now - timedelta(days=7)
        week_alerts = len(violations[violations['Timestamp'] >= week_ago])
        
        top_class = "N/A"
        if not violations.empty:
            top_class = violations['Class'].mode().iloc[0]
            
        return jsonify({
            "total_alerts": total_alerts,
            "today_alerts": today_alerts,
            "week_alerts": week_alerts,
            "top_class": top_class
        })
    except Exception as e:
        print(f"Stats error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Service Initialization
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
analytics_service = AnalyticsDashboard(csv_file)
report_service    = ReportGenerator(csv_file)
cost_service      = CostAnalyzer()
email_service     = EmailService()

advanced_analytics       = None
advanced_email_reporter  = None
schedule_manager         = None

if HAS_ADVANCED_ANALYTICS:
    advanced_analytics = PredictiveAnalytics(csv_file)

if HAS_EMAIL_REPORTING:
    advanced_email_reporter = AdvancedEmailReporter()
    schedule_manager        = ReportScheduleManager()

scheduler = get_scheduler()

system_start_time = datetime.now()

# ─────────────────────────────────────────────────
# Auth: OTP + Users (for React frontend)
# ─────────────────────────────────────────────────
import secrets as _secrets
import string as _string
import smtplib
from email.mime import multipart as mime_multipart, text as mime_text
import hashlib as _hashlib

USERS_FILE = str(Path(__file__).parent.parent / "data" / "users.json")
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = os.environ.get('EMAIL_SENDER_EMAIL', 'p.saipratyusha732@gmail.com')
SENDER_PASSWORD = os.environ.get('EMAIL_SENDER_PASSWORD', 'miduuotoblozqzqj')
OTP_EXPIRY_MINUTES = 5

_otp_store = {}  # { email: { otp, time } }

def _hash_password(pw):
    return _hashlib.sha256(pw.encode()).hexdigest()

def _load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def _save_users(users):
    os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f)

@app.route('/api/auth/send-otp', methods=['POST'])
def send_otp():
    data = request.get_json()
    email = data.get('email', '')
    if not email or '@' not in email:
        return jsonify({"success": False, "message": "Invalid email"}), 400
    otp = ''.join(_secrets.choice(_string.digits) for _ in range(6))
    # Send via SMTP
    try:
        msg = mime_multipart.MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = email
        msg['Subject'] = f'Your OTP Code: {otp}'
        body = f"""
        <html><body style="font-family: Arial, sans-serif; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; border: 1px solid #eee; border-radius: 10px; padding: 20px;">
                <h2 style="color: #709138;">🔐 Security Verification</h2>
                <p>Please use the following One-Time Password (OTP) to access the system:</p>
                <div style="background: #f8f9fa; padding: 20px; text-align: center; font-size: 32px; font-weight: bold; letter-spacing: 5px; color: #709138; border-radius: 8px;">
                    {otp}
                </div>
                <p style="color: #666; font-size: 14px; margin-top: 20px;">
                    This code will expire in {OTP_EXPIRY_MINUTES} minutes.
                </p>
            </div>
        </body></html>
        """
        msg.attach(mime_text.MIMEText(body, 'html'))
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        _otp_store[email] = {"otp": otp, "time": datetime.now().isoformat()}
        return jsonify({"success": True, "message": f"Verification code sent to {email}"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/auth/verify-otp', methods=['POST'])
def verify_otp():
    data = request.get_json()
    email = data.get('email', '')
    code = data.get('code', '')
    stored = _otp_store.get(email)
    if not stored:
        return jsonify({"success": False, "message": "No OTP was sent to this email"}), 400
    otp_time = datetime.fromisoformat(stored["time"])
    from datetime import timedelta
    if datetime.now() - otp_time > timedelta(minutes=OTP_EXPIRY_MINUTES):
        del _otp_store[email]
        return jsonify({"success": False, "message": "Code expired. Request a new one."}), 400
    if code == stored["otp"]:
        del _otp_store[email]
        return jsonify({"success": True, "message": "Email verified!"})
    return jsonify({"success": False, "message": "Invalid verification code"}), 400

@app.route('/api/auth/register', methods=['POST'])
def register_user_api():
    data = request.get_json()
    username = data.get('username', '')
    password = data.get('password', '')
    if not username or not password:
        return jsonify({"success": False, "message": "Username and password required"}), 400
    username = username.strip()
    # Username validation
    if len(username) < 3:
        return jsonify({"success": False, "message": "Username must be at least 3 characters"}), 400
    if len(username) > 30:
        return jsonify({"success": False, "message": "Username must be 30 characters or less"}), 400
    import re
    if not re.match(r'^[a-zA-Z0-9._-]+$', username):
        return jsonify({"success": False, "message": "Username can only contain letters, numbers, dots, underscores, and hyphens"}), 400
    if username[0] in '._-':
        return jsonify({"success": False, "message": "Username cannot start with a special character"}), 400
    # Password validation
    if len(password) < 8:
        return jsonify({"success": False, "message": "Password must be at least 8 characters"}), 400
    if not re.search(r'[A-Z]', password):
        return jsonify({"success": False, "message": "Password must contain at least one uppercase letter"}), 400
    if not re.search(r'[a-z]', password):
        return jsonify({"success": False, "message": "Password must contain at least one lowercase letter"}), 400
    if not re.search(r'[0-9]', password):
        return jsonify({"success": False, "message": "Password must contain at least one number"}), 400
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'\"\\|,.<>/?]', password):
        return jsonify({"success": False, "message": "Password must contain at least one special character"}), 400
    users = _load_users()
    if username.lower() in [k.lower() for k in users.keys()]:
        return jsonify({"success": False, "message": "Username already exists"}), 400
    users[username] = _hash_password(password)
    _save_users(users)
    return jsonify({"success": True, "message": "Registration complete!"})

@app.route('/api/auth/login', methods=['POST'])
def login_user_api():
    data = request.get_json()
    username = data.get('username', '')
    password = data.get('password', '')
    users = _load_users()
    for k in users:
        if k.lower() == username.lower():
            if users[k] == _hash_password(password):
                return jsonify({"success": True, "message": "Login successful", "username": k})
            else:
                return jsonify({"success": False, "message": "Invalid password"}), 401
    return jsonify({"success": False, "message": "User not found"}), 401

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Serve data directory files (static-like)
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@app.route("/data/<path:filename>")
def serve_data_file(filename):
    """Serve files from the shared data directory."""
    target = os.path.join(data_dir, filename)
    if os.path.exists(target):
        return send_file(target)
    abort(404)

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# HTML Pages
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
HOME_HTML = """<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Real-Time Monitoring System - ThirdEye</title>
<link rel="icon" type="image/png" href="/static/favicon.png">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:'Inter','Segoe UI',sans-serif;background-color:#F4F7F9;
background-image:radial-gradient(#D1DBE5 1px,transparent 1px);background-size:40px 40px;
min-height:100vh;display:flex;align-items:center;justify-content:center;color:#2D3E50;padding:20px;}
.hero-container{text-align:center;max-width:900px;animation:fadeInUp 0.8s ease-out;}
@keyframes fadeInUp{from{opacity:0;transform:translateY(30px)}to{opacity:1;transform:translateY(0)}}
@keyframes slideDown{from{opacity:0;transform:translateY(-20px)}to{opacity:1;transform:translateY(0)}}
h1{font-size:2.5rem;font-weight:700;margin:0 0 12px 0;color:#709138;letter-spacing:-0.5px;animation:slideDown 0.8s ease-out 0.1s both;}
.subtitle{font-size:1rem;color:#4A4A4A;margin:0 0 40px 0;line-height:1.6;}
.button-group{display:flex;gap:20px;justify-content:center;flex-wrap:wrap;margin-bottom:70px;}
.btn{padding:16px 40px;border-radius:16px;font-size:1.05rem;font-weight:700;border:none;cursor:pointer;
transition:all 0.3s;display:inline-flex;align-items:center;gap:12px;text-decoration:none;color:white;
text-transform:uppercase;letter-spacing:0.5px;}
.btn-primary{background:#709138;box-shadow:0 10px 25px rgba(112,145,56,0.2);}
.btn-primary:hover{transform:translateY(-4px);box-shadow:0 15px 40px rgba(0,212,255,0.5);}
.btn-secondary{background:#00A1C9;}
.btn-secondary:hover{transform:translateY(-4px);}
.info-cards{display:grid;grid-template-columns:repeat(3,1fr);gap:25px;margin-top:40px;}
.card{background:#FFFFFF;border:1px solid #D1DBE5;border-radius:20px;padding:40px 30px;text-align:center;
transition:all 0.3s;animation:fadeInUp 0.8s ease-out;}
.card:hover{transform:translateY(-8px);box-shadow:0 12px 40px rgba(0,212,255,0.15);}
.card-icon{font-size:3rem;margin-bottom:20px;color:#709138;}
.card h3{font-size:1.15rem;margin:0 0 12px 0;color:#2D3E50;font-weight:600;}
.card p{color:#4A4A4A;margin:0;font-size:0.875rem;line-height:1.5;}
.logo{display:flex;align-items:center;justify-content:center;margin:0 auto 30px;}
@media(max-width:768px){.info-cards{grid-template-columns:1fr;}.button-group{flex-direction:column;}}
</style></head><body>
<div class="hero-container">
<div class="logo"><img src="/static/logo.png?v=3" alt="ThirdEye Logo" style="max-height:60px;width:auto;max-width:100%;"></div>
<h1>Real-Time Monitoring System</h1>
<p class="subtitle">Advanced AI-Powered Restricted Area Detection with Business Intelligence</p>
<div class="button-group">
<a href="/data" class="btn btn-primary"><i class="fas fa-chart-line"></i> View Dashboard</a>
<a href="/docs" class="btn btn-primary"><i class="fas fa-code"></i> API Documentation</a>
</div>
<div class="info-cards">
<div class="card"><div class="card-icon"><i class="fas fa-chart-line"></i></div><h3>Live Dashboard</h3><p>Real-time detection metrics and analytics</p></div>
<div class="card"><div class="card-icon"><i class="fas fa-brain"></i></div><h3>AI Analytics</h3><p>Advanced predictive analytics and anomaly detection</p></div>
<div class="card"><div class="card-icon"><i class="fas fa-envelope"></i></div><h3>Email Reports</h3><p>Automated scheduled reporting system</p></div>
</div></div></body></html>"""

@app.route("/")
def get_home():
    """Home page with navigation to dashboard."""
    resp = Response(HOME_HTML, content_type="text/html")
    resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    return resp

@app.route("/data")
def get_data_dashboard():
    """Serve the live monitoring dashboard."""
    return render_template_string(open(
        str(Path(__file__).parent.parent / "frontend" / "templates" / "data.html")).read())

@app.route("/snapshots")
def get_snapshots_gallery():
    """Serve the snapshot gallery page."""
    return render_template_string(open(
        str(Path(__file__).parent.parent / "frontend" / "templates" / "snapshots.html")).read())

@app.route("/docs")
def api_docs():
    """Simple API documentation page."""
    return jsonify({"message": "Visit /api/info for endpoint listing", "info": "/api/info"})

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Activity Feed (in-memory)
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
activity_feed = []
ACTIVITY_FEED_MAX_SIZE = 1000


def sync_activity_from_csv():
    global activity_feed
    synced_count = 0
    try:
        csv_path = os.path.abspath(csv_file)
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            if not df.empty:
                def parse_ts(ts):
                    if pd.isna(ts):
                        return datetime.now()
                    try:
                        return pd.to_datetime(ts)
                    except:
                        return datetime.now()
                df['Timestamp'] = df['Timestamp'].apply(parse_ts)
                df = df.sort_values('Timestamp', ascending=False)
                activity_feed.clear()
                for _, row in df.head(500).iterrows():
                    try:
                        is_viol = str(row.get('Restricted Area Violation', 'No')).lower() == 'yes'
                        conf = float(row.get('Confidence', 0))
                        cls = str(row.get('Class', 'Unknown'))
                        event = {
                            "id": str(len(activity_feed) + 1),
                            "timestamp": row['Timestamp'].strftime('%Y-%m-%dT%H:%M:%S') if hasattr(row['Timestamp'], 'strftime') else str(row['Timestamp']),
                            "type": "detection",
                            "title": f"Detection: {cls}",
                            "description": f"Confidence: {conf*100:.1f}%",
                            "is_violation": is_viol,
                            "class": cls,
                            "confidence": round(conf * 100, 2)
                        }
                        activity_feed.append(event)
                        synced_count += 1
                    except Exception as e:
                        continue
    except Exception as e:
        print(f"Error syncing activity from CSV: {e}")
    return synced_count


def sync_activity_from_user_activity():
    global activity_feed
    synced_count = 0
    try:
        ua_path = os.path.abspath("data/user_activity.json")
        if os.path.exists(ua_path):
            with open(ua_path, 'r') as f:
                data = json.load(f)
            activities = data.get("activities", [])
            for act in activities[:200]:
                try:
                    event = {
                        "id": str(len(activity_feed) + 1),
                        "timestamp": act.get("timestamp", datetime.now().isoformat()),
                        "type": "user_activity",
                        "title": f"{act.get('user','Unknown')}: {act.get('action','Unknown')}",
                        "description": act.get("details", ""),
                        "status": act.get("status", "success"),
                        "user": act.get("user", "Unknown"),
                        "action": act.get("action", "Unknown")
                    }
                    activity_feed.append(event)
                    synced_count += 1
                except:
                    continue
    except Exception as e:
        print(f"Error syncing user activity: {e}")
    return synced_count


def refresh_activity_feed():
    global activity_feed
    activity_feed.clear()
    sync_activity_from_csv()
    sync_activity_from_user_activity()
    return len(activity_feed)


def add_activity_event(event_type, data):
    event = {
        "id": str(len(activity_feed) + 1),
        "timestamp": datetime.now().isoformat(),
        "type": event_type,
        "data": data
    }
    activity_feed.insert(0, event)
    if len(activity_feed) > ACTIVITY_FEED_MAX_SIZE:
        activity_feed.pop()
    return event


# Initialize activity feed on startup
print("Initializing activity feed from CSV and user activity...")
refresh_activity_feed()

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# WebSocket Background Tasks
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
_ws_thread_started = False
_ws_thread_lock = threading.Lock()


def _detection_broadcast_loop():
    """Broadcast new CSV rows to /ws clients every second."""
    last_line_count = 0
    while True:
        try:
            if os.path.exists(csv_file):
                df = pd.read_csv(csv_file)
                if len(df) > last_line_count:
                    new_data = df.iloc[last_line_count:]
                    last_line_count = len(df)
                    total_violations = df[df["Restricted Area Violation"] == "Yes"].shape[0]
                    class_counts = Counter(df["Class"])
                    most_frequent = class_counts.most_common(1)[0][0] if class_counts else "None"
                    top5 = df[df["Restricted Area Violation"] == "Yes"].tail(5).to_dict(orient="records")
                    payload = {
                        "timestamp": new_data["Timestamp"].tolist(),
                        "class": new_data["Class"].tolist(),
                        "confidence": new_data["Confidence"].apply(lambda x: round(float(x) * 100, 2)).tolist(),
                        "restricted_area_violation": new_data["Restricted Area Violation"].tolist(),
                        "summary": {
                            "total_detections": len(df),
                            "total_violations": total_violations,
                            "most_frequent_class": most_frequent,
                            "top_5_violations": top5
                        }
                    }
                    socketio.emit("detection_update", payload, namespace="/")
        except Exception as e:
            print(f"Detection broadcast error: {e}")
        time.sleep(1)


def _data_broadcast_loop():
    """Broadcast full sorted data to /ws/data clients every second."""
    while True:
        try:
            if os.path.exists(csv_file):
                df = pd.read_csv(csv_file)
                if not df.empty:
                    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
                    df = df.sort_values(by='Timestamp', ascending=False)
                    df['Timestamp'] = df['Timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
                    socketio.emit("data_update", {"data": df.to_dict(orient="records")}, namespace="/")
                else:
                    socketio.emit("data_update", {"data": []}, namespace="/")
            else:
                socketio.emit("data_update", {"data": []}, namespace="/")
        except Exception as e:
            print(f"Data broadcast error: {e}")
        time.sleep(1)


def _activity_broadcast_loop():
    """Broadcast activity feed every 2 seconds."""
    while True:
        try:
            if activity_feed:
                socketio.emit("activity_update", {"events": activity_feed[:20]}, namespace="/")
            else:
                if os.path.exists(csv_file):
                    df = pd.read_csv(csv_file)
                    if not df.empty:
                        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
                        df = df.sort_values('Timestamp', ascending=False)
                        recent = df.head(20)
                        events = []
                        for _, row in recent.iterrows():
                            events.append({
                                "timestamp": row['Timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                                "type": "detection",
                                "class": row['Class'],
                                "confidence": round(float(row['Confidence']) * 100, 2),
                                "is_violation": row['Restricted Area Violation'] == "Yes"
                            })
                        socketio.emit("activity_update", {"events": events}, namespace="/")
        except Exception as e:
            print(f"Activity broadcast error: {e}")
        time.sleep(2)


@socketio.on("connect")
def handle_connect():
    global _ws_thread_started
    with _ws_thread_lock:
        if not _ws_thread_started:
            threading.Thread(target=_detection_broadcast_loop, daemon=True).start()
            threading.Thread(target=_data_broadcast_loop, daemon=True).start()
            threading.Thread(target=_activity_broadcast_loop, daemon=True).start()
            _ws_thread_started = True
    emit("connected", {"message": "Connected to ThirdEye monitoring server"})


@socketio.on("disconnect")
def handle_disconnect():
    pass

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Video
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@app.route("/video")
def get_video():
    """Serve the recorded video file."""
    video_path = str(Path(__file__).parent.parent / "data" / "recorded_video.mp4")
    return send_file(video_path, mimetype="video/mp4")

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Snapshots
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@app.route("/api/snapshots-count")
def get_snapshots_count():
    count = 0
    if os.path.exists(frames_dir):
        count = len([f for f in os.listdir(frames_dir) if f.endswith('.jpg')])
    return jsonify({"count": count})


@app.route("/api/snapshots")
def get_snapshots():
    snapshots_list = []
    try:
        if os.path.exists(frames_dir):
            files = [f for f in os.listdir(frames_dir) if f.endswith('.jpg')]
            files = sorted(files, key=lambda x: os.path.getmtime(os.path.join(frames_dir, x)), reverse=True)
            for filename in files[:500]:
                filepath = os.path.join(frames_dir, filename)
                stats = os.stat(filepath)
                parts = filename.replace('.jpg', '').split('_')
                timestamp_str = ""
                if len(parts) >= 3:
                    try:
                        timestamp_str = f"{parts[1][:4]}-{parts[1][4:6]}-{parts[1][6:]} {parts[2][:2]}:{parts[2][2:4]}:{parts[2][4:6]}"
                    except:
                        pass
                if not timestamp_str:
                    timestamp_str = datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                snapshots_list.append({
                    "id": filename,
                    "filename": filename,
                    "timestamp": timestamp_str,
                    "path": f"/data/frames/{filename}",
                    "size": stats.st_size,
                    "class": "Unknown",
                    "confidence": 0.0,
                    "violation": True
                })
        return jsonify({"snapshots": snapshots_list})
    except Exception as e:
        return jsonify({"snapshots": [], "error": str(e)})


@app.route("/api/snapshots/delete", methods=["POST"])
def delete_snapshot():
    try:
        data = request.get_json()
        filename = data.get("id")
        if not filename:
            return jsonify({"message": "Filename ID required"}), 400
        filepath = os.path.join(frames_dir, filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            return jsonify({"status": "success", "message": f"Deleted {filename}"})
        else:
            return jsonify({"message": "File not found"}), 404
    except Exception as e:
        return jsonify({"message": str(e)}), 500

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Alerts
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@app.route("/api/alerts")
def get_alerts():
    limit = request.args.get("limit", 50, type=int)
    try:
        df = pd.read_csv(csv_file)
        if df.empty:
            return jsonify({"total_alerts": 0, "alerts": [], "timestamp": datetime.now().isoformat()})
        violations = df[df["Restricted Area Violation"] == "Yes"].copy()
        violations['Timestamp'] = pd.to_datetime(violations['Timestamp'])
        violations = violations.sort_values('Timestamp', ascending=False)
        recent = violations.head(limit)
        alerts = []
        for _, row in recent.iterrows():
            alerts.append({
                "timestamp": row['Timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                "class": row['Class'],
                "confidence": round(float(row['Confidence']) * 100, 2),
                "is_violation": True
            })
        return jsonify({"total_alerts": len(violations), "recent_alerts": len(alerts), "alerts": alerts, "timestamp": datetime.now().isoformat()})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/alerts/recent")
def get_recent_alerts():
    hours = request.args.get("hours", 24, type=int)
    try:
        df = pd.read_csv(csv_file)
        if df.empty:
            return jsonify({"total_alerts": 0, "time_range_hours": hours, "alerts": [], "timestamp": datetime.now().isoformat()})
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        cutoff = datetime.now() - timedelta(hours=hours)
        recent_df = df[df['Timestamp'] >= cutoff]
        violations = recent_df[recent_df["Restricted Area Violation"] == "Yes"].copy()
        violations = violations.sort_values('Timestamp', ascending=False)
        alerts = []
        for _, row in violations.iterrows():
            alerts.append({
                "timestamp": row['Timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                "class": row['Class'],
                "confidence": round(float(row['Confidence']) * 100, 2)
            })
        return jsonify({"total_alerts": len(violations), "time_range_hours": hours, "alerts": alerts, "timestamp": datetime.now().isoformat()})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/alerts/stats")
def get_alerts_stats():
    try:
        df = pd.read_csv(csv_file)
        if df.empty:
            return jsonify({"total_alerts": 0, "today_alerts": 0, "week_alerts": 0, "unique_classes": 0, "top_class": None, "avg_confidence": 0, "timestamp": datetime.now().isoformat()})
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        violations = df[df["Restricted Area Violation"] == "Yes"].copy()
        today = datetime.now().date()
        today_v = violations[violations['Timestamp'].dt.date == today]
        week_ago = datetime.now() - timedelta(days=7)
        week_v = violations[violations['Timestamp'] >= week_ago]
        top_class = violations['Class'].mode().iloc[0] if not violations.empty else None
        avg_conf = round(violations['Confidence'].mean() * 100, 2) if not violations.empty else 0
        return jsonify({
            "total_alerts": len(violations),
            "today_alerts": len(today_v),
            "week_alerts": len(week_v),
            "unique_classes": violations['Class'].nunique(),
            "top_class": top_class,
            "avg_confidence": avg_conf,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Detection Data
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@app.route("/api/detections/summary")
def get_detections_summary():
    try:
        df = pd.read_csv(csv_file)
        if df.empty:
            return jsonify({"total": 0, "violations": 0, "safe": 0})
        total = len(df)
        violations = len(df[df["Restricted Area Violation"] == "Yes"])
        return jsonify({"total": total, "violations": violations, "safe": total - violations,
                        "avg_confidence": round(df['Confidence'].mean() * 100, 2)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/detections/recent")
def get_recent_detections():
    limit = request.args.get("limit", 100, type=int)
    try:
        df = pd.read_csv(csv_file)
        if df.empty:
            return jsonify({"detections": []})
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        df = df.sort_values('Timestamp', ascending=False).head(limit)
        df['Timestamp'] = df['Timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
        return jsonify({"detections": df.to_dict(orient="records")})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/detections/today")
def get_today_detections():
    try:
        df = pd.read_csv(csv_file)
        if df.empty:
            return jsonify({"total": 0, "violations": 0})
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        today = datetime.now().date()
        today_df = df[df['Timestamp'].dt.date == today]
        return jsonify({
            "total": len(today_df),
            "violations": len(today_df[today_df["Restricted Area Violation"] == "Yes"]),
            "date": str(today)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Business Intelligence â€” KPI Analytics
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@app.route("/api/analytics/kpis/mttr")
def get_mttr():
    try:
        result = analytics_service.calculate_mttr()
        return jsonify(_convert_to_native_types(result))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/analytics/kpis/false-positive-rate")
def get_false_positive_rate():
    try:
        result = analytics_service.calculate_false_positive_rate()
        return jsonify(_convert_to_native_types(result))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/analytics/kpis/coverage")
def get_coverage():
    try:
        result = analytics_service.calculate_coverage_percentage()
        return jsonify(_convert_to_native_types(result))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/analytics/executive-summary")
def get_executive_summary():
    try:
        result = analytics_service.get_executive_summary()
        return jsonify(_convert_to_native_types(result))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/analytics/trend-analysis")
def get_trend_analysis_bi():
    days = request.args.get("days", 30, type=int)
    try:
        result = analytics_service.get_trend_analysis(days=days)
        return jsonify(_convert_to_native_types(result))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/analytics/dashboard")
def get_analytics_dashboard():
    try:
        mttr     = analytics_service.calculate_mttr()
        fpr      = analytics_service.calculate_false_positive_rate()
        coverage = analytics_service.calculate_coverage_percentage()
        summary  = analytics_service.get_executive_summary()
        trend    = analytics_service.get_trend_analysis()
        return jsonify(_convert_to_native_types({
            "mttr": mttr, "false_positive_rate": fpr, "coverage": coverage,
            "executive_summary": summary, "trend_analysis": trend, "timestamp": datetime.now().isoformat()
        }))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Reports
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@app.route("/api/reports/daily")
def get_daily_report():
    date_str = request.args.get("date")
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else datetime.now().date()
        result = report_service.generate_daily_report(date)
        return jsonify(_convert_to_native_types(result))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/reports/weekly")
def get_weekly_report():
    end_date_str = request.args.get("end_date")
    try:
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date() if end_date_str else datetime.now().date()
        result = report_service.generate_weekly_report(end_date)
        return jsonify(_convert_to_native_types(result))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/reports/monthly")
def get_monthly_report():
    year  = request.args.get("year",  datetime.now().year,  type=int)
    month = request.args.get("month", datetime.now().month, type=int)
    try:
        result = report_service.generate_monthly_report(year, month)
        return jsonify(_convert_to_native_types(result))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/reports/compliance/<report_type>")
def get_compliance_report(report_type):
    try:
        result = report_service.generate_compliance_report(report_type)
        return jsonify(_convert_to_native_types(result))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/reports/send-email", methods=["POST"])
def send_report_email():
    data = request.get_json() or {}
    try:
        report_type = data.get("report_type", "daily")
        recipient   = data.get("recipient_email", email_service.config.get("recipient_email", ""))
        if report_type == "weekly":
            report_data = report_service.generate_weekly_report(datetime.now().date())
        elif report_type == "monthly":
            report_data = report_service.generate_monthly_report(datetime.now().year, datetime.now().month)
        else:
            report_data = report_service.generate_daily_report(datetime.now().date())
        result = email_service.send_report_email(report_data, [recipient])
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Report Scheduling
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@app.route("/api/schedules")
def get_schedules():
    try:
        result = report_service.get_report_schedules()
        return jsonify(_convert_to_native_types(result))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/schedules", methods=["POST"])
def create_schedule():
    data = request.get_json() or {}
    try:
        result = report_service.add_report_schedule(data)
        return jsonify(_convert_to_native_types(result)), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/schedules/<schedule_id>", methods=["DELETE"])
def delete_schedule(schedule_id):
    try:
        result = scheduler.remove_schedule(schedule_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/schedules/<schedule_id>/toggle", methods=["PATCH"])
def toggle_schedule(schedule_id):
    data   = request.get_json() or {}
    active = data.get("active", True)
    try:
        result = scheduler.toggle_schedule(schedule_id, active)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/schedules/<schedule_id>/execute", methods=["POST"])
def execute_schedule(schedule_id):
    try:
        result = scheduler.execute_schedule_now(schedule_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Cost Analysis
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@app.route("/api/cost/config")
def get_cost_config():
    try:
        return jsonify(_convert_to_native_types(cost_service.get_config()))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/cost/config", methods=["PUT"])
def update_cost_config():
    data = request.get_json() or {}
    try:
        return jsonify(_convert_to_native_types(cost_service.update_config(data)))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/cost/operational")
def get_operational_cost():
    try:
        return jsonify(_convert_to_native_types(cost_service.calculate_operational_costs()))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/cost/roi")
def get_roi():
    try:
        return jsonify(_convert_to_native_types(cost_service.calculate_roi()))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/cost/resource-utilization")
def get_resource_utilization():
    try:
        return jsonify(_convert_to_native_types(cost_service.get_resource_utilization()))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/cost/complete-analysis")
def get_complete_cost_analysis():
    try:
        return jsonify(_convert_to_native_types(cost_service.get_complete_analysis()))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Email Service
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@app.route("/api/email/test")
def test_email():
    try:
        result = email_service.test_email_connection()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/email/config")
def get_email_config():
    cfg = email_service.config.copy()
    cfg.pop("password", None)
    cfg.pop("sender_password", None)
    return jsonify(cfg)


@app.route("/api/violations/alert", methods=["POST"])
def send_violation_alert():
    data = request.get_json() or {}
    try:
        if not email_service.config.get("enabled"):
            return jsonify({"status": "skipped", "message": "Email service disabled"})
        violation_data = {
            "class_name": data.get("class_name",  "Unknown"),
            "confidence": data.get("confidence",  0.0),
            "timestamp":  data.get("timestamp",   datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            "camera_id":  data.get("camera_id",   "CAM-001"),
            "location":   data.get("location",    "Main Camera"),
        }
        recipient_email = data.get("recipient_email")
        recipients = [recipient_email] if recipient_email else None
        result = email_service.send_violation_alert(violation_data=violation_data, recipients=recipients, snapshot_path=data.get("snapshot_path"))
        return jsonify(result) if result.get("status") == "success" else (jsonify(result), 400)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/email/alert", methods=["POST"])
def send_email_alert_compat():
    return send_violation_alert()


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Advanced Email Reporting
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@app.route("/api/email/send-report", methods=["POST"])
def send_report_advanced():
    if not HAS_EMAIL_REPORTING:
        return jsonify({"error": "Email Reporting module not available"}), 503
    data = request.get_json() or {}
    try:
        result = advanced_email_reporter.send_scheduled_report(
            report_type=data.get("report_type", "daily"),
            template_type=data.get("template_type", "summary"),
            recipients=[data.get("recipient_email", "")],
            include_csv=True, include_pdf=data.get("include_pdf", False)
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/email/schedule-report", methods=["POST"])
def schedule_report():
    if not HAS_EMAIL_REPORTING:
        return jsonify({"error": "Email Reporting module not available"}), 503
    data = request.get_json() or {}
    try:
        schedule = schedule_manager.add_schedule(
            report_type=data.get("report_type", "daily"), template_type=data.get("template_type", "summary"),
            recipient=data.get("recipient_email", ""), schedule_type=data.get("schedule_type", "daily"),
            day_of_week=data.get("day_of_week"), day_of_month=data.get("day_of_month"), time=data.get("time", "08:00")
        )
        return jsonify(schedule)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/email/schedules")
def get_email_schedules():
    if not HAS_EMAIL_REPORTING:
        return jsonify({"error": "Email Reporting module not available"}), 503
    try:
        return jsonify(schedule_manager.get_schedules())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/email/schedules/<schedule_id>", methods=["DELETE"])
def delete_email_schedule(schedule_id):
    if not HAS_EMAIL_REPORTING:
        return jsonify({"error": "Email Reporting module not available"}), 503
    try:
        return jsonify(schedule_manager.delete_schedule(schedule_id))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/email/templates")
def get_email_templates():
    if not HAS_EMAIL_REPORTING:
        return jsonify({"error": "Email Reporting module not available"}), 503
    return jsonify({"templates": [
        {"name": "summary",     "description": "Executive summary with key metrics and recommendations"},
        {"name": "detailed",    "description": "Detailed report with charts and comprehensive analysis"},
        {"name": "compliance",  "description": "Compliance-focused report for regulatory requirements"},
        {"name": "operational", "description": "Operational metrics for security teams"}
    ]})


@app.route("/api/detections/summary")
def get_detections_summary():
    try:
        if not os.path.exists(csv_file):
            return jsonify({
                "total": 0, "violations": 0, 
                "total_detections": 0, "total_violations": 0,
                "average_confidence": 0, "top_class": "N/A"
            })
        df = pd.read_csv(csv_file)
        if df.empty:
            return jsonify({
                "total": 0, "violations": 0, 
                "total_detections": 0, "total_violations": 0,
                "average_confidence": 0, "top_class": "N/A"
            })
            
        total = len(df)
        violations_df = df[df["Restricted Area Violation"] == "Yes"]
        violations = len(violations_df)
        avg_conf = df["Confidence"].mean() if not df.empty else 0
        top_class = df["Class"].mode().iloc[0] if not df["Class"].empty else "N/A"
        
        return jsonify({
            "total": total,
            "violations": violations,
            "total_detections": total,
            "total_violations": violations,
            "average_confidence": float(avg_conf),
            "top_class": top_class
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/detections/recent")
def get_recent_detections_api():
    limit = request.args.get("limit", 100, type=int)
    try:
        if not os.path.exists(csv_file):
            return jsonify({"detections": []})
        df = pd.read_csv(csv_file)
        if df.empty:
            return jsonify({"detections": []})
        recent = df.tail(limit).to_dict('records')
        return jsonify({"detections": recent})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/snapshots-count")
def get_snapshots_count():
    try:
        count = len([f for f in os.listdir(frames_dir) if f.endswith('.jpg')])
        return jsonify({"count": count})
    except Exception as e:
        return jsonify({"count": 0})

@app.route("/api/snapshots")
def get_snapshots_api():
    try:
        files = sorted([f for f in os.listdir(frames_dir) if f.endswith('.jpg')], reverse=True)
        snapshots = [{"id": f, "filename": f, "path": f"/static/frames/{f}"} for f in files]
        return jsonify({"snapshots": snapshots})
    except Exception as e:
        return jsonify({"snapshots": []})

@app.route("/api/snapshots/delete", methods=["POST"])
def delete_snapshot_api():
    data = request.get_json() or {}
    filename = data.get("id") or data.get("filename")
    if not filename:
        return jsonify({"error": "No filename provided"}), 400
    try:
        filepath = os.path.join(frames_dir, filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            return jsonify({"status": "deleted"})
        return jsonify({"error": "File not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/alerts/recent")
def get_recent_alerts_api():
    hours = request.args.get("hours", 24, type=int)
    try:
        if not os.path.exists(csv_file):
            return jsonify({"alerts": []})
        df = pd.read_csv(csv_file)
        if df.empty:
            return jsonify({"alerts": []})
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        recent_time = datetime.now() - timedelta(hours=hours)
        violations = df[(df["Restricted Area Violation"] == "Yes") & (df['Timestamp'] >= recent_time)]
        # Sort by timestamp descending
        violations = violations.sort_values(by='Timestamp', ascending=False)
        return jsonify({"alerts": violations.to_dict('records')})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─────────────────────────────────────────────────
# Advanced Analytics
# ─────────────────────────────────────────────────
@app.route("/api/analytics/predictive/forecast")
def get_forecast():
    if not HAS_ADVANCED_ANALYTICS:
        return jsonify({"error": "Advanced analytics not available"}), 503
    days_ahead = request.args.get("days_ahead", 7, type=int)
    try:
        result = advanced_analytics.forecast_detections(days_ahead=days_ahead)
        return jsonify(_convert_to_native_types(result))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/analytics/predictive/trend")
def get_predictive_trend():
    if not HAS_ADVANCED_ANALYTICS:
        return jsonify({"error": "Advanced analytics not available"}), 503
    days = request.args.get("days", 30, type=int)
    try:
        detector = PredictiveAnalytics(csv_file)
        return jsonify(_convert_to_native_types(detector.get_trend_analysis(days=days)))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/analytics/anomalies/detect", methods=["POST"])
def detect_anomalies_endpoint():
    if not HAS_ADVANCED_ANALYTICS:
        return jsonify({"error": "Advanced analytics not available"}), 503
    data   = request.get_json() or {}
    method = data.get("method", "zscore")
    try:
        detector = AnomalyDetection(csv_file)
        return jsonify(_convert_to_native_types(detector.detect_anomalies(method=method)))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/analytics/anomalies/behavioral", methods=["POST"])
def detect_behavioral_anomalies_endpoint():
    if not HAS_ADVANCED_ANALYTICS:
        return jsonify({"error": "Advanced analytics not available"}), 503
    try:
        detector = AnomalyDetection(csv_file)
        return jsonify(_convert_to_native_types(detector.detect_behavioral_anomalies()))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/analytics/kpis/advanced")
def get_advanced_kpis():
    if not HAS_ADVANCED_ANALYTICS:
        return jsonify({"error": "Advanced analytics not available"}), 503
    try:
        analyzer = StatisticalAnalyzer(csv_file)
        return jsonify(_convert_to_native_types(analyzer.calculate_kpis()))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/analytics/correlation")
def get_correlation():
    if not HAS_ADVANCED_ANALYTICS:
        return jsonify({"error": "Advanced analytics not available"}), 503
    try:
        analyzer = StatisticalAnalyzer(csv_file)
        return jsonify(_convert_to_native_types(analyzer.get_correlation_analysis()))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/analytics/percentiles")
def get_percentiles():
    if not HAS_ADVANCED_ANALYTICS:
        return jsonify({"error": "Advanced analytics not available"}), 503
    try:
        analyzer = StatisticalAnalyzer(csv_file)
        return jsonify(_convert_to_native_types(analyzer.get_percentile_analysis()))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Chart Data (for web dashboard)
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@app.route("/api/analytics/charts/class-distribution")
def get_class_distribution():
    try:
        df = pd.read_csv(csv_file)
        if df.empty:
            return jsonify({"data": []})
        counts = df['Class'].value_counts()
        data = [{"class": k, "count": int(v)} for k, v in counts.items()]
        return jsonify({"data": data})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/analytics/charts/violation-trend")
def get_violation_trend():
    days = request.args.get("days", 7, type=int)
    try:
        df = pd.read_csv(csv_file)
        if df.empty:
            return jsonify({"labels": [], "violations": [], "detections": []})
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        end_date   = datetime.now().date()
        date_range = [end_date - timedelta(days=days - 1 - i) for i in range(days)]
        labels     = [d.strftime('%Y-%m-%d') for d in date_range]
        vio_day    = df[df['Restricted Area Violation'] == 'Yes'].groupby(df['Timestamp'].dt.date).size()
        det_day    = df.groupby(df['Timestamp'].dt.date).size()
        
        data = []
        for d in date_range:
            data.append({
                "label": d.strftime('%Y-%m-%d'),
                "value": int(det_day.get(d, 0)),
                "violations": int(vio_day.get(d, 0)),
                "count": int(det_day.get(d, 0)) # For backward compatibility
            })
            
        return jsonify({"data": data, "labels": labels, "violations": [int(vio_day.get(d, 0)) for d in date_range]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/analytics/charts/confidence-by-class")
def get_confidence_by_class():
    try:
        df = pd.read_csv(csv_file)
        if df.empty:
            return jsonify({"labels": [], "data": []})
        avg_conf = (df.groupby('Class')['Confidence'].mean() * 100).sort_values(ascending=True)
        return jsonify({"labels": avg_conf.index.tolist(), "data": [round(v, 2) for v in avg_conf.values.tolist()]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/analytics/charts/hourly-activity")
def get_hourly_activity():
    try:
        df = pd.read_csv(csv_file)
        if df.empty:
            return jsonify({"labels": [], "detections": [], "violations": []})
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        df['Hour']      = df['Timestamp'].dt.hour
        hourly_det = df.groupby('Hour').size()
        hourly_vio = df[df['Restricted Area Violation'] == 'Yes'].groupby('Hour').size()
        
        data = []
        for h in range(24):
            data.append({
                "label": f"{h:02d}:00",
                "value": int(hourly_det.get(h, 0)),
                "violations": int(hourly_vio.get(h, 0)),
                "count": int(hourly_det.get(h, 0))
            })
            
        return jsonify({"data": data, "labels": [f"{h:02d}:00" for h in range(24)]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/analytics/charts/violation-status")
def get_violation_status():
    try:
        df = pd.read_csv(csv_file)
        if df.empty:
            return jsonify({"labels": [], "data": [], "colors": []})
        v = len(df[df['Restricted Area Violation'] == 'Yes'])
        s = len(df[df['Restricted Area Violation'] == 'No'])
        return jsonify({"labels": ["Violations", "Safe"], "data": [v, s], "colors": ["#ef4444", "#22c55e"]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/analytics/stats")
def get_analytics_stats():
    try:
        df = pd.read_csv(csv_file)
        if df.empty:
            return jsonify({"total_detections": 0, "total_violations": 0, "total_safe": 0, "violation_rate": 0, "avg_confidence": 0, "top_class": "-"})
        total = len(df)
        v     = len(df[df['Restricted Area Violation'] == 'Yes'])
        return jsonify({
            "total_detections": total, "total_violations": v, "total_safe": total - v,
            "violation_rate":   round(v / total * 100, 2) if total > 0 else 0,
            "avg_confidence":   round(df['Confidence'].mean() * 100, 2),
            "top_class":        df['Class'].mode().iloc[0] if not df.empty else "-"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Activity Feed
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@app.route("/api/activity/feed")
def get_activity_feed():
    limit      = request.args.get("limit", 50, type=int)
    event_type = request.args.get("event_type")
    try:
        events = activity_feed[:limit]
        if event_type:
            events = [e for e in events if e.get("type") == event_type]
        return jsonify({"events": events, "total_count": len(activity_feed), "displayed_count": len(events)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/activity/sync", methods=["POST"])
def sync_activity():
    try:
        count = refresh_activity_feed()
        return jsonify({"success": True, "total_events": count, "message": f"Activity feed synced with {count} events"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/activity/detections")
def get_detection_activity():
    limit = request.args.get("limit", 100, type=int)
    try:
        df = pd.read_csv(csv_file)
        if df.empty:
            return jsonify({"events": [], "total_count": 0})
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        df = df.sort_values('Timestamp', ascending=False)
        events = []
        for _, row in df.head(limit).iterrows():
            events.append({"id": str(len(events) + 1),
                           "timestamp":    row['Timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                           "type":         "detection",
                           "class":        row['Class'],
                           "confidence":   round(float(row['Confidence']) * 100, 2),
                           "is_violation": row['Restricted Area Violation'] == "Yes"})
        return jsonify({"events": events, "total_count": len(df), "displayed_count": len(events)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# System Health
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@app.route("/api/health")
def health_check():
    return jsonify({
        "status": "healthy", "timestamp": datetime.now().isoformat(),
        "camera_active": getattr(app, "camera_active", False),
        "alert_active": getattr(app, "alert_active", False),
        "services": {
            "analytics": "operational", "reports": "operational", "cost_analysis": "operational",
            "email":     "operational" if email_service.config.get("enabled") else "disabled",
            "scheduler": "operational" if scheduler.scheduler.running else "stopped"
        }
    })


@app.route("/api/health/detailed")
def get_detailed_health():
    try:
        cpu   = psutil.cpu_percent(interval=1)
        mem   = psutil.virtual_memory()
        disk  = psutil.disk_usage('/')
        net   = psutil.net_io_counters()
        proc  = psutil.Process()
        try:    threads = proc.num_threads()
        except: threads = 0
        try:    ofiles = len(proc.open_files())
        except: ofiles = 0
        try:
            with open(CAMERAS_FILE, 'r') as f: cams = json.load(f).get("cameras", [])
            cam_count  = len(cams)
            online     = sum(1 for c in cams if c.get("status") == "online")
        except:
            cam_count = online = 0
        uptime = (datetime.now() - system_start_time).total_seconds()
        return jsonify({
            "status":              "healthy" if cpu < 90 and mem.percent < 90 else "warning",
            "timestamp":           datetime.now().isoformat(),
            "cpu_percent":         cpu, "memory_percent": mem.percent, "disk_percent": disk.percent,
            "network_connected":   True,
            "uptime_formatted":    str(timedelta(seconds=int(uptime))),
            "active_threads":      threads, "open_files": ofiles,
            "python_version":      f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "cpu_count":           psutil.cpu_count(),
            "memory_used_gb":      round(mem.used  / (1024**3), 2),
            "memory_total_gb":     round(mem.total / (1024**3), 2),
            "disk_used_gb":        round(disk.used  / (1024**3), 2),
            "disk_total_gb":       round(disk.total / (1024**3), 2),
            "bytes_sent_mb":       round(net.bytes_sent / (1024**2), 2),
            "bytes_recv_mb":       round(net.bytes_recv / (1024**2), 2),
            "process_memory_mb":   round(proc.memory_info().rss / (1024**2), 2),
            "process_cpu_percent": proc.cpu_percent(interval=0.5),
            "camera_count":        cam_count, "online_cameras": online, "offline_cameras": cam_count - online
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/health/cameras")
def get_camera_health():
    try:
        with open(CAMERAS_FILE, 'r') as f:
            cams = json.load(f).get("cameras", [])
        return jsonify({
            "cameras":       [{"id": c.get("id"), "name": c.get("name"), "location": c.get("location"),
                               "status": c.get("status", "unknown"), "enabled": c.get("enabled", True),
                               "last_active": c.get("last_active"), "url": c.get("url")} for c in cams],
            "total_count":   len(cams),
            "online_count":  sum(1 for c in cams if c.get("status") == "online"),
            "offline_count": sum(1 for c in cams if c.get("status") != "online")
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/health/uptime")
def get_uptime():
    uptime = (datetime.now() - system_start_time).total_seconds()
    return jsonify({
        "start_time":       system_start_time.isoformat(),
        "uptime_seconds":   int(uptime),
        "uptime_formatted": str(timedelta(seconds=int(uptime))),
        "uptime_days":      int(uptime // 86400),
        "uptime_hours":     int((uptime % 86400) // 3600),
        "uptime_minutes":   int((uptime % 3600) // 60)
    })


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Camera Management
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def load_cameras():
    try:
        with open(CAMERAS_FILE, 'r') as f:
            return json.load(f).get("cameras", [])
    except:
        return []


def save_cameras(cameras):
    with open(CAMERAS_FILE, 'w') as f:
        json.dump({"cameras": cameras}, f, indent=2)


def generate_camera_id():
    return f"cam_{uuid.uuid4().hex[:8]}"


@app.route("/api/cameras/start", methods=["POST"])
def start_camera_feed():
    global global_cap
    with camera_lock:
        if not global_cap:
            # Note: For some platforms, cv2.CAP_DSHOW might be needed, using default and falling back
            global_cap = cv2.VideoCapture(0)
            if global_cap.isOpened():
                global_cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                global_cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                app.camera_active = True
                return jsonify({"success": True, "message": "Camera started"})
            else:
                global_cap = None
                app.camera_active = False
                return jsonify({"error": "Failed to open camera"}), 500
        app.camera_active = True
        return jsonify({"success": True, "message": "Camera already running"})


@app.route("/api/cameras/stop", methods=["POST"])
def stop_camera_feed():
    global global_cap
    with camera_lock:
        app.camera_active = False
        if global_cap:
            global_cap.release()
            global_cap = None
    return jsonify({"success": True, "message": "Camera stopped"})


@app.route("/api/video_feed")
def video_feed_route():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/api/camera_settings', methods=['POST'])
def set_camera_settings():
    data = request.json
    if not data: return jsonify({"error": "No data"}), 400
    if "conf_threshold" in data:
        camera_settings["conf_threshold"] = float(data["conf_threshold"])
    if "detect_classes" in data:
        camera_settings["detect_classes"] = data["detect_classes"]
    if "alert_classes" in data:
        camera_settings["alert_classes"] = data["alert_classes"]
    return jsonify({"success": True, "settings": camera_settings})


@app.route("/api/cameras")
def get_all_cameras():
    try:
        cameras = load_cameras()
        return jsonify({"cameras": cameras, "total_count": len(cameras)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/cameras", methods=["POST"])
def add_camera():
    config = request.get_json() or {}
    try:
        cameras = load_cameras()
        if any(c.get("name") == config.get("name") for c in cameras):
            return jsonify({"error": "Camera with this name already exists"}), 400
        new_cam = {
            "id": generate_camera_id(), "name": config.get("name", ""), "url": config.get("url", ""),
            "enabled": config.get("enabled", True), "resolution": config.get("resolution", "640x480"),
            "fps": config.get("fps", 20), "location": config.get("location", ""),
            "detection_classes": config.get("detection_classes", []), "alert_classes": config.get("alert_classes", []),
            "created_at": datetime.now().isoformat(), "last_active": None, "status": "offline"
        }
        cameras.append(new_cam)
        save_cameras(cameras)
        add_activity_event("camera_added", {"camera_id": new_cam["id"], "camera_name": new_cam["name"]})
        return jsonify({"success": True, "camera": new_cam, "message": f"Camera '{new_cam['name']}' added"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/cameras/<camera_id>")
def get_camera(camera_id):
    try:
        camera = next((c for c in load_cameras() if c.get("id") == camera_id), None)
        if not camera:
            return jsonify({"error": "Camera not found"}), 404
        return jsonify({"camera": camera})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/cameras/<camera_id>", methods=["PUT"])
def update_camera(camera_id):
    config = request.get_json() or {}
    try:
        cameras = load_cameras()
        idx = next((i for i, c in enumerate(cameras) if c.get("id") == camera_id), None)
        if idx is None:
            return jsonify({"error": "Camera not found"}), 404
        if any(c.get("name") == config.get("name") and c.get("id") != camera_id for c in cameras):
            return jsonify({"error": "Camera with this name already exists"}), 400
        cameras[idx].update({k: config.get(k, cameras[idx].get(k)) for k in
                              ["name","url","enabled","resolution","fps","location","detection_classes","alert_classes"]})
        save_cameras(cameras)
        add_activity_event("camera_updated", {"camera_id": camera_id, "camera_name": cameras[idx]["name"]})
        return jsonify({"success": True, "camera": cameras[idx], "message": "Camera updated"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/cameras/<camera_id>", methods=["DELETE"])
def delete_camera(camera_id):
    try:
        cameras = load_cameras()
        idx = next((i for i, c in enumerate(cameras) if c.get("id") == camera_id), None)
        if idx is None:
            return jsonify({"error": "Camera not found"}), 404
        deleted = cameras.pop(idx)
        save_cameras(cameras)
        add_activity_event("camera_deleted", {"camera_id": camera_id, "camera_name": deleted.get("name")})
        return jsonify({"success": True, "message": f"Camera '{deleted.get('name')}' deleted"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# User Activity
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def load_user_activity():
    try:
        with open(USER_ACTIVITY_FILE, 'r') as f:
            return json.load(f).get("activities", [])
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_user_activity(activities):
    with open(USER_ACTIVITY_FILE, 'w') as f:
        json.dump({"activities": activities}, f, indent=2)


def log_activity(user, action, details="", ip_address="", status="success"):
    activity = {
        "id": uuid.uuid4().hex[:8], "timestamp": datetime.now().isoformat(),
        "user": user, "action": action, "details": details,
        "ip_address": ip_address, "status": status
    }
    activities = load_user_activity()
    activities.insert(0, activity)
    if len(activities) > 1000:
        activities = activities[:1000]
    save_user_activity(activities)
    add_activity_event("user_activity", {"user": user, "action": action, "status": status})
    return activity


@app.route("/api/users/activity")
def get_user_activity():
    limit  = request.args.get("limit", 100, type=int)
    user   = request.args.get("user")
    action = request.args.get("action")
    try:
        activities = load_user_activity()
        if user:   activities = [a for a in activities if a.get("user")   == user]
        if action: activities = [a for a in activities if a.get("action") == action]
        shown = activities[:limit]
        return jsonify({"activities": shown, "total_count": len(load_user_activity()), "displayed_count": len(shown)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/users/activity", methods=["POST"])
def log_user_activity():
    data = request.get_json() or {}
    try:
        activity = log_activity(user=data.get("user",""), action=data.get("action",""),
                                details=data.get("details",""), ip_address=data.get("ip_address",""),
                                status=data.get("status","success"))
        return jsonify({"success": True, "activity": activity, "message": "Activity logged"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/users/stats")
def get_user_stats():
    try:
        activities = load_user_activity()
        if not activities:
            return jsonify({"total_users": 0, "total_actions": 0, "active_today": 0, "unique_ips": 0})
        unique_users = set(a.get("user") for a in activities if a.get("user"))
        unique_ips   = set(a.get("ip_address") for a in activities if a.get("ip_address"))
        cutoff       = (datetime.now() - timedelta(hours=24)).isoformat()
        active_today = set(a.get("user") for a in activities if a.get("timestamp","") >= cutoff and a.get("user"))
        user_actions = [a for a in activities if a.get("user") and a.get("user") != "system"]
        return jsonify({"total_users": len(unique_users), "total_actions": len(user_actions),
                        "active_today": len(active_today), "unique_ips": len(unique_ips),
                        "timestamp": datetime.now().isoformat()})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# API Info
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@app.route("/api/info")
def api_info():
    return jsonify({
        "name": "Real-Time Restricted Area Monitoring System API",
        "version": "2.0.0", "framework": "Flask + Flask-SocketIO",
        "description": "Advanced Business Intelligence & Reporting API",
        "features": {
            "analytics":         ["GET /api/analytics/kpis/mttr","GET /api/analytics/kpis/false-positive-rate","GET /api/analytics/kpis/coverage","GET /api/analytics/executive-summary","GET /api/analytics/trend-analysis","GET /api/analytics/dashboard"],
            "reports":           ["GET /api/reports/daily","GET /api/reports/weekly","GET /api/reports/monthly","GET /api/reports/compliance/<type>","POST /api/reports/send-email"],
            "scheduling":        ["GET /api/schedules","POST /api/schedules","DELETE /api/schedules/<id>","PATCH /api/schedules/<id>/toggle","POST /api/schedules/<id>/execute"],
            "cost_analysis":     ["GET /api/cost/config","PUT /api/cost/config","GET /api/cost/operational","GET /api/cost/roi","GET /api/cost/resource-utilization","GET /api/cost/complete-analysis"],
            "email":             ["GET /api/email/test","GET /api/email/config"],
            "advanced_analytics":["GET /api/analytics/predictive/forecast","GET /api/analytics/predictive/trend","POST /api/analytics/anomalies/detect","POST /api/analytics/anomalies/behavioral","GET /api/analytics/kpis/advanced","GET /api/analytics/correlation","GET /api/analytics/percentiles"],
            "advanced_email":    ["POST /api/email/send-report","POST /api/email/schedule-report","GET /api/email/schedules","DELETE /api/email/schedules/<id>","GET /api/email/templates"],
            "activity_feed":     ["GET /api/activity/feed","GET /api/activity/detections","POST /api/activity/sync"],
            "system_health":     ["GET /api/health","GET /api/health/detailed","GET /api/health/cameras","GET /api/health/uptime"],
            "camera_management": ["GET /api/cameras","POST /api/cameras","GET /api/cameras/<id>","PUT /api/cameras/<id>","DELETE /api/cameras/<id>"],
            "user_activity":     ["GET /api/users/activity","POST /api/users/activity","GET /api/users/stats"],
            "websocket_events":  ["detection_update","data_update","activity_update"]
        }
    })


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Entry Point
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
if __name__ == "__main__":
    print("\n" + "="*60)
    print("ðŸš€ Starting Flask Backend Server")
    print("="*60)
    print("ðŸ“ Server:    http://localhost:8000")
    print("ðŸ” API Info:  http://localhost:8000/api/info")
    print("ðŸ“Š Dashboard: http://localhost:8000/data")
    print("ðŸ“¸ Snapshots: http://localhost:8000/snapshots")
    print("="*60 + "\n")
    socketio.run(app, host="0.0.0.0", port=8000, debug=False, allow_unsafe_werkzeug=True)
