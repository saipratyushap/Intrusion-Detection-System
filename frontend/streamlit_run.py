import os
import requests

# Set environment variables for stability on macOS
os.environ["STREAMLIT_WATCHER_TYPE"] = "none"
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["OMP_NUM_THREADS"] = "1"

import streamlit as st
import cv2
import numpy as np
import pandas as pd
from ultralytics import YOLO
import threading
import base64
import random
from pydantic import BaseModel
import smtplib
import email.mime.text as mime_text
import email.mime.multipart as mime_multipart
import secrets
import string
from datetime import datetime, timedelta
import time
import pygame
import hashlib
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.image import MIMEImage
import ssl

# API Configuration
API_URL = "http://127.0.0.1:8000"

def log_user_action(user, action, details=""):
    """Log user action to the backend API"""
    try:
        requests.post(f"{API_URL}/api/users/activity", json={
            "user": user,
            "action": action,
            "details": details,
            "ip_address": "127.0.0.1",
            "status": "success"
        }, timeout=10)
    except Exception as e:
        print(f"Failed to log activity: {e}")
from pathlib import Path
from collections import Counter
import plotly.graph_objects as go
import plotly.express as px

# Set page config as the first Streamlit command
st.set_page_config(
    page_title="Real-Time Intrusion Detection - ThirdEye", 
    page_icon=str(Path(__file__).parent / "static" / "favicon.png"),
    layout="wide", 
    initial_sidebar_state="expanded"
)

# Import enhanced analytics modules
try:
    from enhanced_analytics import show_enhanced_analytics
    HAS_ENHANCED_ANALYTICS = True
except ImportError:
    HAS_ENHANCED_ANALYTICS = False
    print("Warning: enhanced_analytics.py not found")

try:
    import enhanced_plotly_analytics as epa
    HAS_PLOTLY_ANALYTICS = True
except ImportError:
    HAS_PLOTLY_ANALYTICS = False
    print("Warning: enhanced_plotly_analytics.py not found")

# API Configuration for Email Reporting
API_BASE_URL = "http://localhost:8000"

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    print("Warning: requests library not found")

try:
    import sys
    sys.path.append(str(Path(__file__).parent.parent))
    from backend.advanced_email_reporting import EmailReportTemplate, ReportScheduleManager
    HAS_EMAIL_REPORTING = True
    # Initialize schedule manager globally for use in UI
    schedule_manager = ReportScheduleManager()
except ImportError:
    HAS_EMAIL_REPORTING = False
    print("Warning: Email reporting modules not available")
    schedule_manager = None

# Load environment variables
ENV_FILE = Path(__file__).parent.parent / ".env"

def load_env():
    """Load environment variables from .env file"""
    env_config = {}
    if ENV_FILE.exists():
        with open(ENV_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_config[key.strip()] = value.strip()
    return env_config

# Load env config
ENV_CONFIG = load_env()

# Email configuration from .env
EMAIL_ENABLED = ENV_CONFIG.get('EMAIL_ENABLED', 'false').lower() == 'true'
EMAIL_SMTP_SERVER = ENV_CONFIG.get('EMAIL_SMTP_SERVER', 'smtp.gmail.com')
EMAIL_SMTP_PORT = int(ENV_CONFIG.get('EMAIL_SMTP_PORT', 465))
EMAIL_SENDER_EMAIL = ENV_CONFIG.get('EMAIL_SENDER_EMAIL', '')
EMAIL_SENDER_PASSWORD = ENV_CONFIG.get('EMAIL_SENDER_PASSWORD', '')
EMAIL_RECIPIENT_EMAIL = ENV_CONFIG.get('EMAIL_RECIPIENT_EMAIL', '')

# API Helper Functions for Email Reporting

def call_api(endpoint: str, method: str = "GET", data: dict = None, params: dict = None) -> dict:
    """Make API call to backend with error handling"""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        if method == "GET":
            response = requests.get(url, params=params, timeout=60)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=60)
        elif method == "DELETE":
            response = requests.delete(url, timeout=60)
        else:
            return {"error": f"Unsupported method: {method}"}
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        return {"error": "Cannot connect to backend API. Is FastAPI running on port 8000?"}
    except requests.exceptions.Timeout:
        return {"error": "API request timeout"}
    except Exception as e:
        return {"error": str(e)}

# Email Reporting API Functions
def send_report_api(report_type: str, template_type: str, recipient_email: str, include_pdf: bool = False) -> dict:
    """Send report via backend"""
    return call_api("/api/email/send-report", method="POST", 
                   data={
                       "report_type": report_type,
                       "template_type": template_type,
                       "recipient_email": recipient_email,
                       "include_pdf": include_pdf
                   })

def schedule_report_api(report_type: str, template_type: str, recipient_email: str, 
                       schedule_type: str, time: str = "09:00") -> dict:
    """Schedule report via backend"""
    return call_api("/api/email/schedule-report", method="POST",
                   data={
                       "report_type": report_type,
                       "template_type": template_type,
                       "recipient_email": recipient_email,
                       "schedule_type": schedule_type,
                       "time": time
                   })

def get_email_schedules() -> dict:
    """Get scheduled reports from backend"""
    return call_api("/api/email/schedules")

def delete_email_schedule(schedule_id: str) -> dict:
    """Delete scheduled report from backend"""
    return call_api(f"/api/email/schedules/{schedule_id}", method="DELETE")

def execute_email_schedule(schedule_id: str) -> dict:
    """Execute a scheduled report immediately via backend"""
    return call_api(f"/api/schedules/{schedule_id}/execute", method="POST")

def get_email_templates() -> dict:
    """Get available email templates from backend"""
    return call_api("/api/email/templates")

# Activity Feed Functions
def get_user_activity_from_api(limit: int = 20) -> dict:
    """Get user activity from backend API"""
    try:
        url = f"{API_BASE_URL}/api/users/activity?limit={limit}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.json()
        return {"error": f"API returned status {response.status_code}"}
    except requests.exceptions.ConnectionError:
        return {"error": "Cannot connect to backend API"}
    except Exception as e:
        return {"error": str(e)}

def get_detection_activity_from_api(limit: int = 20) -> dict:
    """Get detection activity from backend API"""
    try:
        url = f"{API_BASE_URL}/api/activity/detections?limit={limit}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.json()
        return {"error": f"API returned status {response.status_code}"}
    except requests.exceptions.ConnectionError:
        return {"error": "Cannot connect to backend API"}
    except Exception as e:
        return {"error": str(e)}

USERS_FILE = str(Path(__file__).parent.parent / "data" / "users.json")

# Load users from file
def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

# Save users to file
def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f)

# OTP Configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = os.environ.get('EMAIL_SENDER_EMAIL', 'p.saipratyusha732@gmail.com')
SENDER_PASSWORD = os.environ.get('EMAIL_SENDER_PASSWORD', 'miduuotoblozqzqj')
OTP_EXPIRY_MINUTES = 5

def generate_otp(length=6):
    return ''.join(secrets.choice(string.digits) for _ in range(length))

def send_otp_email(recipient_email, otp):
    try:
        msg = mime_multipart.MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = recipient_email
        msg['Subject'] = f'Your OTP Code: {otp}'
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
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
        </body>
        </html>
        """
        msg.attach(mime_text.MIMEText(body, 'html'))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True, "OTP sent successfully"
    except Exception as e:
        return False, str(e)

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'otp_verified' not in st.session_state:
    st.session_state.otp_verified = False
if 'otp_sent' not in st.session_state:
    st.session_state.otp_sent = False
if 'otp_email' not in st.session_state:
    st.session_state.otp_email = ""
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'users' not in st.session_state:
    st.session_state.users = load_users()
if 'show_signup' not in st.session_state:
    st.session_state.show_signup = False

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_password(username, password):
    users = load_users()
    # Case-insensitive search for username
    username_lower = username.lower()
    for user_key in users.keys():
        if user_key.lower() == username_lower:
            return users[user_key] == hash_password(password)
    return False

def register_user(username, password):
    users = load_users()
    # Case-insensitive check for existing username
    username_lower = username.lower()
    for user_key in users.keys():
        if user_key.lower() == username_lower:
            return False  # Username already exists
    users[username] = hash_password(password)
    save_users(users)
    return True

# Helper for Logo Rendering
def get_base64_of_bin_file(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except:
        return ""

def get_img_with_href(local_img_path, target_width=250):
    bin_str = get_base64_of_bin_file(local_img_path)
    if bin_str:
        # Detect actual image format from base64 header
        if bin_str.startswith('iVBORw0KGgo'):
            img_format = 'png'
        elif bin_str.startswith('/9j/'):
            img_format = 'jpeg'
        else:
            img_format = local_img_path.split('.')[-1]
        return f'<div style="text-align: center; margin-bottom: 1rem;"><img src="data:image/{img_format};base64,{bin_str}" style="max-width: {target_width}px;" /></div>'
    return ""


def inject_custom_css(authenticated=True):
    """Inject custom CSS based on authentication state"""
    sidebar_display = "block" if authenticated else "none"
    header_display = "block" if authenticated else "none"
    
    css = f"""
    <style>
        /* Hide sidebar and header on auth pages */
        section[data-testid="stSidebar"] {{
            display: {sidebar_display} !important;
        }}
        header[data-testid="stHeader"] {{
            display: {header_display} !important;
        }}
        
        /* Force White Background and Theme */
        .stApp, [data-testid="stAppViewContainer"] {{
            background-color: #F8FAFC !important;
        }}
        
        /* Card & Form Styling */
        [data-testid="stForm"] {{
            background: white !important;
            padding: 2.5rem 2.5rem !important;
            border-radius: 20px !important;
            box-shadow: 0 10px 30px rgba(0,0,0,0.05) !important;
            border: 1px solid #E2E8F0 !important;
            margin-bottom: 2rem !important;
        }}
        
        /* Input Field Styling - Force White Everywhere */
        div[data-baseweb="input"], 
        div[data-baseweb="input"] > div, 
        input, 
        .stTextInput input, 
        .stTextInput [data-baseweb="input"] {{
            background-color: white !important;
            color: #2D3E50 !important;
            -webkit-text-fill-color: #2D3E50 !important;
        }}
        
        /* Specific selector for Streamlit's internal wrappers */
        div[data-baseweb="base-input"] {{
            background-color: white !important;
            border-radius: 8px !important;
            border: 1px solid #D1DBE5 !important;
        }}
        
        /* Ensure the form itself doesn't darken children */
        [data-testid="stForm"] div {{
            background-color: transparent;
        }}
        
        [data-testid="stForm"] {{
            background-color: white !important;
        }}
        
        /* Button Styling - Exact match */
        button:not([data-testid="baseButton-headerNoPadding"]), 
        .stButton > button {{
            color: white !important;
            background-color: #709138 !important;
            border-radius: 8px !important;
            border: none !important;
            padding: 0.6rem 1.2rem !important;
            font-weight: 700 !important;
            font-size: 1rem !important;
            transition: all 0.3s ease !important;
            width: 100% !important;
        }}
        button:not([data-testid="baseButton-headerNoPadding"]):hover, 
        .stButton > button:hover {{
            background-color: #5d7a2f !important;
            box-shadow: 0 4px 15px rgba(112, 145, 56, 0.3) !important;
            transform: translateY(-1px) !important;
        }}
        
        /* Password visibility toggle - keep it small and icon-only */
        button[kind="header"], 
        button[data-testid="baseButton-header"],
        button[data-testid="baseButton-headerNoPadding"] {{
            background: transparent !important;
            width: auto !important;
            padding: 0.25rem !important;
            min-width: unset !important;
        }}
        
        /* Additional selectors for password toggle in input containers */
        div[data-baseweb="input"] button,
        .stTextInput button {{
            background: transparent !important;
            width: auto !important;
            padding: 0.25rem 0.5rem !important;
            min-width: unset !important;
            color: #64748B !important;
            font-size: 0.875rem !important;
        }}
        
        div[data-baseweb="input"] button:hover,
        .stTextInput button:hover {{
            background: rgba(0,0,0,0.05) !important;
            color: #2D3E50 !important;
        }}
        
        /* Sidebar Styling */
        [data-testid="stSidebar"] {{
            background-color: #FFFFFF !important;
            border-right: 1px solid #E2E8F0 !important;
        }}
        
        /* Hide Plotly mode bar buttons (zoom, pan, etc.) */
        .modebar {{
            display: none !important;
        }}
        
        /* Ensure sidebar images display correctly */
        [data-testid="stSidebar"] img {{
            max-width: 100% !important;
            height: auto !important;
            display: block !important;
        }}
        
        /* Header Card for Dashboard */
        .app-header {{ 
            text-align: center; 
            padding: 2rem; 
            margin-bottom: 2rem; 
            background: #FFFFFF; 
            border-radius: 20px; 
            border: 1px solid #D1DBE5; 
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.05);
            position: relative;
            overflow: hidden;
        }}
        
        .welcome-header {{
            text-align: center;
            margin-bottom: 2rem;
            color: #2D3E50;
            font-size: 1.4rem;
            font-weight: 800;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
        }}
        
        /* Tabs Styling */
        .stTabs [data-baseweb="tab-list"] {{
            background-color: white;
            padding: 0.5rem;
            border-radius: 12px;
            border: 1px solid #E2E8F0;
        }}
        
        /* Section Headers with Vertical Bar */
        .section-header, .tab-section-header {{ 
            font-size: 1.45rem !important; 
            font-weight: 800 !important; 
            color: #709138 !important; 
            margin: 2rem 0 1.5rem 0 !important; 
            display: flex; 
            align-items: center; 
            gap: 0.75rem; 
            border-left: 6px solid #709138 !important; 
            padding-left: 1.25rem !important;
            line-height: 1 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.5px !important;
        }}
        
        .stat-card-custom {{
            background: white;
            border-radius: 15px;
            padding: 1.5rem;
            text-align: center;
            border: 1px solid #E2E8F0;
            transition: all 0.3s ease;
        }}
        
        .badge-pill-custom {{
            padding: 0.5rem 1.25rem;
            border-radius: 50px;
            font-size: 0.85rem;
            font-weight: 600;
        }}
        .badge-live-custom {{ background: rgba(34, 197, 94, 0.1); color: #22c55e; border: 1px solid rgba(34, 197, 94, 0.2); }}
        .badge-yolo-custom {{ background: rgba(124, 58, 237, 0.1); color: #7c3aed; border: 1px solid rgba(124, 58, 237, 0.2); }}
        .badge-secure-custom {{ background: rgba(0, 161, 201, 0.1); color: #00A1C9; border: 1px solid rgba(0, 161, 201, 0.2); }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

inject_custom_css(st.session_state.authenticated)

csv_file = str(Path(__file__).parent.parent / "data" / "detection_log.csv")
frames_dir = str(Path(__file__).parent.parent / "data" / "frames")
recordings_dir = str(Path(__file__).parent.parent / "data" / "recordings")
os.makedirs(frames_dir, exist_ok=True)
os.makedirs(recordings_dir, exist_ok=True)
if not os.path.exists(csv_file):
    pd.DataFrame(columns=["Timestamp", "Class", "Confidence", "Restricted Area Violation"]).to_csv(csv_file, index=False)

@st.cache_resource
def load_model():
    return YOLO(str(Path(__file__).parent.parent / "model" / "best.pt"))

model = load_model()
available_classes = list(model.names.values())

def generate_class_colors():
    return {model.names[class_id]: tuple(random.randint(0, 255) for _ in range(3)) for class_id in model.names}

class_colors = generate_class_colors()
restricted_area = None
object_entry_times = {}
# Email notification tracking
email_thread = None
last_email_time = {}
# Alert system tracking
alert_active = False
alert_thread = None

def send_violation_email_internal(class_name, confidence, snapshot_path=None):
    """Send email notification via backend API"""
    global EMAIL_ENABLED, EMAIL_RECIPIENT_EMAIL, API_BASE_URL
    
    print(f"🔍 send_violation_email_internal started for {class_name}")
    
    if not EMAIL_ENABLED:
        print(f"❌ Email is not enabled in .env")
        return False
        
    try:
        if not 'requests' in sys.modules and not HAS_REQUESTS:
             print("❌ requests library not found")
             return False

        # Prepare payload
        payload = {
            "class_name": class_name,
            "confidence": float(confidence),
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "camera_id": "CAM-001",
            "location": "Main Camera",
            "snapshot_path": str(snapshot_path) if snapshot_path and os.path.exists(snapshot_path) else None
        }
        
        # Add recipient if configured
        # Note: We don't send recipient_email to allow backend to use its full list from .env
        # payload["recipient_email"] = ... 
        
        print(f"🚀 Sending alert request to {API_BASE_URL}/api/email/alert")
        try:
            response = requests.post(f"{API_BASE_URL}/api/email/alert", json=payload, timeout=5)
            
            if response.status_code == 200:
                print(f"✅ Email alert sent successfully via backend")
                return True
            else:
                print(f"❌ Backend returned error: {response.status_code} - {response.text}")
                return False
        except Exception as conn_err:
             print(f"❌ Connection error to backend: {conn_err}")
             return False
            
    except Exception as e:
        print(f"❌ Error sending email alert: {e}")
        return False

def send_email_notification(class_name, confidence, snapshot_path=None):
    """Send email notification in a separate thread with optional snapshot"""
    global email_thread, last_email_time
    
    print(f"📧 send_email_notification called for {class_name}")
    
    # Rate limit: don't send more than 1 email per minute per class
    current_time = time.time()
    if class_name in last_email_time:
        if current_time - last_email_time[class_name] < 60:  # 60 seconds
            print(f"⏰ Rate limited: skipping email for {class_name} (last sent < 1 min ago)")
            return  # Skip if less than 1 minute since last email
    
    def email_worker():
        print(f"🔧 email_worker starting for {class_name}")
        if send_violation_email_internal(class_name, confidence, snapshot_path):
            print(f"✅ Email sent successfully for {class_name} violation")
            last_email_time[class_name] = current_time
        else:
            print(f"❌ Email sending failed for {class_name}")
    
    # Start email thread
    print(f"🚀 Starting email thread for {class_name}")
    thread = threading.Thread(target=email_worker, daemon=True)
    thread.start()

# Initialize pygame mixer only when needed
_pygame_initialized = False
def init_pygame_mixer():
    global _pygame_initialized
    if not _pygame_initialized:
        try:
            pygame.mixer.init()
            _pygame_initialized = True
        except Exception as e:
            print(f"Warning: Could not initialize PyGame mixer: {e}")
            _pygame_initialized = True  # Mark as attempted to avoid repeated failures

def play_alert_sound(sound_path):
    try:
        init_pygame_mixer()
        pygame.mixer.music.load(sound_path)
        pygame.mixer.music.play(-1)
        while alert_active:
            time.sleep(1)
        pygame.mixer.music.stop()
    except Exception as e:
        print(f"Audio playback error: {e}")
        pass

def start_alert(sound_path):
    global alert_active, alert_thread
    if not alert_active:
        alert_active = True
        alert_thread = threading.Thread(target=play_alert_sound, args=(sound_path,), daemon=True)
        alert_thread.start()

def stop_alert():
    global alert_active
    if alert_active:
        alert_active = False

def draw_roi(frame):
    global restricted_area
    h, w, _ = frame.shape
    center = (w // 2, h // 2)
    axes = (w // 4, h // 8)
    restricted_area = (center, axes)
    cv2.ellipse(frame, center, axes, 0, 0, 360, (0, 0, 255), 2)
    return frame

def is_near_restricted_area(box):
    if restricted_area:
        center, axes = restricted_area
        x1, y1, x2, y2 = box
        obj_center = ((x1 + x2) // 2, (y1 + y2) // 2)
        distance = np.linalg.norm(np.array(center) - np.array(obj_center))
        return distance < (min(axes) + 50)
    return False

def save_detection_data(class_name, confidence):
    data = {"Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Class": class_name, "Confidence": confidence, "Restricted Area Violation": "Yes"}
    df = pd.DataFrame([data])
    df.to_csv(csv_file, mode='a', header=False, index=False)

def update_frame(cap, conf_threshold, detect_classes, alert_classes_list):
    if not cap:
        return None, [], None
    
    ret, frame = cap.read()
    if not ret:
        return None, [], None
    
    results = model(frame, conf=conf_threshold, iou=0.3)
    annotated_frame = frame.copy()
    object_inside = False
    detected = []
    current_violator = None
    
    for result in results[0].boxes:
        class_id = int(result.cls)
        class_name = model.names[class_id]
        
        if class_name in detect_classes:
            detected.append(class_name)
            
            color = class_colors.get(class_name, (0, 255, 0))
            x1, y1, x2, y2 = map(int, result.xyxy[0])
            conf = result.conf[0]
            
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 3)
            cv2.putText(annotated_frame, f"{class_name} {conf:.2f}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            
            if is_near_restricted_area([x1, y1, x2, y2]):
                if class_name in alert_classes_list:
                    object_inside = True
                    current_violator = class_name
                    cv2.putText(annotated_frame, f"{class_name} in Restricted Area!", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                    
                    if class_name not in object_entry_times:
                        object_entry_times[class_name] = time.time()
                    
                    # Calculate elapsed time in restricted area
                    elapsed = time.time() - object_entry_times[class_name]
                    remaining = max(0, 2.0 - elapsed)
                    
                    if remaining > 0:
                         cv2.putText(annotated_frame, f"Alert in {remaining:.1f}s", (x1, y1 - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
                    
                    if elapsed > 2:
                        print(f"🚨 VIOLATION DETECTED: {class_name} with {conf:.2%} confidence")
                        save_detection_data(class_name, float(conf))
                        object_entry_times[class_name] = time.time()
                        # Capture and save snapshot for email
                        snapshot_path = save_frame(annotated_frame)
                        print(f"📸 Snapshot saved: {snapshot_path}")
                        # Send email notification with snapshot
                        print(f"📧 Sending email alert for {class_name}...")
                        send_email_notification(class_name, float(conf), snapshot_path)
                        print(f"✅ Email sent for {class_name}")
                        
                        # Visual confirmation on frame
                        cv2.putText(annotated_frame, "ALERT SENT!", (x1, y1 - 55), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    
    if object_inside:
        start_alert(str(Path(__file__).parent / "static" / "sounds" / "alert.wav"))
    else:
        stop_alert()
    
    annotated_frame = draw_roi(annotated_frame)
    return annotated_frame, detected, current_violator

def start_camera():
    cap = cv2.VideoCapture(0)
    if cap.isOpened():
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        return cap
    return None

def stop_camera(cap):
    if cap:
        cap.release()
        cv2.destroyAllWindows()

def save_frame(frame):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"frame_{ts}.jpg"
    filepath = os.path.join(frames_dir, filename)
    cv2.imwrite(filepath, frame)
    return filepath

# ============ Video Recording Functions ============

def get_video_writer(filepath, fps=20, width=640, height=480):
    """Initialize video writer for recording - macOS compatible with proper codec"""
    # For macOS compatibility, always use .avi format with MJPG codec
    filepath_fixed = filepath.replace('.mp4', '.avi')

    # Try MJPG codec first (most compatible with macOS)
    fourcc = cv2.VideoWriter_fourcc(*'MJPG')
    writer = cv2.VideoWriter(filepath_fixed, fourcc, fps, (width, height))

    if writer.isOpened():
        print(f"✓ Using MJPG codec (AVI format): {filepath_fixed}")
        st.session_state.current_recording_file = filepath_fixed
        return writer

    # Fallback to XVID if MJPG fails
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    writer = cv2.VideoWriter(filepath_fixed, fourcc, fps, (width, height))

    if writer.isOpened():
        print(f"✓ Using XVID codec (AVI format): {filepath_fixed}")
        st.session_state.current_recording_file = filepath_fixed
        return writer

    # Last resort - try MP4V codec
    fourcc = cv2.VideoWriter_fourcc(*'MP4V')
    writer = cv2.VideoWriter(filepath_fixed, fourcc, fps, (width, height))

    if writer.isOpened():
        print(f"✓ Using MP4V codec (AVI format): {filepath_fixed}")
        st.session_state.current_recording_file = filepath_fixed
        return writer

    print("❌ Failed to initialize video writer with any codec")
    return None


def init_video_writer(quality="Medium (720p)", fps=20):
    """Initialize video writer with quality and fps settings"""
    # Determine resolution based on quality
    if "Low" in quality:
        width, height = 640, 480
    elif "Medium" in quality:
        width, height = 1280, 720
    else:  # High
        width, height = 1920, 1080
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"recording_{timestamp}.avi"
    filepath = os.path.join(recordings_dir, filename)
    
    # Use the existing get_video_writer function
    return get_video_writer(filepath, fps, width, height)

def get_recordings():
    """Get list of recordings with metadata"""
    recordings = []
    if os.path.exists(recordings_dir):
        for f in sorted(os.listdir(recordings_dir), reverse=True):
            if f.endswith(('.mp4', '.avi', '.mov')):
                filepath = os.path.join(recordings_dir, f)
                if os.path.exists(filepath):
                    file_size = os.path.getsize(filepath)
                    # Get creation time
                    ctime = os.path.getctime(filepath)
                    recordings.append({
                        'name': f,
                        'path': filepath,
                        'size': file_size,
                        'created': datetime.fromtimestamp(ctime).strftime('%Y-%m-%d %H:%M:%S'),
                        'size_mb': file_size / (1024 * 1024)
                    })
    return recordings

def format_duration(seconds):
    """Format duration in seconds to readable format"""
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins}m {secs}s"
    else:
        hours = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        return f"{hours}h {mins}m"

def get_video_duration(filepath):
    """Get video duration in seconds using OpenCV"""
    try:
        cap = cv2.VideoCapture(filepath)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        cap.release()
        if fps > 0:
            return frame_count / fps
        return 0
    except:
        return 0

def delete_recording(filepath):
    """Delete a recording file"""
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
        return False
    except Exception as e:
        print(f"Error deleting recording: {e}")
        return False

if 'camera_active' not in st.session_state:
    st.session_state.camera_active = False
if 'cap' not in st.session_state:
    st.session_state.cap = None
if 'recording' not in st.session_state:
    st.session_state.recording = False
if 'detect_all' not in st.session_state:
    st.session_state.detect_all = True
if 'alert_all' not in st.session_state:
    st.session_state.alert_all = True
# Video recording session state
if 'video_recording' not in st.session_state:
    st.session_state.video_recording = False
if 'video_writer' not in st.session_state:
    st.session_state.video_writer = None
if 'current_recording_file' not in st.session_state:
    st.session_state.current_recording_file = None
if 'recording_start_time' not in st.session_state:
    st.session_state.recording_start_time = None
if 'recording_quality' not in st.session_state:
    st.session_state.recording_quality = "Medium (720p)"
if 'recording_fps' not in st.session_state:
    st.session_state.recording_fps = 20

# Real-time alerts tracking
if 'active_alerts' not in st.session_state:
    st.session_state.active_alerts = []


# ============ AUTHENTICATION PAGES ============

def login_page():
    # Centered Layout
    _, col_center, _ = st.columns([1, 2.5, 1])
    
    with col_center:
        # Logo Section - Base64 Rendering for absolute reliability
        current_dir = os.path.dirname(os.path.abspath(__file__))
        logo_path = os.path.join(current_dir, "static", "logo.jpg")
        logo_html = get_img_with_href(logo_path, 250)
        
        if logo_html:
            st.markdown(logo_html, unsafe_allow_html=True)
        else:
            # Fallback to URL if local file missing
            st.markdown(f'''
                <div style="display: flex; justify-content: center; margin-bottom: 2rem;">
                    <img src="https://raw.githubusercontent.com/psaipratyusha/Intrusion-Detection-System/main/frontend/static/logo.jpg" style="max-width: 250px;">
                </div>
            ''', unsafe_allow_html=True)
        
        # Titles
        st.markdown("""
            <div style="text-align: center; margin-bottom: 2.5rem; margin-top: 1.5rem;">
                <h1 style="color: #709138; font-weight: 800; font-size: 3.2rem; margin-bottom: 0.2rem; letter-spacing: -1.5px;">Intrusion Detection</h1>
                <p style="color: #64748B; font-size: 1.05rem; font-weight: 500;">Next-generation surveillance & monitoring</p>
            </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            st.markdown('<div class="welcome-header">🔐 Welcome Back</div>', unsafe_allow_html=True)
            
            # Username
            st.markdown('<label style="font-weight: 700; color: #475569; font-size: 0.95rem; margin-bottom: 0.4rem; display: block;">Username</label>', unsafe_allow_html=True)
            username = st.text_input("Username", key="login_username", label_visibility="collapsed")
            
            st.markdown('<div style="margin-top: 1.5rem;"></div>', unsafe_allow_html=True)
            
            # Password
            st.markdown('<label style="font-weight: 700; color: #475569; font-size: 0.95rem; margin-bottom: 0.4rem; display: block;">Password</label>', unsafe_allow_html=True)
            password = st.text_input("Password", type="password", key="login_password", label_visibility="collapsed")
            
            st.markdown('<div style="margin-top: 2.5rem;"></div>', unsafe_allow_html=True)
            
            submit = st.form_submit_button("Sign In Securely", use_container_width=True)
            
            if submit:
                if username and password:
                    if check_password(username, password):
                        st.session_state.authenticated = True
                        st.session_state.username = username
                        st.balloons()
                        st.success("Login Successful!")
                        log_user_action(username, "login_success", "User logged in via Streamlit")
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
                else:
                    st.error("Please enter credentials")
    
        # Footer
        st.markdown("""
            <div style="text-align: center; margin-top: 2.5rem; margin-bottom: 1rem; color: #64748B; font-size: 1rem; font-weight: 500;">
                New to the system?
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("Create Management Account", key="goto_signup", use_container_width=True):
            st.session_state.show_signup = True
            st.rerun()
        
        st.markdown('<div style="margin-top: 4rem;"></div>', unsafe_allow_html=True)

def signup_page():
    # Initialize signup state variables if not present
    if 'signup_step' not in st.session_state:
        st.session_state.signup_step = 'email'  # verify, details
    if 'signup_email' not in st.session_state:
        st.session_state.signup_email = ''
    if 'signup_otp' not in st.session_state:
        st.session_state.signup_otp = ''
    if 'signup_otp_time' not in st.session_state:
        st.session_state.signup_otp_time = None

    # Outer container for centering
    _, col_mid, _ = st.columns([1.2, 2, 1.2])
    
    with col_mid:
        # Logo Section - Base64 Rendering (same as login page)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        logo_path = os.path.join(current_dir, "static", "logo.jpg")
        logo_html = get_img_with_href(logo_path, 250)
        
        if logo_html:
            st.markdown(logo_html, unsafe_allow_html=True)
        else:
            # Fallback to URL if local file missing
            st.markdown(f'''
                <div style="display: flex; justify-content: center; margin-bottom: 2rem;">
                    <img src="https://raw.githubusercontent.com/psaipratyusha/Intrusion-Detection-System/main/frontend/static/logo.jpg" style="max-width: 250px;">
                </div>
            ''', unsafe_allow_html=True)
        
        # Titles (matching login page style)
        st.markdown("""
            <div style="text-align: center; margin-bottom: 2.5rem; margin-top: 1.5rem;">
                <h1 style="color: #709138; font-weight: 800; font-size: 3.2rem; margin-bottom: 0.2rem; letter-spacing: -1.5px;">Intrusion Detection</h1>
                <p style="color: #64748B; font-size: 1.05rem; font-weight: 500;">Next-generation surveillance & monitoring</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Step 1: Email Input
        if st.session_state.signup_step == 'email':
            with st.form("signup_email_form"):
                st.markdown("<h3>📧 Verify Email</h3>", unsafe_allow_html=True)
                email = st.text_input("Email Address", placeholder="your.name@example.com")
                submit = st.form_submit_button("Send Verification Code", use_container_width=True)
                
                if submit:
                    if email and "@" in email and "." in email:
                        # Check if user already exists (optional, but good practice)
                        # We don't have easy email->user mapping yet, so we skip for now 
                        # or we could iterate users if we stored emails. 
                        # For now, just send OTP.
                        
                        otp = generate_otp()
                        success, msg = send_otp_email(email, otp)
                        if success:
                            st.session_state.signup_otp = otp
                            st.session_state.signup_email = email
                            st.session_state.signup_step = 'verify'
                            st.session_state.signup_otp_time = datetime.now().isoformat()
                            st.success(f"Verification code sent to {email}")
                            st.rerun()
                        else:
                            st.error(f"Failed to send email: {msg}")
                    else:
                        st.error("Please enter a valid email address")

        # Step 2: OTP Verification
        elif st.session_state.signup_step == 'verify':
            with st.form("signup_verify_form"):
                st.markdown("<h3>🔢 Verify Code</h3>", unsafe_allow_html=True)
                st.markdown(f"Code sent to: **{st.session_state.signup_email}**")
                otp_input = st.text_input("Enter 6-Digit Code", placeholder="••••••", max_chars=6)
                
                col_s1, col_s2 = st.columns(2)
                with col_s1:
                    verify_submit = st.form_submit_button("Verify Email", use_container_width=True)
                with col_s2:
                    change_email = st.form_submit_button("Change Email", use_container_width=True)
                
                if verify_submit:
                    # Check expiry
                    otp_time = datetime.fromisoformat(st.session_state.signup_otp_time)
                    if datetime.now() - otp_time > timedelta(minutes=OTP_EXPIRY_MINUTES):
                        st.error("Code expired. Please request a new one.")
                        st.session_state.signup_step = 'email'
                        st.rerun()
                    elif otp_input == st.session_state.signup_otp:
                        st.success("Email Verified!")
                        st.session_state.signup_step = 'details'
                        st.rerun()
                    else:
                        st.error("Invalid verification code")
                
                if change_email:
                    st.session_state.signup_step = 'email'
                    st.rerun()

        # Step 3: Account Details
        elif st.session_state.signup_step == 'details':
            with st.form("signup_details_form"):
                st.markdown("<h3>📝 Account Details</h3>", unsafe_allow_html=True)
                st.info(f"Verified Email: {st.session_state.signup_email}")
                
                new_username = st.text_input("Choose Username", placeholder="e.g. jdoe")
                new_password = st.text_input("Choose Password", type="password", placeholder="At least 4 chars")
                confirm_password = st.text_input("Confirm Password", type="password", placeholder="Repeat password")
                
                st.markdown('<div style="margin-top: 1rem;"></div>', unsafe_allow_html=True)
                submit = st.form_submit_button("Complete Registration", use_container_width=True)
                
                if submit:
                    if new_username and new_password and confirm_password:
                        if new_password != confirm_password:
                            st.error("Passwords do not match")
                        elif len(new_password) < 4:
                            st.error("Password must be at least 4 characters")
                        else:
                            if register_user(new_username, new_password):
                                # Optionally save the email association here if we updated the backend
                                st.success("Registration Complete! Please login.")
                                log_user_action(new_username, "signup_success", f"User registered: {st.session_state.signup_email}")
                                st.session_state.show_signup = False
                                # Reset signup state
                                del st.session_state.signup_step
                                del st.session_state.signup_email
                                del st.session_state.signup_otp
                                del st.session_state.signup_otp_time
                                st.rerun()
                            else:
                                st.error("Username already registered")
                    else:
                        st.error("Please fill in all fields")

        # Bottom Actions centered
        st.markdown('<div style="margin-top: 2rem; text-align: center; color: #64748B; font-weight: 500;">Already registered?</div>', unsafe_allow_html=True)
        if st.button("Return to Secure Login", key="back_to_login_btn", use_container_width=True):
            st.session_state.show_signup = False
            # Clean up signup state
            if 'signup_step' in st.session_state: del st.session_state.signup_step
            if 'signup_email' in st.session_state: del st.session_state.signup_email
            if 'signup_otp' in st.session_state: del st.session_state.signup_otp
            if 'signup_otp_time' in st.session_state: del st.session_state.signup_otp_time
            st.rerun()

# ============ MAIN APP ============

def main_app():
    # Sidebar Logo and User Profile - Use Base64 encoding
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Try to use PNG with transparency first
    logo_path = os.path.join(current_dir, "static", "logo.png")
    if not os.path.exists(logo_path):
        logo_path = os.path.join(current_dir, "static", "logo.jpg")
    
    # Generate logo HTML explicitly
    try:
        if os.path.exists(logo_path):
            with open(logo_path, "rb") as f:
                logo_bytes = f.read()
            bin_str = base64.b64encode(logo_bytes).decode()
            
            # Determine mime type
            mime_type = "image/png" if logo_path.endswith(".png") else "image/jpeg"
            
            # For PNG, no mix-blend-mode needed. For JPG, keep it just in case.
            style = "max-width: 220px; display: block; border-radius: 4px;"
            if mime_type == "image/jpeg":
                 style += " mix-blend-mode: multiply;"
            
            sidebar_logo_html = f'''
                <div style="text-align: left; margin-bottom: 1.5rem;">
                    <img src="data:{mime_type};base64,{bin_str}" 
                         style="{style}">
                </div>
            '''
            st.sidebar.markdown(sidebar_logo_html, unsafe_allow_html=True)
        else:
            # Fallback to URL if file doesn't exist (this points to jpg so keep multiply)
            st.sidebar.markdown(f'''
                <div style="text-align: left; margin-bottom: 1.5rem;">
                    <img src="https://raw.githubusercontent.com/psaipratyusha/Intrusion-Detection-System/main/frontend/static/logo.jpg" 
                         style="max-width: 220px; mix-blend-mode: multiply; display: block; border-radius: 4px;">
                </div>
            ''', unsafe_allow_html=True)
    except Exception as e:
        print(f"Error loading logo: {e}")

    if st.session_state.get('username'):
        st.sidebar.markdown(f"""
        <div style="margin-bottom: 1.5rem;">
            <div style="color: #475569; font-size: 0.9rem; font-weight: 600;">User: {st.session_state.username}</div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.sidebar.button("Logout", key="logout_btn"):
            if st.session_state.get('username'):
                log_user_action(st.session_state.username, "logout", "User logged out")
            st.session_state.authenticated = False
            st.session_state.username = ""
            if st.session_state.cap:
                stop_camera(st.session_state.cap)
            st.session_state.cap = None
            st.session_state.camera_active = False
            st.session_state.recording = False
            st.rerun()
    
    st.sidebar.markdown("<br>", unsafe_allow_html=True)
    st.sidebar.markdown("### System Settings")

    col_detect_all, col_detect_none = st.sidebar.columns([1, 1])
    with col_detect_all:
        if st.button("All", key="detect_all_btn", use_container_width=True):
            st.session_state.detect_all = True
            st.rerun()
    with col_detect_none:
        if st.button("None", key="detect_none_btn", use_container_width=True):
            st.session_state.detect_all = False
            st.rerun()

    st.sidebar.markdown("**Objects to Detect**")
    detect_options = st.sidebar.multiselect("Objects to Detect", available_classes, default=available_classes if st.session_state.detect_all else [], label_visibility="collapsed")

    col_alert_all, col_alert_none = st.sidebar.columns([1, 1])
    with col_alert_all:
        if st.button("All", key="alert_all_btn", use_container_width=True):
            st.session_state.alert_all = True
            st.rerun()
    with col_alert_none:
        if st.button("None", key="alert_none_btn", use_container_width=True):
            st.session_state.alert_all = False
            st.rerun()

    st.sidebar.markdown("**Objects for Alert**")
    alert_options = st.sidebar.multiselect("Objects for Alert", available_classes, default=available_classes if st.session_state.alert_all else [], label_visibility="collapsed")

    st.sidebar.markdown("**Confidence Threshold**")
    conf_thresh = st.sidebar.slider("Confidence Threshold", 0.0, 1.0, 0.15, 0.05, label_visibility="collapsed")

    st.sidebar.markdown("<br>", unsafe_allow_html=True)
    st.sidebar.markdown("### Camera Controls")

    col_cam_start, col_cam_stop = st.sidebar.columns(2)
    with col_cam_start:
        if st.button("Start", key="camera_start_btn", use_container_width=True):
            if not st.session_state.camera_active:
                cap = start_camera()
                if cap:
                    st.session_state.cap = cap
                    st.session_state.camera_active = True
                    st.session_state.recording = True
                    st.rerun()
                else:
                    st.sidebar.error("Cannot access camera")
    
    with col_cam_stop:
        if st.button("Stop", key="camera_stop_btn", use_container_width=True):
            if st.session_state.camera_active:
                # Stop video recording if active
                if st.session_state.video_recording and st.session_state.video_writer:
                    st.session_state.video_writer.release()
                    st.session_state.video_writer = None
                    st.session_state.video_recording = False
                    if st.session_state.recording_start_time:
                        duration = time.time() - st.session_state.recording_start_time
                        st.success(f"Recording saved: {os.path.basename(st.session_state.current_recording_file)} ({format_duration(duration)})")
                    else:
                        st.success("Recording saved successfully")
                    st.session_state.current_recording_file = None
                    st.session_state.recording_start_time = None
                
                stop_camera(st.session_state.cap)
                st.session_state.cap = None
                st.session_state.camera_active = False
                st.session_state.recording = False
                st.rerun()

    if st.session_state.camera_active:
        st.sidebar.markdown('<div class="status-badge">Live</div>', unsafe_allow_html=True)
    else:
        st.sidebar.markdown('<div class="status-badge inactive">Offline</div>', unsafe_allow_html=True)

    # Video Recording Controls
    if st.session_state.camera_active:
        st.sidebar.markdown("<br>", unsafe_allow_html=True)
        st.sidebar.markdown("### Video Recording")
        
        # Recording Quality
        st.sidebar.markdown("**Recording Quality**")
        recording_quality = st.sidebar.selectbox(
            "Quality",
            ["Low (480p)", "Medium (720p)", "High (1080p)"],
            index=1,
            label_visibility="collapsed",
            key="recording_quality_select"
        )
        st.session_state.recording_quality = recording_quality
        
        # Recording FPS
        st.sidebar.markdown("**Recording FPS**")
        recording_fps = st.sidebar.slider(
            "FPS",
            5, 30, 20,
            label_visibility="collapsed",
            key="recording_fps_slider"
        )
        st.session_state.recording_fps = recording_fps
        
        st.sidebar.markdown("<br>", unsafe_allow_html=True)
        
        # Recording buttons
        col_rec_start, col_rec_stop = st.sidebar.columns(2)
        with col_rec_start:
            if st.button("⏺ Start", key="recording_start_btn", use_container_width=True, disabled=st.session_state.video_recording):
                # Initialize video writer
                video_writer = init_video_writer(
                    st.session_state.recording_quality,
                    st.session_state.recording_fps
                )
                if video_writer:
                    st.session_state.video_writer = video_writer
                    st.session_state.video_recording = True
                    st.session_state.recording_start_time = time.time()
                    st.sidebar.success("Recording started!")
                    st.rerun()
                else:
                    st.sidebar.error("Failed to start recording")
        
        with col_rec_stop:
            if st.button("⏹ Stop", key="recording_stop_btn", use_container_width=True, disabled=not st.session_state.video_recording):
                if st.session_state.video_recording and st.session_state.video_writer:
                    st.session_state.video_writer.release()
                    st.session_state.video_writer = None
                    st.session_state.video_recording = False
                    if st.session_state.recording_start_time:
                        duration = time.time() - st.session_state.recording_start_time
                        st.sidebar.success(f"Recording saved! ({int(duration)}s)")
                    st.session_state.current_recording_file = None
                    st.session_state.recording_start_time = None
                    st.rerun()
        
        # Show recording status
        if st.session_state.video_recording and st.session_state.recording_start_time:
            duration = int(time.time() - st.session_state.recording_start_time)
            st.sidebar.markdown(
                f'<div style="text-align: center; color: #dc2626; font-weight: 600; margin-top: 0.5rem;">🔴 Recording: {duration}s</div>',
                unsafe_allow_html=True
            )

    # Main Area
    # 1. Main Header Card
    st.markdown("""
        <div class="app-header">
            <h1 style="color: #709138; font-size: 3rem; font-weight: 800; margin-bottom: 0.5rem;">Real-Time Intrusion Detection</h1>
            <p style="color: #64748B; font-size: 1.1rem; font-weight: 500;">AI-Powered Restricted Area Monitoring System</p>
        </div>
    """, unsafe_allow_html=True)

    # Tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Home", "Live Monitor", "Analytics", "Snapshots", "Recordings", "Email Reporting"])

    with tab1:
        # 2. Sub-Header Card with Status Badges
        st.markdown("""
            <div class="glass-card" style="text-align: center; padding: 2.5rem 2rem; margin-bottom: 2rem;">
                <h2 style="color: #709138; font-size: 2.5rem; font-weight: 800; margin-bottom: 1.5rem; display: flex; align-items: center; justify-content: center; gap: 1rem;">
                    🛡️ Real-Time Intrusion Detection
                </h2>
                <p style="color: #64748B; font-size: 1.2rem; font-weight: 500; margin-bottom: 2rem;">Advanced AI-Powered surveillance system with state-of-the-art YOLO detection</p>
                <div style="display: flex; justify-content: center; gap: 1.5rem;">
                    <span class="badge-pill-custom badge-live-custom">● Live Monitoring</span>
                    <span class="badge-pill-custom badge-yolo-custom">● YOLOv8</span>
                    <span class="badge-pill-custom badge-secure-custom">● Secure</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # 3. System Statistics Dashboard
        st.markdown('<div class="section-header">📊 System Statistics</div>', unsafe_allow_html=True)
        
        # Read current data for statistics
        try:
            df = pd.read_csv(csv_file)
            total_detections = len(df) if not df.empty else 0
            total_violations = len(df[df["Restricted Area Violation"] == "Yes"]) if not df.empty else 0
            last_detection = df["Timestamp"].max() if not df.empty else "No data yet"
        except:
            total_detections = 0
            total_violations = 0
            last_detection = "No data yet"
        
        snapshot_count = 0
        if os.path.exists(frames_dir):
            snapshot_count = len([f for f in os.listdir(frames_dir) if f.endswith('.jpg')])
        
        col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
        with col_stat1:
            st.markdown(f"""
            <div class="stat-card-custom">
                <div style="font-size: 2.5rem; margin-bottom: 1rem;">🎯</div>
                <div style="font-size: 2rem; font-weight: 800; color: #00d4ff;">{total_detections}</div>
            </div>
            """, unsafe_allow_html=True)
        with col_stat2:
            st.markdown(f"""
            <div class="stat-card-custom">
                <div style="font-size: 2.5rem; margin-bottom: 1rem;">🚨</div>
                <div style="font-size: 2rem; font-weight: 800; color: #ef4444;">{total_violations}</div>
            </div>
            """, unsafe_allow_html=True)
        with col_stat3:
            st.markdown(f"""
            <div class="stat-card-custom">
                <div style="font-size: 2.5rem; margin-bottom: 1rem;">📸</div>
                <div style="font-size: 2rem; font-weight: 800; color: #709138;">{snapshot_count}</div>
            </div>
            """, unsafe_allow_html=True)
        with col_stat4:
            st.markdown(f"""
            <div class="stat-card-custom">
                <div style="font-size: 2.5rem; margin-bottom: 1rem;">👥</div>
                <div style="font-size: 2rem; font-weight: 800; color: #7c3aed;">{len(available_classes)}</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Enhanced Feature Cards with detailed descriptions
        st.markdown('<div class="section-header">✨ Key Features</div>', unsafe_allow_html=True)
        
        col_feat1, col_feat2 = st.columns(2)
        with col_feat1:
            st.markdown("""
            <div class="glass-card" style="padding: 1.5rem; transition: transform 0.3s ease;">
                <div style="display: flex; align-items: center; margin-bottom: 0.75rem;">
                    <div style="font-size: 2rem; margin-right: 0.85rem;">🎯</div>
                    <div>
                        <h3 style="color: #709138; margin: 0; font-size: 1.2rem; font-weight: 700;">Real-Time Detection</h3>
                        <span style="color: #00d4ff; font-size: 0.8rem;">● Live Object Recognition</span>
                    </div>
                </div>
                <p style="color: #4A4A4A; line-height: 1.6; margin-bottom: 0.75rem; font-size: 0.95rem;">Advanced YOLOv8 neural network provides instant object detection with high accuracy. Monitor multiple object classes simultaneously in real-time video streams.</p>
                <ul style="color: #4A4A4A; margin: 0; padding-left: 1.1rem; font-size: 0.9rem;">
                    <li>⚡ Sub-30ms processing time</li>
                    <li>🎯 80%+ detection accuracy</li>
                    <li>📊 Multi-class support</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class="glass-card" style="padding: 1.5rem; transition: transform 0.3s ease;">
                <div style="display: flex; align-items: center; margin-bottom: 0.75rem;">
                    <div style="font-size: 2rem; margin-right: 0.85rem;">📈</div>
                    <div>
                        <h3 style="color: #709138; margin: 0; font-size: 1.2rem; font-weight: 700;">Analytics Dashboard</h3>
                        <span style="color: #22c55e; font-size: 0.8rem;">● Comprehensive Insights</span>
                    </div>
                </div>
                <p style="color: #4A4A4A; line-height: 1.6; margin-bottom: 0.75rem; font-size: 0.95rem;">Detailed analytics with charts, trends, and violation patterns. Export data for further analysis and reporting.</p>
                <ul style="color: #4A4A4A; margin: 0; padding-left: 1.1rem; font-size: 0.9rem;">
                    <li>📊 Detection trends</li>
                    <li>🚨 Violation patterns</li>
                    <li>📥 CSV export support</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        with col_feat2:
            st.markdown("""
            <div class="glass-card" style="padding: 1.5rem; transition: transform 0.3s ease;">
                <div style="display: flex; align-items: center; margin-bottom: 0.75rem;">
                    <div style="font-size: 2rem; margin-right: 0.85rem;">🔔</div>
                    <div>
                        <h3 style="color: #709138; margin: 0; font-size: 1.2rem; font-weight: 700;">Smart Alerting</h3>
                        <span style="color: #ef4444; font-size: 0.8rem;">● Instant Notifications</span>
                    </div>
                </div>
                <p style="color: #4A4A4A; line-height: 1.6; margin-bottom: 0.75rem; font-size: 0.95rem;">Intelligent alerting system triggers immediate notifications when restricted area violations are detected. Audio alerts and visual indicators keep you informed.</p>
                <ul style="color: #4A4A4A; margin: 0; padding-left: 1.1rem; font-size: 0.9rem;">
                    <li>🔊 Audio alerts</li>
                    <li>🚨 Instant visual warnings</li>
                    <li>⏱️ Configurable thresholds</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class="glass-card" style="padding: 1.5rem; transition: transform 0.3s ease;">
                <div style="display: flex; align-items: center; margin-bottom: 0.75rem;">
                    <div style="font-size: 2rem; margin-right: 0.85rem;">📸</div>
                    <div>
                        <h3 style="color: #709138; margin: 0; font-size: 1.2rem; font-weight: 700;">Snapshots Gallery</h3>
                        <span style="color: #f59e0b; font-size: 0.8rem;">● Visual Evidence</span>
                    </div>
                </div>
                <p style="color: #4A4A4A; line-height: 1.6; margin-bottom: 0.75rem; font-size: 0.95rem;">Automatic snapshot capture for every detection event. Build a visual history of all monitored activities with timestamped evidence.</p>
                <ul style="color: #4A4A4A; margin: 0; padding-left: 1.1rem; font-size: 0.9rem;">
                    <li>🖼️ Auto-capture</li>
                    <li>📅 Timestamped images</li>
                    <li>🔍 Easy gallery view</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        # System Status Panel
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-header">📌 System Status</div>', unsafe_allow_html=True)
        
        col_status1, col_status2 = st.columns(2)
        with col_status1:
            camera_status = "🟢 Active" if st.session_state.camera_active else "🔴 Inactive"
            recording_status = "🔴 Not Recording" if not st.session_state.recording else "🟢 Recording"
            
            st.markdown(f"""
            <div class="glass-card" style="padding: 1.5rem;">
                <h4 style="color: #2D3E50; margin-bottom: 1.25rem; display: flex; align-items: center; gap: 0.5rem; font-size: 1.15rem;">
                    <span style="font-size: 1.25rem;">🎥</span> Camera & Recording Status
                </h4>
                <div style="display: grid; gap: 1rem;">
                    <div style="display: flex; justify-content: space-between; padding: 0.75rem; background: rgba(255,255,255,0.03); border-radius: 10px;">
                        <span style="color: #4A4A4A;">Camera Status</span>
                        <span style="color: {'#4ade80' if st.session_state.camera_active else '#ef4444'}; font-weight: 600;">{camera_status}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; padding: 0.75rem; background: rgba(255,255,255,0.03); border-radius: 10px;">
                        <span style="color: #4A4A4A;">Recording Status</span>
                        <span style="color: {'#4ade80' if st.session_state.recording else '#94a3b8'}; font-weight: 600;">{recording_status}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; padding: 0.75rem; background: rgba(255,255,255,0.03); border-radius: 10px;">
                        <span style="color: #4A4A4A;">Detection Classes</span>
                        <span style="color: #00d4ff; font-weight: 600;">{len(detect_options) if detect_options else 0} selected</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; padding: 0.75rem; background: rgba(255,255,255,0.03); border-radius: 10px;">
                        <span style="color: #4A4A4A;">Confidence Threshold</span>
                        <span style="color: #a78bfa; font-weight: 600;">{conf_thresh:.2f}</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col_status2:
            st.markdown(f"""
            <div class="glass-card" style="padding: 1.5rem;">
                <h4 style="color: #2D3E50; margin-bottom: 1.25rem; display: flex; align-items: center; gap: 0.5rem; font-size: 1.15rem;">
                    <span style="font-size: 1.25rem;">🤖</span> Model Information
                </h4>
                <div style="display: grid; gap: 1rem;">
                    <div style="display: flex; justify-content: space-between; padding: 0.75rem; background: rgba(255,255,255,0.03); border-radius: 10px;">
                        <span style="color: #4A4A4A;">Model Type</span>
                        <span style="color: #00d4ff; font-weight: 600;">YOLOv8n</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; padding: 0.75rem; background: rgba(255,255,255,0.03); border-radius: 10px;">
                        <span style="color: #4A4A4A;">Total Classes</span>
                        <span style="color: #22c55e; font-weight: 600;">{len(available_classes)}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; padding: 0.75rem; background: rgba(255,255,255,0.03); border-radius: 10px;">
                        <span style="color: #4A4A4A;">Alert Classes</span>
                        <span style="color: #ef4444; font-weight: 600;">{len(alert_options) if alert_options else 0} selected</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; padding: 0.75rem; background: rgba(255,255,255,0.03); border-radius: 10px;">
                        <span style="color: #4A4A4A;">Last Detection</span>
                        <span style="color: #f59e0b; font-weight: 600; font-size: 0.9rem;">{str(last_detection)[:19] if last_detection != "No data yet" else last_detection}</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Quick Start Guide
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-header">🚀 Quick Start Guide</div>', unsafe_allow_html=True)
        
        st.markdown("""
        <div class="glass-card" style="padding: 2rem;">
            <div style="display: flex; gap: 2rem; flex-wrap: wrap;">
                <div style="flex: 1; min-width: 200px;">
                    <h5 style="color: #00d4ff; margin-bottom: 1rem; display: flex; align-items: center; gap: 0.5rem;">
                        <span style="background: linear-gradient(135deg, #00d4ff, #7c3aed); color: white; width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.9rem; font-weight: 700;">1</span>
                        Start Monitoring
                    </h5>
                    <p style="color: #4A4A4A; margin: 0; padding-left: 2.5rem;">Click "Start" in the sidebar to activate the camera feed and begin real-time monitoring.</p>
                </div>
                <div style="flex: 1; min-width: 200px;">
                    <h5 style="color: #7c3aed; margin-bottom: 1rem; display: flex; align-items: center; gap: 0.5rem;">
                        <span style="background: linear-gradient(135deg, #7c3aed, #ec4899); color: white; width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.9rem; font-weight: 700;">2</span>
                        Configure Settings
                    </h5>
                    <p style="color: #4A4A4A; margin: 0; padding-left: 2.5rem;">Select objects to detect and alert on using the sidebar options. Adjust confidence threshold as needed.</p>
                </div>
                <div style="flex: 1; min-width: 200px;">
                    <h5 style="color: #ec4899; margin-bottom: 1rem; display: flex; align-items: center; gap: 0.5rem;">
                        <span style="background: linear-gradient(135deg, #ec4899, #f97316); color: white; width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.9rem; font-weight: 700;">3</span>
                        View Analytics
                    </h5>
                    <p style="color: #4A4A4A; margin: 0; padding-left: 2.5rem;">Check the Analytics tab for detailed reports, charts, and violation history.</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # ============================================
        # 🚨 REAL-TIME ALERTS SECTION
        # ============================================
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-header">🚨 Real-Time Alerts</div>', unsafe_allow_html=True)
        
        # Fetch alerts from API
        try:
            import requests
            response = requests.get("http://localhost:8000/api/alerts/stats", timeout=5)
            if response.status_code == 200:
                alerts_data = response.json()
                alert_count = alerts_data.get('total_alerts', 0)
                today_alerts = alerts_data.get('today_alerts', 0)
                week_alerts = alerts_data.get('week_alerts', 0)
                top_class = alerts_data.get('top_class', 'N/A')
            else:
                alert_count = 0
                today_alerts = 0
                week_alerts = 0
                top_class = 'N/A'
        except:
            # Fallback to reading CSV directly
            try:
                alerts_df = pd.read_csv(csv_file)
                if not alerts_df.empty:
                    all_violations = alerts_df[alerts_df["Restricted Area Violation"] == "Yes"]
                    alert_count = len(all_violations)
                    today_alerts = 0
                    week_alerts = 0
                    top_class = all_violations['Class'].mode().iloc[0] if not all_violations.empty else 'N/A'
                else:
                    alert_count = 0
                    today_alerts = 0
                    week_alerts = 0
                    top_class = 'N/A'
            except:
                alert_count = 0
                today_alerts = 0
                week_alerts = 0
                top_class = 'N/A'
        
        # Display alert stats
        col_alert1, col_alert2, col_alert3 = st.columns(3)
        
        with col_alert1:
            # Total Alerts Count
            if alert_count > 0:
                st.markdown(f"""
                <div class="glass-card" style="text-align: center; padding: 1.5rem; background: linear-gradient(145deg, rgba(239, 68, 68, 0.15), rgba(239, 68, 68, 0.1)); border: 1px solid rgba(239, 68, 68, 0.3);">
                    <div style="font-size: 3rem; margin-bottom: 0.5rem;">🚨</div>
                    <div style="font-size: 2.5rem; font-weight: 700; color: #ef4444;">{alert_count:,}</div>
                    <div style="color: #fca5a5; font-size: 0.9rem;">Total Violations</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="glass-card" style="text-align: center; padding: 1.5rem;">
                    <div style="font-size: 3rem; margin-bottom: 0.5rem;">✅</div>
                    <div style="font-size: 2rem; font-weight: 700; color: #22c55e;">No Violations</div>
                    <div style="color: #4A4A4A; font-size: 0.9rem;">Start monitoring to detect violations</div>
                </div>
                """, unsafe_allow_html=True)
        
        with col_alert2:
            # Today's and Week's Alerts
            if alert_count > 0:
                st.markdown(f"""
                <div class="glass-card" style="text-align: center; padding: 1.5rem;">
                    <div style="font-size: 3rem; margin-bottom: 0.5rem;">📊</div>
                    <div style="font-size: 1.8rem; font-weight: 700; color: #00d4ff;">{today_alerts} / {week_alerts}</div>
                    <div style="color: #4A4A4A; font-size: 0.9rem;">Today / This Week</div>
                    <div style="color: #a78bfa; font-size: 0.85rem; margin-top: 0.5rem;">Top: {top_class}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="glass-card" style="text-align: center; padding: 1.8rem; border-top: 4px solid #F1F5F9;">
                    <div style="font-size: 3.5rem; margin-bottom: 0.75rem;">📊</div>
                    <div style="font-size: 1.8rem; font-weight: 800; color: #64748B;">No Data Yet</div>
                    <div style="color: #94A3B8; font-size: 1rem;">Start camera to begin monitoring</div>
                </div>
                """, unsafe_allow_html=True)
        
        with col_alert3:
            # Quick Actions
            st.markdown(f"""
            <div class="glass-card" style="padding: 1.5rem;">
                <h4 style="color: #2D3E50; margin-bottom: 1rem;">⚡ Quick Actions</h4>
                <div style="display: flex; flex-direction: column; gap: 0.75rem;">
                    <div style="color: #4A4A4A; padding: 0.5rem 0;">🔔 Test Alert Sound</div>
                    <div style="color: #4A4A4A; padding: 0.5rem 0;">📧 Test Email Alert</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        

        
        
        st.markdown("<br>", unsafe_allow_html=True)

    with tab2:
        st.markdown("""
        <div class="live-monitor-header">
            Live Camera Feed
        </div>
        """, unsafe_allow_html=True)
        
        # Enhanced Status Badge Row
        col_status1, col_status2, col_status3 = st.columns([1, 1, 2])
        with col_status1:
            if st.session_state.camera_active:
                st.markdown('<div class="status-badge-enhanced active"><span class="live-dot"></span>● LIVE</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="status-badge-enhanced inactive">● OFFLINE</div>', unsafe_allow_html=True)
        with col_status2:
            if st.session_state.recording:
                st.markdown('<div class="status-badge-enhanced active" style="border-color: rgba(124, 58, 237, 0.3); background: rgba(124, 58, 237, 0.15); color: #a78bfa;">● RECORDING</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="status-badge-enhanced inactive">● NOT RECORDING</div>', unsafe_allow_html=True)
        with col_status3:
            st.markdown(f'<div style="text-align: right; color: #4A4A4A; font-size: 0.9rem;">📅 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</div>', unsafe_allow_html=True)
        
        st.markdown('<br>', unsafe_allow_html=True)
        
        if st.session_state.camera_active and st.session_state.cap is not None:
            # Enhanced Video Wrapper
            st.markdown('<div class="video-wrapper-enhanced">', unsafe_allow_html=True)
            
            frame_placeholder = st.empty()

            alert_placeholder = st.empty()
            status_placeholder = st.empty()
            frame_count = 0
            detected_count = 0
            
            try:
                while st.session_state.camera_active and st.session_state.cap.isOpened():
                    result = update_frame(st.session_state.cap, conf_thresh, detect_options, alert_options)
                    if result:
                        frame, detected, violator = result
                        if frame is not None:
                            frame_count += 1
                            detected_count = len(detected) if detected else 0
                            
                            if frame_count % 20 == 0 and st.session_state.recording:
                                save_frame(frame)
                            
                            # Write frame to video if recording
                            if st.session_state.video_recording and st.session_state.video_writer:
                                try:
                                    # Resize frame to match recording resolution
                                    if "Low" in st.session_state.recording_quality:
                                        target_size = (640, 480)
                                    elif "Medium" in st.session_state.recording_quality:
                                        target_size = (1280, 720)
                                    else:
                                        target_size = (1920, 1080)
                                    
                                    if frame.shape[1] != target_size[0] or frame.shape[0] != target_size[1]:
                                        frame_resized = cv2.resize(frame, target_size)
                                        st.session_state.video_writer.write(frame_resized)
                                    else:
                                        st.session_state.video_writer.write(frame)
                                except Exception as e:
                                    print(f"Error writing to video: {e}")
                            
                            if alert_active:
                                if violator:
                                    alert_placeholder.markdown(f'''
                                    <div class="alert-enhanced">
                                        <span style="font-size: 1.5rem;">🚨</span>
                                        <span>ALERT: {violator} detected in Restricted Area!</span>
                                    </div>
                                    ''', unsafe_allow_html=True)
                                    status_placeholder.markdown(f'''
                                    <div class="live-indicator" style="background: rgba(239, 68, 68, 0.15); border-color: rgba(239, 68, 68, 0.3);">
                                        <div class="live-dot" style="background: #ef4444; animation: alertPulse 0.5s ease-in-out infinite;"></div>
                                        <span class="live-text" style="color: #fca5a5;">{violator} Violating!</span>
                                    </div>
                                    ''', unsafe_allow_html=True)
                                else:
                                    alert_placeholder.markdown('''
                                    <div class="alert-enhanced">
                                        <span style="font-size: 1.5rem;">🚨</span>
                                        <span>Restricted Area Violation Detected!</span>
                                    </div>
                                    ''', unsafe_allow_html=True)
                            else:
                                alert_placeholder.empty()
                                status_placeholder.markdown(f'''
                                <div class="live-indicator">
                                    <div class="live-dot"></div>
                                    <span class="live-text">Monitoring Active</span>
                                </div>
                                ''', unsafe_allow_html=True)
                            
                            frame_placeholder.image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), channels="RGB", use_container_width=True)
                    time.sleep(0.03)
            except Exception as e:
                st.error(f"Error: {e}")
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Enhanced status bar below video
            st.markdown('<br>', unsafe_allow_html=True)
            recording_display = str(st.session_state.recording)
            st.markdown(f'''
            <div class="glass-card" style="padding: 1rem 1.5rem;">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
                    <div style="display: flex; gap: 2rem;">
                        <div>
                            <span style="color: #4A4A4A; font-size: 0.85rem;">Camera</span>
                            <div style="color: #4ade80; font-weight: 600;">● Active</div>
                        </div>
                        <div>
                            <span style="color: #4A4A4A; font-size: 0.85rem;">Recording</span>
                            <div style="color: #a78bfa; font-weight: 600;">● {recording_display}</div>
                        </div>
                        <div>
                            <span style="color: #4A4A4A; font-size: 0.85rem;">Confidence</span>
                            <div style="color: #00d4ff; font-weight: 600;">● {conf_thresh:.2f}</div>
                        </div>
                    </div>
                    <div>
                        <span class="status-badge-enhanced active">
                            <span style="color: #4ade80;">✓</span> System Ready
                        </span>
                    </div>
                </div>
            </div>
            ''', unsafe_allow_html=True)
            
        else:
            st.info("Click 'Start' in the sidebar to begin monitoring")

    with tab3:
        st.markdown('<div class="tab-section-header">📊 Analytics & Insights</div>', unsafe_allow_html=True)
        
        df = pd.read_csv(csv_file)
        
        if not df.empty:
            # Parse timestamps for time series analysis
            df['Timestamp'] = pd.to_datetime(df['Timestamp'], format='%Y-%m-%d %H:%M:%S')
            df['Hour'] = df['Timestamp'].dt.hour
            df['DayOfWeek'] = df['Timestamp'].dt.dayofweek
            df['DayName'] = df['Timestamp'].dt.day_name()
            df['Date'] = df['Timestamp'].dt.date
            
            # ============ Enhanced Metrics Row ============
            st.markdown('<div class="section-header">📈 Key Metrics</div>', unsafe_allow_html=True)
            
            total_detections = len(df)
            total_violations = len(df[df["Restricted Area Violation"] == "Yes"])
            avg_confidence = df["Confidence"].mean() * 100
            top_class = df["Class"].mode()[0] if not df["Class"].empty else "N/A"
            
            # Calculate detection rate (per hour)
            time_span_hours = (df['Timestamp'].max() - df['Timestamp'].min()).total_seconds() / 3600
            detection_rate = total_detections / max(time_span_hours, 1)
            
            # Most common violation time
            violation_df = df[df["Restricted Area Violation"] == "Yes"]
            if not violation_df.empty:
                common_violation_hour = violation_df['Hour'].mode()[0]
                most_common_violation_time = f"{common_violation_hour}:00 - {common_violation_hour+1}:00"
            else:
                most_common_violation_time = "N/A"
            
            col_m1, col_m2, col_m3, col_m4, col_m5, col_m6 = st.columns(6)
            col_m1.metric("Total Detections", total_detections)
            col_m2.metric("Total Violations", total_violations)
            col_m3.metric("Avg Confidence", f"{avg_confidence:.1f}%")
            col_m4.metric("Top Class", top_class)
            col_m5.metric("Detection Rate", f"{detection_rate:.1f}/hr")
            col_m6.metric("Common Violation Time", most_common_violation_time)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # ============ Time Range Filter ============
            st.markdown('<div class="section-header">⏱️ Time Filter</div>', unsafe_allow_html=True)
            
            time_filter = st.selectbox("Select Time Range", ["All Time", "Last 24 Hours", "Last 7 Days", "Last 30 Days"])
            
            filtered_df = df.copy()
            now = df['Timestamp'].max()
            
            if time_filter == "Last 24 Hours":
                filtered_df = df[df['Timestamp'] >= now - timedelta(hours=24)]
            elif time_filter == "Last 7 Days":
                filtered_df = df[df['Timestamp'] >= now - timedelta(days=7)]
            elif time_filter == "Last 30 Days":
                filtered_df = df[df['Timestamp'] >= now - timedelta(days=30)]
            
            st.markdown(f"Showing {len(filtered_df)} records", unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # ============ Detection Trends Over Time ============
            with st.expander("📈 Detection Trends Over Time", expanded=True):
                if HAS_PLOTLY_ANALYTICS and len(filtered_df) > 1:
                    fig_trends = epa.create_detection_timeline(filtered_df)
                    st.plotly_chart(fig_trends, use_container_width=True, theme=None)
                elif len(filtered_df) > 1:
                    # Group by date for line chart
                    daily_counts = filtered_df.groupby('Date').size().reset_index(name='Detections')
                    daily_counts['Date'] = pd.to_datetime(daily_counts['Date'])
                    daily_counts = daily_counts.sort_values('Date')
                    st.line_chart(daily_counts.set_index('Date'))
                else:
                    st.info("Not enough data for trend analysis")
            
            # ============ Violation Timeline ============
            with st.expander("🚨 Violation Timeline", expanded=False):
                violation_filtered = filtered_df[filtered_df["Restricted Area Violation"] == "Yes"]
                if HAS_PLOTLY_ANALYTICS and len(violation_filtered) > 1:
                    fig_violations = epa.create_detection_timeline(violation_filtered)
                    fig_violations.update_layout(title="Violation Timeline")
                    st.plotly_chart(fig_violations, use_container_width=True, theme=None)
                elif len(violation_filtered) > 1:
                    # Group violations by date
                    daily_violations = violation_filtered.groupby('Date').size().reset_index(name='Violations')
                    daily_violations['Date'] = pd.to_datetime(daily_violations['Date'])
                    daily_violations = daily_violations.sort_values('Date')
                    st.area_chart(daily_violations.set_index('Date'))
                elif len(violation_filtered) == 1:
                    st.info("Only 1 violation recorded in this period")
                else:
                    st.info("No violations recorded in this period")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # ============ Class Distribution & Confidence ============
            with st.expander("🎯 Class Distribution", expanded=False):
                if HAS_PLOTLY_ANALYTICS and len(filtered_df) > 0:
                    fig_pie = epa.create_detection_pie_chart(filtered_df)
                    st.plotly_chart(fig_pie, use_container_width=True, theme=None)
                else:
                    st.info("No class data available for analysis")

            with st.expander("📊 Confidence Distribution", expanded=False):
                if HAS_PLOTLY_ANALYTICS and len(filtered_df) > 0:
                    fig_conf = epa.create_confidence_distribution(filtered_df)
                    st.plotly_chart(fig_conf, use_container_width=True, theme=None)
                else:
                    st.info("No confidence data available for analysis")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # ============ Hourly Detection Pattern (Heatmap) ============
            with st.expander("🕐 Hourly Detection Pattern", expanded=False):
                if len(filtered_df) > 0:
                    if HAS_PLOTLY_ANALYTICS:
                        fig_heatmap = epa.create_detection_heatmap(filtered_df)
                        st.plotly_chart(fig_heatmap, use_container_width=True, theme=None)
                    else:
                        st.info("Chart module not available")
                else:
                    st.info("No data for heatmap analysis")
            
            # ============ Additional Insights ============
            with st.expander("💡 Additional Insights", expanded=False):
                col_insight1, col_insight2 = st.columns(2)
                
                with col_insight1:
                    st.markdown("#### 🎯 Detection Statistics")
                    most_active_day = filtered_df['DayName'].mode()[0] if len(filtered_df) > 0 else 'N/A'
                    busiest_hour = f"{filtered_df['Hour'].mode()[0]}:00" if len(filtered_df) > 0 else 'N/A'
                    st.markdown(f"- **Most Active Day:** {most_active_day}")
                    st.markdown(f"- **Busiest Hour:** {busiest_hour}")
                    st.markdown(f"- **Total Unique Classes:** {filtered_df['Class'].nunique()}")
                    unique_classes_str = ', '.join(filtered_df['Class'].unique()[:5])
                    if len(filtered_df['Class'].unique()) > 5:
                        unique_classes_str += '...'
                    st.markdown(f"- **Unique Classes:** {unique_classes_str}")
                
                with col_insight2:
                    st.markdown("#### 🚨 Violation Statistics")
                    violation_by_class = filtered_df[filtered_df["Restricted Area Violation"] == "Yes"]["Class"].value_counts()
                    st.markdown(f"- **Total Violations:** {len(violation_df)}")
                    if len(violation_by_class) > 0:
                        st.markdown(f"- **Most Common Violator:** {violation_by_class.index[0]}")
                        st.markdown(f"- **Violation Count by Class:**")
                        for class_name, count in violation_by_class.items():
                            st.markdown(f"  - {class_name}: {count}")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # ============ Data Table ============
            with st.expander("📋 Raw Data", expanded=False):
                st.dataframe(filtered_df, use_container_width=True)
            
            # ============ Export Functionality ============
            with st.expander("📥 Export Data", expanded=False):
                col_export1, col_export2 = st.columns(2)
                
                with col_export1:
                    # CSV Download
                    csv = filtered_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download Filtered Data as CSV",
                        data=csv,
                        file_name='detection_analytics_export.csv',
                        mime='text/csv'
                    )
                
                with col_export2:
                    # Summary statistics
                    summary_stats = filtered_df.groupby('Class').agg({
                        'Confidence': ['mean', 'max', 'min', 'count'],
                        'Restricted Area Violation': lambda x: (x == 'Yes').sum()
                    }).round(3)
                    summary_stats.columns = ['Avg Confidence', 'Max Confidence', 'Min Confidence', 'Count', 'Violations']
                    
                    st.markdown("#### Class-wise Summary")
                    st.dataframe(summary_stats, use_container_width=True)
        
        else:
            st.info("No data yet. Start monitoring to see analytics.")

    with tab4:
        st.markdown('<div class="tab-section-header">📸 Captured Snapshots</div>', unsafe_allow_html=True)
        
        # Initialize session state for delete confirmation
        if 'confirm_delete_all_snapshots' not in st.session_state:
            st.session_state.confirm_delete_all_snapshots = False
        
        frames = []
        if os.path.exists(frames_dir):
            for f in sorted(os.listdir(frames_dir), reverse=True):
                if f.endswith('.jpg'):
                    filepath = os.path.join(frames_dir, f)
                    if os.path.exists(filepath) and os.path.getsize(filepath) > 1024:
                        frames.append({'name': f, 'path': filepath})
        
        if frames:
            # Snapshot management tools
            col_stats, col_actions = st.columns([3, 1])
            with col_stats:
                st.markdown(f'<div class="glass-card"><h4>📸 Captured Snapshots ({len(frames)})</h4></div>', unsafe_allow_html=True)
            
            with col_actions:
                # Delete All button
                if st.button("🗑️ Delete All", key="delete_all_snapshots_btn"):
                    if st.session_state.confirm_delete_all_snapshots:
                        # Confirm delete all
                        deleted_count = 0
                        for fr in frames:
                            try:
                                if os.path.exists(fr['path']):
                                    os.remove(fr['path'])
                                    deleted_count += 1
                            except Exception as e:
                                st.error(f"Error deleting {fr['name']}: {e}")
                        
                        st.success(f"✅ Deleted {deleted_count} snapshot(s)")
                        st.session_state.confirm_delete_all_snapshots = False
                        st.rerun()
                    else:
                        st.session_state.confirm_delete_all_snapshots = True
                        st.warning("Click again to confirm")
                
                # Cancel delete all
                if st.session_state.confirm_delete_all_snapshots:
                    if st.button("❌ Cancel"):
                        st.session_state.confirm_delete_all_snapshots = False
                        st.rerun()
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Display snapshots in a grid with delete buttons
            for i in range(0, len(frames), 5):
                cols = st.columns(5)
                for j in range(5):
                    idx = i + j
                    if idx < len(frames):
                        fr = frames[idx]
                        with cols[j]:
                            # Show image
                            try:
                                st.image(fr['path'], caption=fr['name'][:25], use_container_width=True)
                            except Exception as img_error:
                                st.error("Cannot load image")
                            
                            # Delete button for individual snapshot
                            if st.button("🗑️ Delete", key=f"del_snap_{fr['name']}"):
                                try:
                                    if os.path.exists(fr['path']):
                                        os.remove(fr['path'])
                                        st.success("Snapshot deleted")
                                        st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {e}")
                            
                            # File size info
                            try:
                                size_kb = os.path.getsize(fr['path']) / 1024
                                st.caption(f"📁 {size_kb:.1f} KB")
                            except:
                                pass
        else:
            st.info("No snapshots captured yet. Start monitoring to capture violation images.")
            
            # Quick guide
            st.markdown("""
            <div class="glass-card" style="padding: 2rem; margin-top: 1rem;">
                <h4 style="color: #709138; margin-bottom: 1rem;">📝 How Snapshots Work</h4>
                <ol style="color: #4A4A4A; line-height: 2;">
                    <li>Go to the <strong>Live Monitor</strong> tab</li>
                    <li>Start the camera</li>
                    <li>When a violation is detected, a snapshot is automatically captured</li>
                    <li>View and manage snapshots in this tab</li>
                    <li>Use the delete buttons to remove unwanted snapshots</li>
                </ol>
            </div>
            """, unsafe_allow_html=True)

    # ========== TAB 5: RECORDINGS ==========
    with tab5:
        st.markdown('<div class="tab-section-header">🎬 Video Recordings</div>', unsafe_allow_html=True)
        
        # Get all recordings
        recordings = get_recordings()
        
        # Recording statistics
        col_stat1, col_stat2, col_stat3 = st.columns(3)
        with col_stat1:
            st.metric("Total Recordings", len(recordings))
        with col_stat2:
            total_size = sum(r['size_mb'] for r in recordings)
            st.metric("Total Storage", f"{total_size:.2f} MB")
        with col_stat3:
            if recordings:
                latest_recording = recordings[0]['created']
                st.metric("Latest Recording", latest_recording)
            else:
                st.metric("Latest Recording", "N/A")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Recordings management
        st.markdown('<div class="section-header">📁 Recordings Library</div>', unsafe_allow_html=True)
        
        if recordings:
            # Filter and search
            search_term = st.text_input("🔍 Search recordings", placeholder="Enter recording name...")
            if search_term:
                recordings = [r for r in recordings if search_term.lower() in r['name'].lower()]
            
            st.markdown(f"Showing {len(recordings)} recording(s)", unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Display recordings in a grid
            for i in range(0, len(recordings), 2):
                col_rec1, col_rec2 = st.columns(2)
                
                for j, recording in enumerate(recordings[i:i+2]):
                    with [col_rec1, col_rec2][j]:
                        with st.expander(f"🎬 {recording['name']}", expanded=False):
                            # Recording information and download options
                            try:
                                # Try to get a preview frame using OpenCV (only for .avi files which are more compatible)
                                if recording['name'].endswith('.avi'):
                                    cap = cv2.VideoCapture(recording['path'])
                                    if cap.isOpened():
                                        ret, frame = cap.read()
                                        if ret:
                                            # Convert BGR to RGB
                                            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                                            st.image(frame_rgb, caption="Preview frame", width=300)
                                        cap.release()

                            except Exception as e:
                                st.warning(f"Preview not available for {recording['name']}, but video can still be downloaded.")
                            
                            # Recording metadata
                            duration = get_video_duration(recording['path'])
                            
                            st.markdown(f"""
                            <div style="display: grid; gap: 0.5rem; margin-top: 1rem;">
                                <div style="display: flex; justify-content: space-between;">
                                    <span style="color: #4A4A4A;">Created:</span>
                                    <span style="color: #2D3E50;">{recording['created']}</span>
                                </div>
                                <div style="display: flex; justify-content: space-between;">
                                    <span style="color: #4A4A4A;">Size:</span>
                                    <span style="color: #22c55e;">{recording['size_mb']:.2f} MB</span>
                                </div>
                                <div style="display: flex; justify-content: space-between;">
                                    <span style="color: #4A4A4A;">Duration:</span>
                                    <span style="color: #00d4ff;">{format_duration(duration)}</span>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Action buttons
                            col_dl, col_del = st.columns(2)
                            with col_dl:
                                with open(recording['path'], 'rb') as f:
                                    # Determine MIME type based on file extension
                                    mime_type = 'video/avi' if recording['name'].endswith('.avi') else 'video/mp4'
                                    st.download_button(
                                        label="📥 Download",
                                        data=f.read(),
                                        file_name=recording['name'],
                                        mime=mime_type,
                                        key=f"dl_{recording['name']}"
                                    )
                            with col_del:
                                if st.button("🗑️ Delete", key=f"del_{recording['name']}"):
                                    if delete_recording(recording['path']):
                                        st.success("Recording deleted")
                                        st.rerun()
                                    else:
                                        st.error("Failed to delete recording")
        else:
            st.info("No recordings found. Start video recording from the Live Monitor tab!")
            
            # Quick start guide for recording
            st.markdown("""
            <div class="glass-card" style="padding: 2rem; margin-top: 1rem;">
                <h4 style="color: #709138; margin-bottom: 1rem;">📝 How to Record</h4>
                <ol style="color: #4A4A4A; line-height: 2;">
                    <li>Go to the <strong>Live Monitor</strong> tab</li>
                    <li>Start the camera if not already running</li>
                    <li>In the sidebar, select your <strong>Recording Quality</strong> (Low/Medium/High)</li>
                    <li>Adjust <strong>Recording FPS</strong> as needed</li>
                    <li>Click <strong>⏺ Start Recording</strong> to begin</li>
                    <li>Click <strong>⏹ Stop Recording</strong> when finished</li>
                    <li>View and manage recordings in this tab</li>
                </ol>
            </div>
            """, unsafe_allow_html=True)
        
        # Bulk actions
        if recordings:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("---")
            col_bulk1, col_bulk2 = st.columns(2)
            with col_bulk1:
                if st.button("🗑️ Delete All Recordings", key="delete_all_recordings_btn"):
                    if st.session_state.get('confirm_delete_all'):
                        # Delete all recordings
                        deleted_count = 0
                        for recording in recordings:
                            if delete_recording(recording['path']):
                                deleted_count += 1
                        st.success(f"Deleted {deleted_count} recording(s)")
                        st.rerun()
                    else:
                        st.session_state.confirm_delete_all = True
                        st.warning("Click again to confirm delete all")
            with col_bulk2:
                if st.session_state.get('confirm_delete_all'):
                    if st.button("❌ Cancel"):
                        st.session_state.confirm_delete_all = False
                        st.rerun()

    # ========== TAB 6: EMAIL REPORTING ==========
    with tab6:
        st.markdown('<div class="tab-section-header">📧 Email Reporting</div>', unsafe_allow_html=True)
        
        if not HAS_EMAIL_REPORTING:
            st.error("Email Reporting module not available. Please ensure advanced_email_reporting.py is installed.")
        else:
            email_tab1, email_tab2, email_tab3 = st.tabs(["Send Report", "Scheduled Reports", "Report Templates"])
            
            # Send Report Tab
            with email_tab1:
                st.markdown("### 📤 Send Report Immediately")
                st.markdown("Generate and send a report right now.")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    report_type = st.selectbox("Report Type", ["daily", "weekly", "monthly"])
                
                with col2:
                    template_type = st.selectbox("Report Template", ["summary", "detailed", "compliance", "operational"])
                
                with col3:
                    st.write("")  # Spacing
                
                col1, col2 = st.columns(2)
                with col1:
                    include_csv = st.checkbox("Include CSV", value=True)
                with col2:
                    include_pdf = st.checkbox("Include PDF", value=False)
                
                recipients_input = st.text_area("Recipients (comma-separated)", height=80, help="Enter email addresses separated by commas")
                
                if st.button("📨 Send Report Now", use_container_width=True):
                    if not recipients_input.strip():
                        st.error("Please enter at least one recipient email")
                    else:
                        with st.spinner("Preparing report..."):
                            try:
                                recipients = [e.strip() for e in recipients_input.split(",") if e.strip()]
                                
                                # Send report via API
                                result = send_report_api(
                                    report_type=report_type,
                                    template_type=template_type,
                                    recipient_email=recipients[0],  # Send to first recipient
                                    include_pdf=include_pdf
                                )
                                
                                if "error" not in result:
                                    st.success(f"✅ Report sent successfully")
                                    st.info(f"Recipients: {', '.join(recipients)}")
                                    if include_pdf:
                                        st.info("📎 PDF attachment included")
                                else:
                                    st.error(f"❌ {result.get('error', 'Unknown error')}")
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
            
            # Scheduled Reports Tab
            with email_tab2:
                st.markdown("### 📅 Manage Scheduled Reports")
                st.markdown("Create and manage automatic report delivery schedules.")
                
                schedule_action = st.radio("Action", ["View Schedules", "Create New Schedule", "Edit Schedule"])
                
                if schedule_action == "View Schedules":
                    try:
                        schedules_response = get_email_schedules()
                        schedules = schedules_response.get("schedules", []) if isinstance(schedules_response, dict) else schedules_response
                        
                        if schedules:
                            for schedule in schedules:
                                with st.expander(f"📋 {schedule.get('name', 'Unnamed')} ({schedule.get('report_type', 'unknown')})"):
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        st.write(f"**Type:** {schedule.get('report_type', 'N/A')}")
                                    with col2:
                                        st.write(f"**Template:** {schedule.get('template_type', 'N/A')}")
                                    with col3:
                                        status = "🟢 Active" if schedule.get('active', True) else "🔴 Inactive"
                                        st.write(f"**Status:** {status}")
                                    
                                    st.write(f"**Recipients:** {', '.join(schedule.get('recipients', []))}")
                                    st.write(f"**Last Sent:** {schedule.get('last_sent', 'Never')}")
                                    st.write(f"**Next Send:** {schedule.get('next_send', 'N/A')}")
                                    
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        if st.button("📤 Send Now", key=f"send_{schedule['id']}"):
                                            with st.spinner("Sending..."):
                                                result = execute_email_schedule(schedule['id'])
                                                if result.get("status") == "success" or result.get("message", "").find("success") >= 0:
                                                    st.success("Report sent!")
                                                else:
                                                    st.error(result.get("message", "Error sending report"))
                                    with col2:
                                        if st.button("✏️ Edit", key=f"edit_{schedule['id']}"):
                                            st.session_state.edit_schedule_id = schedule['id']
                                    with col3:
                                        if st.button("🗑️ Delete", key=f"del_{schedule['id']}"):
                                            result = delete_email_schedule(schedule['id'])
                                            if result.get("status") == "success":
                                                st.success("Schedule deleted")
                                                st.rerun()
                        else:
                            st.info("No scheduled reports configured yet. Create one to get started!")
                    except Exception as e:
                        st.error(f"Error loading schedules: {str(e)}")
                
                elif schedule_action == "Create New Schedule":
                    with st.form("new_schedule_form"):
                        schedule_name = st.text_input("Schedule Name", placeholder="e.g., Daily Security Report")
                        report_type = st.selectbox("Report Type", ["daily", "weekly", "monthly"])
                        template_type = st.selectbox("Template", ["summary", "detailed", "compliance", "operational"])
                        send_time = st.time_input("Send Time")
                        recipients = st.text_area("Recipients (comma-separated)", height=80)
                        include_csv = st.checkbox("Include CSV", value=True)
                        include_pdf = st.checkbox("Include PDF", value=False)
                        
                        if st.form_submit_button("✅ Create Schedule"):
                            if not schedule_name or not recipients:
                                st.error("Please fill in all required fields")
                            else:
                                try:
                                    schedule_manager = ReportScheduleManager()
                                    config = {
                                        "name": schedule_name,
                                        "report_type": report_type,
                                        "template_type": template_type,
                                        "send_time": send_time.strftime("%H:%M"),
                                        "recipients": [e.strip() for e in recipients.split(",") if e.strip()],
                                        "include_csv": include_csv,
                                        "include_pdf": include_pdf
                                    }
                                    result = schedule_manager.add_schedule(config)
                                    if result["status"] == "success":
                                        st.success(f"✅ Schedule created: {schedule_name}")
                                        st.balloons()
                                    else:
                                        st.error(result.get("message", "Error creating schedule"))
                                except Exception as e:
                                    st.error(f"Error: {str(e)}")
            
            # Report Templates Tab
            with email_tab3:
                st.markdown("### 📋 Report Templates")
                st.markdown("Choose and configure report templates for your needs.")
                
                templates = EmailReportTemplate.list_templates()
                
                for template in templates:
                    with st.expander(f"📄 {template['name']}"):
                        st.write(f"**Description:** {template['description']}")
                        
                        template_config = EmailReportTemplate.get_template(template['id'])
                        st.write(f"**Sections Included:**")
                        for section in template_config['sections']:
                            st.write(f"  • {section.replace('_', ' ').title()}")
                        
                        st.write(f"**Template ID:** `{template['id']}`")


# Main Application Entry Point
if st.session_state.authenticated:
    main_app()
else:
    if st.session_state.get('show_signup'):
        signup_page()
    else:
        login_page()
