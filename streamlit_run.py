import streamlit as st
import cv2
import numpy as np
import pandas as pd
from ultralytics import YOLO
import threading
import random
from datetime import datetime, timedelta
import os
import time
import pygame
import hashlib
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import ssl
from pathlib import Path
from collections import Counter
import plotly.graph_objects as go
import plotly.express as px

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
    from advanced_email_reporting import EmailReportTemplate, ReportScheduleManager
    HAS_EMAIL_REPORTING = True
    # Initialize schedule manager globally for use in UI
    schedule_manager = ReportScheduleManager()
except ImportError:
    HAS_EMAIL_REPORTING = False
    print("Warning: Email reporting modules not available")
    schedule_manager = None

# Load environment variables
ENV_FILE = Path(__file__).parent / ".env"

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
            response = requests.get(url, params=params, timeout=30)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=30)
        elif method == "DELETE":
            response = requests.delete(url, timeout=30)
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

USERS_FILE = "data/users.json"

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

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
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

st.markdown("""
<style>
/* ============================================
   🎨 Enhanced Dark Theme - Streamlit Frontend
   Consistent with FastAPI Backend
   ============================================ */

.stApp { 
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%); 
}

/* Animated Background Elements */
.stApp::before {
    content: '';
    position: fixed;
    top: -150px;
    left: -150px;
    width: 500px;
    height: 500px;
    background: radial-gradient(circle, rgba(0, 212, 255, 0.12) 0%, transparent 70%);
    border-radius: 50%;
    animation: float 25s infinite ease-in-out;
    z-index: 0;
    pointer-events: none;
}

@keyframes float {
    0%, 100% { transform: translate(0, 0) scale(1); }
    25% { transform: translate(80px, 80px) scale(1.1); }
    50% { transform: translate(40px, 150px) scale(0.9); }
    75% { transform: translate(-60px, 80px) scale(1.05); }
}

/* App Header - Enhanced Glass Morphism */
.app-header { 
    text-align: center; 
    padding: 3rem 2rem; 
    margin-bottom: 2.5rem; 
    background: rgba(255, 255, 255, 0.05); 
    backdrop-filter: blur(20px); 
    border-radius: 24px; 
    border: 1px solid rgba(255, 255, 255, 0.1); 
    box-shadow: 
        0 8px 32px rgba(0, 0, 0, 0.3),
        inset 0 1px 0 rgba(255, 255, 255, 0.1);
    position: relative;
    overflow: hidden;
}

.app-header::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, #00d4ff, #7c3aed, #ec4899, transparent);
    animation: shimmer 3s infinite;
}

@keyframes shimmer {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(100%); }
}

.app-header h1 { 
    font-size: 3rem; 
    font-weight: 800; 
    background: linear-gradient(135deg, #00d4ff 0%, #7c3aed 50%, #ec4899 100%); 
    -webkit-background-clip: text; 
    -webkit-text-fill-color: transparent; 
    background-clip: text; 
    margin-bottom: 0.75rem;
    letter-spacing: -0.5px;
}

.app-header p { 
    font-size: 1.15rem; 
    color: #94a3b8; 
    font-weight: 500; 
    margin-top: 0.5rem;
    letter-spacing: 0.3px;
}

/* Glass Card - Enhanced */
.glass-card { 
    background: rgba(255, 255, 255, 0.05); 
    backdrop-filter: blur(16px); 
    border-radius: 20px; 
    padding: 2rem; 
    margin-bottom: 1.5rem; 
    border: 1px solid rgba(255, 255, 255, 0.1); 
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    transition: all 0.3s ease;
}

.glass-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 12px 45px rgba(0, 0, 0, 0.4);
    border-color: rgba(255, 255, 255, 0.15);
}

/* Section Header - Enhanced */
.section-header { 
    font-size: 1.6rem; 
    font-weight: 700; 
    color: #f1f5f9; 
    margin-bottom: 1.5rem; 
    display: flex; 
    align-items: center; 
    gap: 0.75rem;
    letter-spacing: 0.3px;
}

.section-header::before { 
    content: ''; 
    width: 4px; 
    height: 28px; 
    background: linear-gradient(180deg, #00d4ff, #7c3aed); 
    border-radius: 2px; 
}
/* Tab Section Header - Enhanced */
.tab-section-header { 
    font-size: 1.85rem; 
    font-weight: 800; 
    color: #f1f5f9; 
    margin-bottom: 1.75rem; 
    display: flex; 
    align-items: center; 
    gap: 1rem; 
    padding-bottom: 1rem; 
    border-bottom: 2px solid rgba(0, 212, 255, 0.2);
    letter-spacing: 0.3px;
}

.tab-section-header::before { 
    content: ''; 
    width: 6px; 
    height: 36px; 
    background: linear-gradient(180deg, #00d4ff, #7c3aed); 
    border-radius: 3px; 
}

/* Tabs - Enhanced Gradient Design */
.stTabs [data-baseweb="tab-list"] { 
    gap: 12px; 
    background: linear-gradient(135deg, rgba(0, 212, 255, 0.08) 0%, rgba(124, 58, 237, 0.08) 50%, rgba(236, 72, 153, 0.08) 100%); 
    border-radius: 16px; 
    padding: 0.75rem; 
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.05);
}

.stTabs [data-baseweb="tab"] { 
    background: rgba(255, 255, 255, 0.05); 
    border-radius: 12px; 
    color: #94a3b8; 
    font-weight: 600; 
    padding: 0.75rem 1.5rem;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    border: 1px solid transparent;
}

.stTabs [data-baseweb="tab"]:hover { 
    background: linear-gradient(135deg, rgba(0, 212, 255, 0.15), rgba(124, 58, 237, 0.15)); 
    color: #fff; 
    transform: translateY(-3px);
    border-color: rgba(255, 255, 255, 0.1);
    box-shadow: 0 4px 12px rgba(0, 212, 255, 0.2);
}

.stTabs [aria-selected="true"] { 
    background: linear-gradient(135deg, #00d4ff, #7c3aed, #ec4899) !important; 
    color: #fff !important; 
    font-weight: 700 !important;
    box-shadow: 0 4px 15px rgba(0, 212, 255, 0.4);
    border-color: transparent !important;
}
/* Video Wrapper - Enhanced Border */
.video-wrapper { 
    border-radius: 20px; 
    overflow: hidden; 
    border: 3px solid rgba(0, 212, 255, 0.4); 
    box-shadow: 
        0 0 40px rgba(0, 212, 255, 0.25),
        0 10px 40px rgba(0, 0, 0, 0.3); 
    background: #000;
    transition: all 0.3s ease;
}

.video-wrapper:hover {
    border-color: rgba(124, 58, 237, 0.4);
    box-shadow: 
        0 0 50px rgba(124, 58, 237, 0.3),
        0 12px 45px rgba(0, 0, 0, 0.4);
}

/* Alert Box - Enhanced Pulse Animation */
.alert-box { 
    background: linear-gradient(145deg, rgba(239, 68, 68, 0.15), rgba(239, 68, 68, 0.1)); 
    border: 2px solid rgba(239, 68, 68, 0.5); 
    border-radius: 12px; 
    padding: 1rem 1.5rem; 
    color: #fca5a5; 
    font-weight: 700; 
    animation: alertPulse 1.5s ease-in-out infinite;
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

@keyframes alertPulse { 
    0%, 100% { 
        opacity: 1; 
        box-shadow: 0 0 20px rgba(239, 68, 68, 0.3);
    } 
    50% { 
        opacity: 0.95; 
        box-shadow: 0 0 40px rgba(239, 68, 68, 0.5);
    } 
}

/* Status Badge - Enhanced with Animation */
.status-badge { 
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 0.5rem 1.2rem; 
    border-radius: 20px; 
    font-size: 0.9rem; 
    font-weight: 600; 
    background: rgba(34, 197, 94, 0.15); 
    color: #4ade80; 
    border: 1px solid rgba(34, 197, 94, 0.3);
    transition: all 0.3s ease;
}

.status-badge:hover {
    transform: translateX(3px);
    box-shadow: 0 4px 12px rgba(34, 197, 94, 0.2);
}

.status-badge.inactive { 
    background: rgba(148, 163, 184, 0.15); 
    color: #94a3b8; 
    border-color: rgba(148, 163, 184, 0.3); 
}

/* Buttons - Enhanced Gradient */
.stButton > button { 
    background: linear-gradient(135deg, #00d4ff, #7c3aed) !important; 
    color: white !important; 
    border: none !important; 
    border-radius: 12px !important; 
    padding: 0.75rem 1.5rem !important; 
    font-weight: 600 !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    box-shadow: 0 4px 12px rgba(0, 212, 255, 0.2) !important;
}

.stButton > button:hover { 
    background: linear-gradient(135deg, #7c3aed, #ec4899) !important; 
    transform: translateY(-3px) !important; 
    box-shadow: 0 6px 20px rgba(0, 212, 255, 0.4) !important; 
}
/* Sidebar Button - Enhanced */
.sidebar-button > button { 
    background: linear-gradient(135deg, #00d4ff, #7c3aed) !important; 
    color: white !important; 
    border: none !important; 
    border-radius: 12px !important; 
    padding: 0.75rem 1.5rem !important; 
    font-weight: 600 !important; 
    width: 100% !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    box-shadow: 0 4px 12px rgba(0, 212, 255, 0.2) !important;
}

.sidebar-button > button:hover { 
    background: linear-gradient(135deg, #7c3aed, #ec4899) !important; 
    transform: translateY(-3px) !important;
    box-shadow: 0 6px 20px rgba(0, 212, 255, 0.4) !important;
}

/* Metrics - Enhanced with Animation */
[data-testid="stMetricValue"] { 
    color: #00d4ff !important; 
    font-size: 2.2rem !important; 
    font-weight: 800 !important;
    letter-spacing: -0.5px !important;
    animation: countUp 0.6s ease-out !important;
}

@keyframes countUp {
    from {
        opacity: 0;
        transform: translateY(15px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

[data-testid="stMetricLabel"] { 
    color: #94a3b8 !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    letter-spacing: 0.5px !important;
    text-transform: uppercase !important;
}
/* Auth Container */
.auth-container { 
    max-width: 450px; 
    margin: 0 auto; 
}

/* Text Input - Enhanced */
.stTextInput > div > div > input { 
    background: rgba(255, 255, 255, 0.05) !important; 
    border: 1px solid rgba(255, 255, 255, 0.1) !important; 
    color: white !important;
    border-radius: 10px !important;
    padding: 0.75rem 1rem !important;
    transition: all 0.3s ease !important;
}

.stTextInput > div > div > input:focus { 
    border-color: rgba(0, 212, 255, 0.5) !important; 
    box-shadow: 0 0 0 3px rgba(0, 212, 255, 0.1) !important;
}

/* Multi Select - Enhanced */
.stMultiSelect > div > div > div { 
    background: rgba(255, 255, 255, 0.05) !important; 
    border: 1px solid rgba(0, 212, 255, 0.3) !important; 
    color: white !important;
    border-radius: 10px !important;
}

.stMultiSelect svg { 
    color: #00d4ff !important; 
}

/* Slider - Enhanced Gradient */
.stSlider [data-baseweb="slider"] { 
    color: #00d4ff !important; 
}

.stSlider [data-baseweb="slider"] > div > div > div { 
    background: linear-gradient(90deg, #00d4ff, #7c3aed, #ec4899) !important; 
}

.stSlider [data-baseweb="slider"] > div > div > span > div { 
    background: white !important; 
    border: 3px solid #00d4ff !important;
    box-shadow: 0 2px 8px rgba(0, 212, 255, 0.4) !important;
}

/* ===== Enhanced Live Monitor Styles ===== */

/* Gradient Header for Live Monitor */
.live-monitor-header {
    font-size: 2rem;
    font-weight: 800;
    background: linear-gradient(135deg, #00d4ff 0%, #7c3aed 50%, #ec4899 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 1.5rem;
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

.live-monitor-header::before {
    content: '📹';
    -webkit-text-fill-color: initial;
    font-size: 1.8rem;
}

/* Camera Not Active Card - Glass Morphism */
.camera-not-active-card {
    background: linear-gradient(145deg, #1e1e3f 0%, #2a2a5a 100%);
    border-radius: 20px;
    padding: 3rem 2rem;
    margin: 2rem auto;
    max-width: 500px;
    box-shadow: 
        0 20px 60px rgba(0, 0, 0, 0.4),
        0 10px 30px rgba(0, 0, 0, 0.3),
        inset 0 1px 0 rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.1);
    animation: fadeInUp 0.6s ease-out;
    text-align: center;
}

@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(30px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* Animated Camera Icon Container */
.camera-icon-container {
    position: relative;
    width: 120px;
    height: 120px;
    margin: 0 auto 1.5rem;
    display: flex;
    align-items: center;
    justify-content: center;
}

/* Camera Icon Circle */
.camera-icon-circle {
    width: 100px;
    height: 100px;
    border-radius: 50%;
    background: linear-gradient(145deg, #3a3a6a, #2a2a4a);
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 
        0 8px 25px rgba(0, 0, 0, 0.4),
        inset 0 2px 0 rgba(255, 255, 255, 0.1);
    position: relative;
    z-index: 2;
}

/* Camera Icon Animation */
.camera-icon-svg {
    font-size: 40px;
    color: #8b8bb8;
    animation: iconPulse 2s ease-in-out infinite;
}

@keyframes iconPulse {
    0%, 100% {
        transform: scale(1);
        color: #8b8bb8;
    }
    50% {
        transform: scale(1.1);
        color: #6c6c9c;
    }
}

/* Pulse Rings Animation */
.pulse-ring {
    position: absolute;
    width: 120px;
    height: 120px;
    border-radius: 50%;
    border: 3px solid rgba(139, 139, 184, 0.4);
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    z-index: 1;
    animation: pulseRing 2s ease-out infinite;
}

.pulse-ring.delay-1 {
    animation-delay: 0.5s;
}

.pulse-ring.delay-2 {
    animation-delay: 1s;
}

@keyframes pulseRing {
    0% {
        transform: translate(-50%, -50%) scale(0.8);
        opacity: 0.8;
    }
    100% {
        transform: translate(-50%, -50%) scale(1.5);
        opacity: 0;
    }
}

/* Status Title */
.camera-status-title {
    font-size: 1.75rem;
    font-weight: 700;
    color: #fff;
    margin-bottom: 0.75rem;
}

/* Status Message */
.camera-status-message {
    font-size: 1rem;
    color: #a0a0c0;
    margin-bottom: 1.5rem;
}

/* Enhanced Live Indicator */
.live-indicator {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    background: rgba(34, 197, 94, 0.15);
    border: 1px solid rgba(34, 197, 94, 0.3);
    border-radius: 30px;
    margin-top: 1rem;
}

.live-dot {
    width: 10px;
    height: 10px;
    background: #22c55e;
    border-radius: 50%;
    animation: livePulse 1.5s ease-in-out infinite;
}

@keyframes livePulse {
    0%, 100% {
        opacity: 1;
        transform: scale(1);
        box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.7);
    }
    50% {
        opacity: 0.8;
        transform: scale(0.9);
        box-shadow: 0 0 0 8px rgba(34, 197, 94, 0);
    }
}

.live-text {
    color: #4ade80;
    font-size: 0.9rem;
    font-weight: 600;
}

/* Enhanced Video Wrapper */
.video-wrapper-enhanced {
    border-radius: 20px;
    overflow: hidden;
    border: 3px solid rgba(0, 212, 255, 0.4);
    box-shadow: 
        0 0 40px rgba(0, 212, 255, 0.25),
        0 10px 40px rgba(0, 0, 0, 0.3);
    background: #000;
    position: relative;
}

/* Video Overlay Stats */
.video-overlay-stats {
    position: absolute;
    top: 1rem;
    right: 1rem;
    background: rgba(0, 0, 0, 0.7);
    backdrop-filter: blur(10px);
    border-radius: 12px;
    padding: 0.75rem 1rem;
    border: 1px solid rgba(255, 255, 255, 0.1);
    z-index: 10;
}

.video-overlay-stats span {
    display: block;
    color: #94a3b8;
    font-size: 0.8rem;
    margin-bottom: 0.25rem;
}

.video-overlay-stats strong {
    color: #00d4ff;
    font-size: 1rem;
}

/* Alert Status Enhanced */
.alert-enhanced {
    background: linear-gradient(145deg, rgba(239, 68, 68, 0.2), rgba(239, 68, 68, 0.1));
    border: 2px solid rgba(239, 68, 68, 0.5);
    border-radius: 12px;
    padding: 1rem 1.5rem;
    color: #fca5a5;
    font-weight: 700;
    animation: alertPulse 1s ease-in-out infinite;
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

@keyframes alertPulse {
    0%, 100% {
        box-shadow: 0 0 20px rgba(239, 68, 68, 0.3);
    }
    50% {
        box-shadow: 0 0 40px rgba(239, 68, 68, 0.5);
    }
}

/* Status Badge Enhanced */
.status-badge-enhanced {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.4rem 1rem;
    border-radius: 20px;
    font-size: 0.85rem;
    font-weight: 600;
}

.status-badge-enhanced.active {
    background: rgba(34, 197, 94, 0.15);
    color: #4ade80;
    border: 1px solid rgba(34, 197, 94, 0.3);
}

.status-badge-enhanced.inactive {
    background: rgba(148, 163, 184, 0.15);
    color: #94a3b8;
    border: 1px solid rgba(148, 163, 184, 0.3);
}

/* Control Button Styles */
.control-btn {
    background: linear-gradient(135deg, #00d4ff, #7c3aed) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.75rem 1.5rem !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
}

.control-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(0, 212, 255, 0.4) !important;
}

/* ===== Analytics Chart Styles ===== */

/* Ensure all Plotly charts display with consistent sizing */
.st.plotly {
    display: flex;
    justify-content: center;
    align-items: center;
    width: 100%;
}

/* Chart container for uniform sizing */
.chart-container {
    display: flex;
    justify-content: center;
    align-items: center;
    width: 100%;
    max-width: 800px;
    margin: 0 auto;
}

/* Ensure charts don't overflow container */
div.st.plotly > div {
    max-width: 100% !important;
    overflow: hidden !important;
}

/* Chart spacing and alignment */
.stMarkdown:has(.section-header) + div > .st.plotly {
    margin: 1rem 0;
    padding: 1rem;
    background: rgba(255, 255, 255, 0.03);
    border-radius: 16px;
}

/* Two column chart layout */
.col_charts1, .col_charts2 {
    display: flex;
    flex-direction: column;
    align-items: center;
}

/* Ensure charts in columns have equal sizing */
.col_charts1 .st.plotly, 
.col_charts2 .st.plotly {
    width: 100% !important;
    max-width: 450px !important;
    margin: 0 auto !important;
}

/* Wrapper for chart sections in columns */
.col_charts1 > div:has(.section-header),
.col_charts2 > div:has(.section-header) {
    width: 100%;
    text-align: center;
}

/* Plotly figure container sizing */
div.st.plotly figure {
    margin: 0 auto !important;
    width: 100% !important;
    max-width: 100% !important;
}

/* Expanders for charts */
.streamlit-expanderContent {
    display: flex;
    flex-direction: column;
    align-items: center;
}

.streamlit-expanderContent > .st.plotly {
    width: 100%;
    max-width: 900px;
}
</style>
""", unsafe_allow_html=True)

csv_file = "data/detection_log.csv"
frames_dir = "data/frames"
recordings_dir = "data/recordings"
os.makedirs(frames_dir, exist_ok=True)
os.makedirs(recordings_dir, exist_ok=True)
if not os.path.exists(csv_file):
    pd.DataFrame(columns=["Timestamp", "Class", "Confidence", "Restricted Area Violation"]).to_csv(csv_file, index=False)

@st.cache_resource
def load_model():
    return YOLO("model/best.pt")

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
    """Send email notification using .env config with optional snapshot attachment"""
    global EMAIL_ENABLED, EMAIL_SMTP_SERVER, EMAIL_SMTP_PORT
    global EMAIL_SENDER_EMAIL, EMAIL_SENDER_PASSWORD, EMAIL_RECIPIENT_EMAIL
    
    print(f"🔍 send_violation_email_internal started for {class_name}")
    print(f"   EMAIL_ENABLED: {EMAIL_ENABLED}")
    print(f"   EMAIL_SENDER_EMAIL: {EMAIL_SENDER_EMAIL}")
    print(f"   EMAIL_RECIPIENT_EMAIL: {EMAIL_RECIPIENT_EMAIL}")
    print(f"   snapshot_path: {snapshot_path}")
    
    if not EMAIL_ENABLED:
        print(f"❌ Email is not enabled in .env")
        return False
    
    if not EMAIL_SENDER_EMAIL or not EMAIL_SENDER_PASSWORD or not EMAIL_RECIPIENT_EMAIL:
        print(f"❌ Missing email configuration")
        return False
    
    try:
        # Handle multiple recipients (support both comma and semicolon separators)
        recipients = EMAIL_RECIPIENT_EMAIL.replace(',', ';').split(';')
        recipients = [r.strip() for r in recipients if r.strip()]
        recipients_str = ', '.join(recipients)
        
        # Create message
        subject = f"🚨 ALERT: Restricted Area Violation Detected - {class_name}"
        body = f"""
        ⚠️ SECURITY ALERT - RESTRICTED AREA VIOLATION
        
        Detected Object: {class_name}
        Confidence: {confidence:.2%}
        Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        
        A restricted object has been detected in the prohibited area.
        Please take immediate action if necessary.
        
        Snapshot image is attached to this email for visual reference.
        
        ---
        Real-Time Intrusion Detection System
        """
        
        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER_EMAIL
        msg['To'] = recipients_str
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        # Attach snapshot if available
        if snapshot_path and os.path.exists(snapshot_path):
            try:
                with open(snapshot_path, 'rb') as f:
                    img_data = f.read()
                
                # Create filename
                filename = f"violation_{class_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                
                # Create MIMEImage with proper encoding
                image = MIMEImage(img_data, _subtype='jpeg')
                image.add_header('Content-Disposition', 'attachment', filename=filename)
                image.add_header('Content-Type', 'image/jpeg', name=filename)
                msg.attach(image)
                print(f"📸 Snapshot attached: {snapshot_path} ({len(img_data)} bytes)")
            except Exception as img_error:
                print(f"Warning: Could not attach snapshot: {img_error}")
                import traceback
                traceback.print_exc()
        
        # Create SSL context
        context = ssl.create_default_context()
        
        # Connect and send
        with smtplib.SMTP_SSL(EMAIL_SMTP_SERVER, EMAIL_SMTP_PORT, context=context) as server:
            server.login(EMAIL_SENDER_EMAIL, EMAIL_SENDER_PASSWORD)
            server.sendmail(EMAIL_SENDER_EMAIL, recipients, msg.as_string())
        
        return True
    except Exception as e:
        print(f"Email error: {e}")
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
                    
                    if time.time() - object_entry_times[class_name] > 2:
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
    
    if object_inside:
        start_alert("static/sounds/alert.wav")
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

st.set_page_config(page_title="Real-Time Intrusion Detection", layout="wide", initial_sidebar_state="expanded")

# ============ AUTHENTICATION PAGES ============

def login_page():
    st.markdown("""
    <div class="app-header">
        <h1>🚀 Intrusion Detection System</h1>
        <p>Sign in to access the surveillance system</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="auth-container">', unsafe_allow_html=True)
    
    st.markdown("### Login", unsafe_allow_html=True)
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        submit = st.form_submit_button("Login")
        
        if submit:
            if username and password:
                # Find the original username (with proper case) from the users
                users = load_users()
                username_lower = username.lower()
                original_username = username  # Default to input
                for user_key in users.keys():
                    if user_key.lower() == username_lower:
                        original_username = user_key
                        break
                
                if users.get(original_username) == hash_password(password):
                    st.session_state.authenticated = True
                    st.session_state.username = original_username  # Use original case
                    st.session_state.show_signup = False
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid username or password")
            else:
                st.error("Please enter both username and password")
    
    st.markdown("---")
    st.markdown("Don't have an account?", unsafe_allow_html=True)
    if st.button("Sign Up", key="signup_btn"):
        st.session_state.show_signup = True
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def signup_page():
    st.markdown("""
    <div class="app-header">
        <h1>🚀 Intrusion Detection System</h1>
        <p>Create a new account</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="auth-container">', unsafe_allow_html=True)
    
    st.markdown("### Sign Up", unsafe_allow_html=True)
    
    with st.form("signup_form"):
        new_username = st.text_input("Choose Username")
        new_password = st.text_input("Choose Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        
        submit = st.form_submit_button("Create Account")
        
        if submit:
            if new_username and new_password and confirm_password:
                if new_password != confirm_password:
                    st.error("Passwords do not match")
                elif len(new_password) < 4:
                    st.error("Password must be at least 4 characters")
                else:
                    if register_user(new_username, new_password):
                        st.success("Account created! Please login.")
                        st.session_state.show_signup = False
                        st.rerun()
                    else:
                        st.error("Username already exists")
            else:
                st.error("Please fill in all fields")
    
    st.markdown("---")
    if st.button("Back to Login", key="back_to_login_btn"):
        st.session_state.show_signup = False
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

# ============ MAIN APP ============

def main_app():
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"Welcome, {st.session_state.username}")
    if st.sidebar.button("Logout", key="logout_btn"):
        st.session_state.authenticated = False
        st.session_state.username = ""
        if st.session_state.cap:
            stop_camera(st.session_state.cap)
        st.session_state.cap = None
        st.session_state.camera_active = False
        st.session_state.recording = False
        st.rerun()

    st.markdown("""<div class="app-header"><h1>Real-Time Intrusion Detection</h1><p>AI-Powered Restricted Area Monitoring System</p></div>""", unsafe_allow_html=True)

    st.sidebar.markdown("### System Settings")

    col_detect_all, col_detect_none = st.sidebar.columns([1, 1])
    with col_detect_all:
        st.markdown('<div class="sidebar-button">', unsafe_allow_html=True)
        if st.button("All", key="detect_all_btn"):
            st.session_state.detect_all = True
        st.markdown('</div>', unsafe_allow_html=True)
    with col_detect_none:
        st.markdown('<div class="sidebar-button">', unsafe_allow_html=True)
        if st.button("None", key="detect_none_btn"):
            st.session_state.detect_all = False
        st.markdown('</div>', unsafe_allow_html=True)

    detect_options = st.sidebar.multiselect("Objects to Detect", available_classes, default=available_classes if st.session_state.detect_all else [])

    col_alert_all, col_alert_none = st.sidebar.columns([1, 1])
    with col_alert_all:
        st.markdown('<div class="sidebar-button">', unsafe_allow_html=True)
        if st.button("All", key="alert_all_btn"):
            st.session_state.alert_all = True
        st.markdown('</div>', unsafe_allow_html=True)
    with col_alert_none:
        st.markdown('<div class="sidebar-button">', unsafe_allow_html=True)
        if st.button("None", key="alert_none_btn"):
            st.session_state.alert_all = False
        st.markdown('</div>', unsafe_allow_html=True)

    alert_options = st.sidebar.multiselect("Objects for Alert", available_classes, default=available_classes if st.session_state.alert_all else [])

    conf_thresh = st.sidebar.slider("Confidence Threshold", 0.0, 1.0, 0.15, 0.05)

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Camera Controls")

    st.markdown('<div class="sidebar-button">', unsafe_allow_html=True)
    if st.sidebar.button("Start", key="camera_start_btn"):
        if not st.session_state.camera_active:
            cap = start_camera()
            if cap:
                st.session_state.cap = cap
                st.session_state.camera_active = True
                st.session_state.recording = True
                st.rerun()
            else:
                st.sidebar.error("Cannot access camera")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="sidebar-button">', unsafe_allow_html=True)
    if st.sidebar.button("Stop", key="camera_stop_btn"):
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
    st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.camera_active:
        st.sidebar.markdown('<div class="status-badge">Live</div>', unsafe_allow_html=True)
    else:
        st.sidebar.markdown('<div class="status-badge inactive">Offline</div>', unsafe_allow_html=True)

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🎥 Video Recording")
    
    # Recording quality settings
    quality_options = ["Low (480p)", "Medium (720p)", "High (1080p)"]
    if 'recording_quality' not in st.session_state or st.session_state.recording_quality not in quality_options:
        st.session_state.recording_quality = "Medium (720p)"
    
    st.session_state.recording_quality = st.sidebar.selectbox(
        "Recording Quality", 
        quality_options,
        index=quality_options.index(st.session_state.recording_quality)
    )
    
    st.session_state.recording_fps = st.sidebar.slider("Recording FPS", 10, 30, 20)
    
    # Video recording controls
    col_rec_start, col_rec_stop = st.sidebar.columns(2)
    with col_rec_start:
        st.markdown('<div class="sidebar-button">', unsafe_allow_html=True)
        if st.button("⏺ Start Recording", key="btn_start_recording"):
            if st.session_state.camera_active and not st.session_state.video_recording:
                # Set resolution based on quality
                if "Low" in st.session_state.recording_quality:
                    width, height = 640, 480
                elif "Medium" in st.session_state.recording_quality:
                    width, height = 1280, 720
                else:
                    width, height = 1920, 1080
                
                # Create recording filename - always use .avi for compatibility
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"recording_{ts}.avi"
                filepath = os.path.join(recordings_dir, filename)
                
                # Start video writer
                writer = get_video_writer(filepath, st.session_state.recording_fps, width, height)
                if writer and writer.isOpened():
                    st.session_state.video_writer = writer
                    st.session_state.current_recording_file = filepath
                    st.session_state.video_recording = True
                    st.session_state.recording_start_time = time.time()
                    st.success(f"Recording started: {filename}")
                    st.rerun()
                else:
                    st.sidebar.error("Failed to initialize video writer")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col_rec_stop:
        st.markdown('<div class="sidebar-button">', unsafe_allow_html=True)
        if st.button("⏹ Stop Recording", key="btn_stop_recording"):
            if st.session_state.video_recording and st.session_state.video_writer:
                # Release video writer
                st.session_state.video_writer.release()
                st.session_state.video_writer = None
                st.session_state.video_recording = False
                st.session_state.recording = False
                
                # Calculate recording duration
                if st.session_state.recording_start_time:
                    duration = time.time() - st.session_state.recording_start_time
                    st.success(f"Recording saved: {os.path.basename(st.session_state.current_recording_file)} ({format_duration(duration)})")
                else:
                    st.success("Recording saved successfully")
                
                st.session_state.current_recording_file = None
                st.session_state.recording_start_time = None
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Show recording status
    if st.session_state.video_recording:
        st.sidebar.markdown(
            '<div class="status-badge" style="background: rgba(239, 68, 68, 0.15); color: #ef4444; border-color: rgba(239, 68, 68, 0.3);">'
            '● REC</div>', 
            unsafe_allow_html=True
        )
        
        # Show recording timer
        if st.session_state.recording_start_time:
            elapsed = time.time() - st.session_state.recording_start_time
            st.sidebar.markdown(f"**Recording Time:** {format_duration(elapsed)}")
    else:
        st.sidebar.markdown('<div class="status-badge inactive">Not Recording</div>', unsafe_allow_html=True)

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Home", "Live Monitor", "Analytics", "Snapshots", "Recordings", "Email Reporting"])

    with tab1:
        # Enhanced Hero Section with animated gradient text
        st.markdown("""
        <div class="app-header" style="text-align: center; padding: 3rem 2rem; margin-bottom: 2rem;">
            <h1 style="font-size: 3.5rem; font-weight: 800; background: linear-gradient(135deg, #00d4ff 0%, #7c3aed 50%, #ec4899 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; margin-bottom: 0.5rem; animation: pulse 3s ease-in-out infinite;">🛡️ Real-Time Intrusion Detection</h1>
            <p style="font-size: 1.3rem; color: #94a3b8; font-weight: 400; margin-top: 0.5rem;">Advanced AI-Powered Surveillance System with YOLO Object Detection</p>
            <div style="display: flex; justify-content: center; gap: 1rem; margin-top: 1.5rem;">
                <span class="status-badge" style="background: rgba(34, 197, 94, 0.15); color: #4ade80; border: 1px solid rgba(34, 197, 94, 0.3);">● Live Monitoring</span>
                <span class="status-badge" style="background: rgba(124, 58, 237, 0.15); color: #a78bfa; border: 1px solid rgba(124, 58, 237, 0.3);">● YOLOv8</span>
                <span class="status-badge" style="background: rgba(0, 212, 255, 0.15); color: #67e8f9; border: 1px solid rgba(0, 212, 255, 0.3);">● Secure</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # System Statistics Dashboard
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
        
        # Count snapshot files
        snapshot_count = 0
        if os.path.exists(frames_dir):
            snapshot_count = len([f for f in os.listdir(frames_dir) if f.endswith('.jpg')])
        
        col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
        with col_stat1:
            st.markdown(f"""
            <div class="glass-card" style="text-align: center; padding: 1.5rem;">
                <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">🎯</div>
                <div style="font-size: 2rem; font-weight: 700; color: #00d4ff;">{total_detections}</div>
                <div style="color: #94a3b8; font-size: 0.9rem;">Total Detections</div>
                <div style="margin-top: 0.5rem; height: 4px; background: linear-gradient(90deg, #00d4ff, #7c3aed); border-radius: 2px;"></div>
            </div>
            """, unsafe_allow_html=True)
        with col_stat2:
            st.markdown(f"""
            <div class="glass-card" style="text-align: center; padding: 1.5rem;">
                <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">🚨</div>
                <div style="font-size: 2rem; font-weight: 700; color: #ef4444;">{total_violations}</div>
                <div style="color: #94a3b8; font-size: 0.9rem;">Total Violations</div>
                <div style="margin-top: 0.5rem; height: 4px; background: linear-gradient(90deg, #ef4444, #f97316); border-radius: 2px;"></div>
            </div>
            """, unsafe_allow_html=True)
        with col_stat3:
            st.markdown(f"""
            <div class="glass-card" style="text-align: center; padding: 1.5rem;">
                <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">📸</div>
                <div style="font-size: 2rem; font-weight: 700; color: #22c55e;">{snapshot_count}</div>
                <div style="color: #94a3b8; font-size: 0.9rem;">Snapshots Captured</div>
                <div style="margin-top: 0.5rem; height: 4px; background: linear-gradient(90deg, #22c55e, #06b6d4); border-radius: 2px;"></div>
            </div>
            """, unsafe_allow_html=True)
        with col_stat4:
            st.markdown(f"""
            <div class="glass-card" style="text-align: center; padding: 1.5rem;">
                <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">👥</div>
                <div style="font-size: 2rem; font-weight: 700; color: #a855f7;">{len(available_classes)}</div>
                <div style="color: #94a3b8; font-size: 0.9rem;">Object Classes</div>
                <div style="margin-top: 0.5rem; height: 4px; background: linear-gradient(90deg, #a855f7, #ec4899); border-radius: 2px;"></div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Enhanced Feature Cards with detailed descriptions
        st.markdown('<div class="section-header">✨ Key Features</div>', unsafe_allow_html=True)
        
        col_feat1, col_feat2 = st.columns(2)
        with col_feat1:
            st.markdown("""
            <div class="glass-card" style="padding: 2rem; transition: transform 0.3s ease;">
                <div style="display: flex; align-items: center; margin-bottom: 1rem;">
                    <div style="font-size: 3rem; margin-right: 1rem;">🎯</div>
                    <div>
                        <h3 style="color: #f1f5f9; margin: 0; font-size: 1.4rem; font-weight: 700;">Real-Time Detection</h3>
                        <span style="color: #00d4ff; font-size: 0.85rem;">● Live Object Recognition</span>
                    </div>
                </div>
                <p style="color: #cbd5e1; line-height: 1.7; margin-bottom: 1rem;">Advanced YOLOv8 neural network provides instant object detection with high accuracy. Monitor multiple object classes simultaneously in real-time video streams.</p>
                <ul style="color: #94a3b8; margin: 0; padding-left: 1.2rem;">
                    <li>⚡ Sub-30ms processing time</li>
                    <li>🎯 80%+ detection accuracy</li>
                    <li>📊 Multi-class support</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class="glass-card" style="padding: 2rem; transition: transform 0.3s ease;">
                <div style="display: flex; align-items: center; margin-bottom: 1rem;">
                    <div style="font-size: 3rem; margin-right: 1rem;">📈</div>
                    <div>
                        <h3 style="color: #f1f5f9; margin: 0; font-size: 1.4rem; font-weight: 700;">Analytics Dashboard</h3>
                        <span style="color: #22c55e; font-size: 0.85rem;">● Comprehensive Insights</span>
                    </div>
                </div>
                <p style="color: #cbd5e1; line-height: 1.7; margin-bottom: 1rem;">Detailed analytics with charts, trends, and violation patterns. Export data for further analysis and reporting.</p>
                <ul style="color: #94a3b8; margin: 0; padding-left: 1.2rem;">
                    <li>📊 Detection trends</li>
                    <li>🚨 Violation patterns</li>
                    <li>📥 CSV export support</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        with col_feat2:
            st.markdown("""
            <div class="glass-card" style="padding: 2rem; transition: transform 0.3s ease;">
                <div style="display: flex; align-items: center; margin-bottom: 1rem;">
                    <div style="font-size: 3rem; margin-right: 1rem;">🔔</div>
                    <div>
                        <h3 style="color: #f1f5f9; margin: 0; font-size: 1.4rem; font-weight: 700;">Smart Alerting</h3>
                        <span style="color: #ef4444; font-size: 0.85rem;">● Instant Notifications</span>
                    </div>
                </div>
                <p style="color: #cbd5e1; line-height: 1.7; margin-bottom: 1rem;">Intelligent alerting system triggers immediate notifications when restricted area violations are detected. Audio alerts and visual indicators keep you informed.</p>
                <ul style="color: #94a3b8; margin: 0; padding-left: 1.2rem;">
                    <li>🔊 Audio alerts</li>
                    <li>🚨 Instant visual warnings</li>
                    <li>⏱️ Configurable thresholds</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class="glass-card" style="padding: 2rem; transition: transform 0.3s ease;">
                <div style="display: flex; align-items: center; margin-bottom: 1rem;">
                    <div style="font-size: 3rem; margin-right: 1rem;">📸</div>
                    <div>
                        <h3 style="color: #f1f5f9; margin: 0; font-size: 1.4rem; font-weight: 700;">Snapshots Gallery</h3>
                        <span style="color: #f59e0b; font-size: 0.85rem;">● Visual Evidence</span>
                    </div>
                </div>
                <p style="color: #cbd5e1; line-height: 1.7; margin-bottom: 1rem;">Automatic snapshot capture for every detection event. Build a visual history of all monitored activities with timestamped evidence.</p>
                <ul style="color: #94a3b8; margin: 0; padding-left: 1.2rem;">
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
                <h4 style="color: #f1f5f9; margin-bottom: 1.5rem; display: flex; align-items: center; gap: 0.5rem;">
                    <span style="font-size: 1.5rem;">🎥</span> Camera & Recording Status
                </h4>
                <div style="display: grid; gap: 1rem;">
                    <div style="display: flex; justify-content: space-between; padding: 0.75rem; background: rgba(255,255,255,0.03); border-radius: 10px;">
                        <span style="color: #94a3b8;">Camera Status</span>
                        <span style="color: {'#4ade80' if st.session_state.camera_active else '#ef4444'}; font-weight: 600;">{camera_status}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; padding: 0.75rem; background: rgba(255,255,255,0.03); border-radius: 10px;">
                        <span style="color: #94a3b8;">Recording Status</span>
                        <span style="color: {'#4ade80' if st.session_state.recording else '#94a3b8'}; font-weight: 600;">{recording_status}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; padding: 0.75rem; background: rgba(255,255,255,0.03); border-radius: 10px;">
                        <span style="color: #94a3b8;">Detection Classes</span>
                        <span style="color: #00d4ff; font-weight: 600;">{len(detect_options) if detect_options else 0} selected</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; padding: 0.75rem; background: rgba(255,255,255,0.03); border-radius: 10px;">
                        <span style="color: #94a3b8;">Confidence Threshold</span>
                        <span style="color: #a78bfa; font-weight: 600;">{conf_thresh:.2f}</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col_status2:
            st.markdown(f"""
            <div class="glass-card" style="padding: 1.5rem;">
                <h4 style="color: #f1f5f9; margin-bottom: 1.5rem; display: flex; align-items: center; gap: 0.5rem;">
                    <span style="font-size: 1.5rem;">🤖</span> Model Information
                </h4>
                <div style="display: grid; gap: 1rem;">
                    <div style="display: flex; justify-content: space-between; padding: 0.75rem; background: rgba(255,255,255,0.03); border-radius: 10px;">
                        <span style="color: #94a3b8;">Model Type</span>
                        <span style="color: #00d4ff; font-weight: 600;">YOLOv8n</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; padding: 0.75rem; background: rgba(255,255,255,0.03); border-radius: 10px;">
                        <span style="color: #94a3b8;">Total Classes</span>
                        <span style="color: #22c55e; font-weight: 600;">{len(available_classes)}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; padding: 0.75rem; background: rgba(255,255,255,0.03); border-radius: 10px;">
                        <span style="color: #94a3b8;">Alert Classes</span>
                        <span style="color: #ef4444; font-weight: 600;">{len(alert_options) if alert_options else 0} selected</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; padding: 0.75rem; background: rgba(255,255,255,0.03); border-radius: 10px;">
                        <span style="color: #94a3b8;">Last Detection</span>
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
                    <p style="color: #94a3b8; margin: 0; padding-left: 2.5rem;">Click "Start" in the sidebar to activate the camera feed and begin real-time monitoring.</p>
                </div>
                <div style="flex: 1; min-width: 200px;">
                    <h5 style="color: #7c3aed; margin-bottom: 1rem; display: flex; align-items: center; gap: 0.5rem;">
                        <span style="background: linear-gradient(135deg, #7c3aed, #ec4899); color: white; width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.9rem; font-weight: 700;">2</span>
                        Configure Settings
                    </h5>
                    <p style="color: #94a3b8; margin: 0; padding-left: 2.5rem;">Select objects to detect and alert on using the sidebar options. Adjust confidence threshold as needed.</p>
                </div>
                <div style="flex: 1; min-width: 200px;">
                    <h5 style="color: #ec4899; margin-bottom: 1rem; display: flex; align-items: center; gap: 0.5rem;">
                        <span style="background: linear-gradient(135deg, #ec4899, #f97316); color: white; width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.9rem; font-weight: 700;">3</span>
                        View Analytics
                    </h5>
                    <p style="color: #94a3b8; margin: 0; padding-left: 2.5rem;">Check the Analytics tab for detailed reports, charts, and violation history.</p>
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
                    <div style="color: #94a3b8; font-size: 0.9rem;">Start monitoring to detect violations</div>
                </div>
                """, unsafe_allow_html=True)
        
        with col_alert2:
            # Today's and Week's Alerts
            if alert_count > 0:
                st.markdown(f"""
                <div class="glass-card" style="text-align: center; padding: 1.5rem;">
                    <div style="font-size: 3rem; margin-bottom: 0.5rem;">📊</div>
                    <div style="font-size: 1.8rem; font-weight: 700; color: #00d4ff;">{today_alerts} / {week_alerts}</div>
                    <div style="color: #94a3b8; font-size: 0.9rem;">Today / This Week</div>
                    <div style="color: #a78bfa; font-size: 0.85rem; margin-top: 0.5rem;">Top: {top_class}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="glass-card" style="text-align: center; padding: 1.5rem;">
                    <div style="font-size: 3rem; margin-bottom: 0.5rem;">📊</div>
                    <div style="font-size: 1.5rem; font-weight: 700; color: #94a3b8;">No Data Yet</div>
                    <div style="color: #94a3b8; font-size: 0.9rem;">Start camera to begin monitoring</div>
                </div>
                """, unsafe_allow_html=True)
        
        with col_alert3:
            # Quick Actions
            st.markdown(f"""
            <div class="glass-card" style="padding: 1.5rem;">
                <h4 style="color: #f1f5f9; margin-bottom: 1rem;">⚡ Quick Actions</h4>
                <div style="display: flex; flex-direction: column; gap: 0.75rem;">
                    <div style="color: #94a3b8; padding: 0.5rem 0;">🔔 Test Alert Sound</div>
                    <div style="color: #94a3b8; padding: 0.5rem 0;">📧 Test Email Alert</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        

        
        
        st.markdown("<br>", unsafe_allow_html=True)

    with tab2:
        st.markdown("""
        <div class="live-monitor-header">
            📹 Live Camera Feed
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
            st.markdown(f'<div style="text-align: right; color: #94a3b8; font-size: 0.9rem;">📅 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</div>', unsafe_allow_html=True)
        
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
                            
                            frame_placeholder.image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), channels="RGB", width='stretch')
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
                            <span style="color: #94a3b8; font-size: 0.85rem;">Camera</span>
                            <div style="color: #4ade80; font-weight: 600;">● Active</div>
                        </div>
                        <div>
                            <span style="color: #94a3b8; font-size: 0.85rem;">Recording</span>
                            <div style="color: #a78bfa; font-weight: 600;">● {recording_display}</div>
                        </div>
                        <div>
                            <span style="color: #94a3b8; font-size: 0.85rem;">Confidence</span>
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
                if len(filtered_df) > 1:
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
                if len(violation_filtered) > 1:
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
            col_charts1, col_charts2 = st.columns(2)
            
            with col_charts1:
                st.markdown('<div class="section-header">🎯 Class Distribution</div>', unsafe_allow_html=True)
                
                if HAS_PLOTLY_ANALYTICS and len(filtered_df) > 0:
                    fig_pie = epa.create_detection_pie_chart(filtered_df)
                    st.plotly_chart(fig_pie, use_container_width=True)
                else:
                    st.info("Chart module not available")
            
            with col_charts2:
                st.markdown('<div class="section-header">📊 Confidence Distribution</div>', unsafe_allow_html=True)
                
                if HAS_PLOTLY_ANALYTICS and len(filtered_df) > 0:
                    fig_conf = epa.create_confidence_distribution(filtered_df)
                    st.plotly_chart(fig_conf, use_container_width=True)
                else:
                    st.info("Chart module not available")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # ============ Hourly Detection Pattern (Heatmap) ============
            with st.expander("🕐 Hourly Detection Pattern", expanded=False):
                if len(filtered_df) > 0:
                    if HAS_PLOTLY_ANALYTICS:
                        fig_heatmap = epa.create_detection_heatmap(filtered_df)
                        st.plotly_chart(fig_heatmap, use_container_width=True)
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
                st.dataframe(filtered_df, width='stretch')
            
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
                    st.dataframe(summary_stats, width='stretch')
        
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
                                st.image(fr['path'], caption=fr['name'][:25], width='stretch')
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
                <h4 style="color: #f1f5f9; margin-bottom: 1rem;">📝 How Snapshots Work</h4>
                <ol style="color: #94a3b8; line-height: 2;">
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
                                    <span style="color: #94a3b8;">Created:</span>
                                    <span style="color: #f1f5f9;">{recording['created']}</span>
                                </div>
                                <div style="display: flex; justify-content: space-between;">
                                    <span style="color: #94a3b8;">Size:</span>
                                    <span style="color: #22c55e;">{recording['size_mb']:.2f} MB</span>
                                </div>
                                <div style="display: flex; justify-content: space-between;">
                                    <span style="color: #94a3b8;">Duration:</span>
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
                <h4 style="color: #f1f5f9; margin-bottom: 1rem;">📝 How to Record</h4>
                <ol style="color: #94a3b8; line-height: 2;">
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



if not st.session_state.authenticated:
    if st.session_state.show_signup:
        signup_page()
    else:
        login_page()
else:
    main_app()
