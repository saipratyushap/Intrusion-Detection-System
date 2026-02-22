# 🚀 Intrusion Detection System

A comprehensive **Intrusion Detection System** built with **FastAPI** and **Streamlit**. This project integrates YOLO object detection with advanced analytics, business intelligence dashboards, and automated reporting capabilities.

---

## 📁 Project Structure

```
Intrusion-Detection-System-main 2/
│
├── frontend/              # Streamlit Frontend Application
│   ├── streamlit_run.py                 # Main Streamlit app
│   ├── enhanced_analytics.py            # Enhanced analytics module
│   ├── enhanced_plotly_analytics.py      # Plotly visualizations
│   ├── static/                          # Static assets (CSS, images, JS)
│   │   ├── styles.css                   # Main styles
│   │   ├── data.css                     # Data page styles
│   │   ├── snapshots.css                 # Snapshots page styles
│   │   ├── login_signup.css             # Login page styles
│   │   ├── script.js                     # Main JavaScript
│   │   ├── data.js                      # Data page JS
│   │   ├── snapshots.js                  # Snapshots page JS
│   │   ├── logo.jpg                     # Logo image
│   │   └── sounds/                      # Alert sounds
│   └── templates/                       # HTML templates
│       ├── data.html                     # Data analytics page
│       └── snapshots.html                 # Snapshots gallery
│
├── backend/               # FastAPI Backend Application
│   ├── fastapi_run.py                   # Main FastAPI app
│   ├── advanced_analytics.py            # Predictive analytics
│   ├── advanced_email_reporting.py       # Email reporting system
│   ├── business_intelligence.py           # BI dashboards
│   ├── email_service.py                  # Email service
│   ├── email_diagnostic.py              # Email diagnostics
│   ├── report_scheduler.py              # Report scheduler
│   └── __init__.py
│
├── data/                  # Shared Data Directory
│   ├── detection_log.csv               # Detection logs
│   ├── frames/                        # Captured frames/snapshots
│   ├── recordings/                     # Video recordings
│   ├── users.json                     # User database
│   ├── cameras.json                   # Camera configurations
│   ├── user_activity.json             # Activity logs
│   ├── cost_config.json               # Cost configuration
│   └── report_schedules.json          # Report schedules
│
├── model/                 # ML Models
│   └── best.pt                         # Best detection model
│
├── .env                    # Environment configuration
├── .env.example           # Example environment file
├── requirements.txt        # Python dependencies
├── PROJECT_STRUCTURE.md   # Project structure documentation
└── README.md              # Main project documentation
```

---

## 🎯 Key Features

### 🔔 Core Monitoring Features
- ✅ **Real-time Object Detection** with YOLO models
- ✅ **Live Video Streaming** with restricted area overlay
- ✅ **Sound Alerts** when violations are detected
- ✅ **Automatic Detection Logging** to CSV files
- ✅ **WebSocket Communication** for real-time updates

### 🔐 Authentication & Security
- ✅ **User Login/Signup System** with secure password handling
- ✅ **Session Management**
- ✅ **Protected Routes**

### 📊 Analytics & Business Intelligence
- ✅ **Advanced Analytics Dashboard**
  - Predictive forecasting (7-30 days)
  - Anomaly detection (Z-score, Isolation Forest, Statistical methods)
  - Trend analysis
  - KPI calculation
  - Correlation analysis
  - Percentile analysis

- ✅ **Business Intelligence Features**
  - Executive summary reports
  - MTTR (Mean Time to Response) calculation
  - False positive rate analysis
  - Coverage percentage metrics
  - Violation trend analysis

- ✅ **Enhanced Plotly Charts**
  - Interactive visualizations
  - Real-time data updates
  - Multiple chart types (bar, pie, line, scatter, doughnut)

### 📧 Email Reporting System
- ✅ **Advanced Email Reporting**
  - HTML email templates
  - PDF report attachments
  - CSV data exports
  - Scheduled report delivery

- ✅ **Report Scheduler**
  - Configure automatic report schedules
  - Multiple report types (daily, weekly, monthly)
  - Configurable recipients
  - Manual report triggering

### 📸 Snapshot Management
- ✅ **Snapshot Capture & Storage**
- ✅ **Snapshot Gallery View**
- ✅ **Filter by Date/Time**
- ✅ **Delete Old Snapshots**

### 🎬 Video Recording
- ✅ **Video Recording**
- ✅ **Playback Functionality**
- ✅ **Recording Quality Selection** (Low/Medium/High)

### 🎨 Modern UI/UX
- ✅ **Responsive Design**
- ✅ **Light/Dark Theme** (green accents)
- ✅ **Interactive Charts**
- ✅ **Real-time Data Refresh**
- ✅ **User-friendly Navigation**

---

## 🆕 Recent Updates (February 2026)

### UI/UX Improvements
- ✅ **Fixed Sidebar Logo Display** - Implemented Base64 encoding for reliable logo rendering
- ✅ **Cleaner Analytics Charts** - Hidden Plotly mode bar buttons (zoom, pan, etc.) for a streamlined look
- ✅ **Improved Logo Styling** - Removed border-radius for seamless sidebar integration

### Video Recording Enhancements
- ✅ **User-Controlled Recording** - Added Start/Stop recording buttons to sidebar
- ✅ **Quality Settings** - Low (480p), Medium (720p), High (1080p) resolution options
- ✅ **FPS Control** - Adjustable recording frame rate (5-30 FPS)
- ✅ **Recording Timer** - Real-time duration display while recording
- ✅ **Auto-Generated Filenames** - Timestamped .avi files saved to `data/recordings/`

### Frontend Streamlining
- ✅ **Removed User Activity Tab** - Moved to backend-only (available via API at port 8000)
- ✅ **6 Main Tabs** - Home, Live Monitor, Analytics, Snapshots, Recordings, Email Reporting

### Performance & Reliability
- ✅ **Increased API Timeouts** - Extended from 30s to 60s for email reporting operations
- ✅ **Better Error Handling** - Improved user activity logging timeout (2s → 10s)

### Email Reporting & Backend Connectivity
- ✅ **Fixed Environment Loading** - Corrected `.env` path resolution across all services
- ✅ **Automated Email Diagnostics** - Configured a dedicated script for testing SMTP connections 

---

## 🚀 Running the Application

### Terminal 1 - Backend (FastAPI):
```bash
cd "/Users/psaipratyusha/Downloads/Intrusion-Detection-System-main 2"
uvicorn backend.fastapi_run:app --host 127.0.0.1 --port 8000 --reload
```

### Terminal 2 - Frontend (Streamlit):
```bash
cd "/Users/psaipratyusha/Downloads/Intrusion-Detection-System-main 2"
streamlit run frontend/streamlit_run.py --server.port 8501
```

### Access URLs
| Component | URL |
|----------|-----|
| **Frontend (Streamlit)** | http://localhost:8501 |
| **Backend API (FastAPI)** | http://127.0.0.1:8000 |
| **API Documentation** | http://127.0.0.1:8000/docs |
| **Web Dashboard** | http://127.0.0.1:8000/data |

---

## 🔐 Default Credentials

| Field | Value |
|-------|-------|
| **Username** | `admin` |
| **Password** | `admin` |

> ⚠️ **Security Note:** Change the default password in production environments!

---

## 🛠️ Installation & Setup

### 1️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

### 2️⃣ Configure Environment

Create a `.env` file:
```env
# Email Configuration
EMAIL_ENABLED=true
EMAIL_SENDER_EMAIL=your_email@gmail.com
EMAIL_SENDER_PASSWORD=your_app_password
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_RECIPIENT_EMAIL=recipient@example.com
```

### 3️⃣ Start Backend
```bash
cd "/Users/psaipratyusha/Downloads/Intrusion-Detection-System-main 2"
uvicorn backend.fastapi_run:app --host 127.0.0.1 --port 8000 --reload
```

### 4️⃣ Start Frontend
```bash
cd "/Users/psaipratyusha/Downloads/Intrusion-Detection-System-main 2"
streamlit run frontend/streamlit_run.py --server.port 8501
```

### 5️⃣ Email System Configuration

#### Understanding Email Roles

The system uses **three different email concepts**:

1. **Sender Email (Admin/System Email)** 🚀
   - **Location:** `.env` file
   - **Purpose:** The email account that SENDS all system emails
   - **Configuration:**
     ```env
     EMAIL_SENDER_EMAIL=your_admin@gmail.com
     EMAIL_SENDER_PASSWORD=your_app_password
     EMAIL_SMTP_SERVER=smtp.gmail.com
     EMAIL_SMTP_PORT=587
     ```
   - **Uses:**
     - Sends OTP verification codes
     - Sends violation alerts
     - Sends scheduled reports
     - All outgoing system notifications

   > 💡 **Important:** This single email and password (`EMAIL_SENDER_PASSWORD`) is used for **ALL** system emails, including OTP Verification, Violation Alerts, and Scheduled Reports.

2. **User Accounts & Verification** 📝
   - **Location:** `data/users.json`
   - **Purpose:** Stores all user accounts (username, password, email)
   - **Use Case:** Main app login/signup system
   - **Note:** Email verification is handled during signup process

3. **Recipient Emails** 📬
   - **Location:** Specified in Email Reporting tab
   - **Purpose:** Who RECEIVES reports and alerts
   - **Example:** `recipient@company.com`, `security@organization.com`
   - **Note:** Can be ANY email address (no verification required)

#### Email Flow Diagram
```
Admin/Sender Email          →  Sends Emails To  →  Recipients
(from .env file)                                    (any email)
your_admin@gmail.com                                user@example.com
                                                    team@company.com
```

> **Note:** Email verification for user signup is handled within the main app login system using `data/users.json`.

---

## 📊 UI Features

### Frontend Dashboard Tabs
1. **Home** - System overview and statistics
2. **Live Monitor** - Real-time camera feed with detection overlay
3. **Analytics** - Charts and visualizations
4. **Snapshots** - Captured violation images gallery
5. **Recordings** - Video recordings library with Start/Stop controls
6. **Email Reporting** - Send and schedule reports

> **Note:** User Activity tab has been moved to the backend API. Access user activity logs via the backend at `http://127.0.0.1:8000`.

### Data Dashboard Tabs
1. **Dashboard** - Stats and detection log
2. **Alerts** - Real-time violation alerts
3. **Analytics** - Interactive charts
4. **Activity Feed** - System activity stream
5. **System Health** - CPU, memory, disk usage
6. **Cameras** - Camera management
7. **User Activity** - User login/logout history
8. **Filters** - Advanced search and filtering
9. **Export** - CSV export functionality

---

## 🔍 How It Works

### Data Storage
All detected data is stored in `data/detection_log.csv`:
- Timestamp
- Class (detected object type)
- Confidence score
- Restricted Area Violation (Yes/No)

### Backend API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/login` | POST | User login |
| `/api/auth/signup` | POST | User registration |
| `/api/auth/logout` | POST | User logout |
| `/ws/data` | WebSocket | Real-time data stream |
| `/api/analytics/*` | GET | Analytics endpoints |
| `/api/reports/*` | GET/POST | Report endpoints |
| `/api/alerts/*` | GET | Alert endpoints |
| `/api/snapshots` | GET | List snapshots |
| `/api/health/*` | GET | System health |

---

## ⚙️ Configuration

### Camera Setup (`data/cameras.json`)
```json
{
    "cameras": [
        {
            "id": "cam_001",
            "name": "Main Camera",
            "url": "0",
            "enabled": true,
            "location": "Entrance"
        }
    ]
}
```

### Cost Configuration (`data/cost_config.json`)
```json
{
    "cost_per_camera_monthly": 50.0,
    "cost_per_detection": 0.01,
    "infrastructure_cost_monthly": 500.0
}
```

---

## 📝 Notes

- Both frontend and backend need to be running for full functionality
- The frontend makes API calls to the backend on port 8000
- Shared data is stored in the root `data/` directory
- Environment variables are read from root `.env` file

---

## 💻 Technologies Used

- **Backend:** FastAPI, Uvicorn, WebSockets
- **Frontend:** Streamlit, HTML/CSS/JavaScript, Chart.js
- **ML Models:** YOLOv8 (Ultralytics)
- **Data:** CSV, JSON
- **Visualizations:** Plotly, Chart.js

---

## 📝 License

This project is open source and available for personal and commercial use.

---

🚀 **Made with ❤️ by Pratyusha**

